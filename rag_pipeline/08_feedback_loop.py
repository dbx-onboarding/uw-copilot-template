# Databricks notebook source
# MAGIC %md
# MAGIC # 08 — Feedback Loop
# MAGIC
# MAGIC Records and analyzes user feedback (thumbs up/down) from the Workbench UI.
# MAGIC Negative feedback is automatically promoted to the MLflow evaluation dataset.
# MAGIC
# MAGIC **Tables used:** `copilot_feedback`, `feedback_overrides`

# COMMAND ----------
import subprocess, sys

_nb_path   = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
_repo_root = "/Workspace/" + "/".join(_nb_path.strip("/").split("/")[:-2])
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-e", _repo_root], check=True)

# COMMAND ----------
dbutils.library.restartPython()

# COMMAND ----------
from uw_copilot.config import Config
from pyspark.sql       import functions as F

cfg = Config()
C   = cfg.catalog
S   = cfg.schema

# COMMAND ----------
# MAGIC %md ## FeedbackManager

# COMMAND ----------
import uuid
from datetime import datetime, timezone


class FeedbackManager:
    """
    Records user feedback in copilot_feedback and exposes analytics.
    Negative feedback can be exported to the MLflow eval dataset.
    """

    def record(
        self,
        user_id:    str,
        question:   str,
        answer:     str,
        rating:     int,           # 1 = thumbs up, -1 = thumbs down
        comment:    str   = None,
        session_id: str   = None,
    ):
        row = spark.createDataFrame([{
            "feedback_id": str(uuid.uuid4()),
            "session_id":  session_id or str(uuid.uuid4()),
            "user_id":     user_id,
            "question":    question,
            "answer":      answer,
            "rating":      rating,
            "comment":     comment,
            "created_at":  datetime.now(timezone.utc),
        }])
        row.write.mode("append").saveAsTable(f"{C}.{S}.copilot_feedback")

    def stats(self):
        df = spark.sql(f"""
            SELECT
                COUNT(*)                                   AS total,
                SUM(CASE WHEN rating = 1  THEN 1 ELSE 0 END) AS thumbs_up,
                SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) AS thumbs_down,
                ROUND(
                    100.0 * SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) / COUNT(*), 1
                )                                          AS satisfaction_pct
            FROM {C}.{S}.copilot_feedback
        """)
        return df.collect()[0]

    def negative_feedback(self, limit: int = 50):
        return spark.sql(f"""
            SELECT feedback_id, user_id, question, answer, comment, created_at
            FROM {C}.{S}.copilot_feedback
            WHERE rating = -1
            ORDER BY created_at DESC
            LIMIT {limit}
        """)

    def record_override(
        self,
        user_id:           str,
        uw_decision:       str,
        ai_recommendation: str = None,
        submission_id:     str = None,
        override_reason:   str = None,
        override_detail:   str = None,
        session_id:        str = None,
    ):
        row = spark.createDataFrame([{
            "override_id":         str(uuid.uuid4()),
            "session_id":          session_id,
            "user_id":             user_id,
            "submission_id":       submission_id,
            "ai_recommendation":   ai_recommendation,
            "uw_decision":         uw_decision,
            "override_reason":     override_reason,
            "override_detail":     override_detail,
            "created_at":          datetime.now(timezone.utc),
        }])
        row.write.mode("append").saveAsTable(f"{C}.{S}.feedback_overrides")


fm = FeedbackManager()
print("FeedbackManager ready")

# COMMAND ----------
# MAGIC %md ## Record Demo Feedback

# COMMAND ----------
demo_feedback = [
    ("james.rodriguez@example.com", "What is Lone Star's current loss ratio?",
     "Lone Star Hauling Partners has a loss ratio of 1499.15% for the 2025-2026 term, based on 3 open claims totaling $877K incurred.", 1, None),
    ("sarah.mitchell@example.com", "What are the referral triggers for HAZMAT?",
     "HAZMAT fleets require CCO-level referral per the authority matrix.", -1, "Too vague — didn't cite the specific thresholds"),
    ("david.chen@example.com", "Show me Pacific Coast's open claims",
     "Pacific Coast Carriers has 2 open claims: CLM-25-3891045 ($385K, Suit Filed) and CLM-25-3891200 ($142K, Pre-Suit).", 1, None),
    ("james.rodriguez@example.com", "What is the minimum premium for auto liability?",
     "I'm not able to find specific minimum premium information in the available documents.", -1, "Should be in the product guide"),
]

for user_id, q, a, rating, comment in demo_feedback:
    fm.record(user_id=user_id, question=q, answer=a, rating=rating, comment=comment)

print("Demo feedback recorded")

# COMMAND ----------
# Stats
s = fm.stats()
print(f"Total feedback:   {s['total']}")
print(f"Thumbs up:        {s['thumbs_up']}")
print(f"Thumbs down:      {s['thumbs_down']}")
print(f"Satisfaction:     {s['satisfaction_pct']}%")

# COMMAND ----------
# MAGIC %md ## Negative Feedback (needs review)

# COMMAND ----------
display(fm.negative_feedback())

# COMMAND ----------
# MAGIC %md ## Override Capture

# COMMAND ----------
# Record an underwriter decision that diverged from AI recommendation
fm.record_override(
    user_id           = "james.rodriguez@example.com",
    submission_id     = "SUB-26-11065",
    ai_recommendation = "Refer",
    uw_decision       = "Bind with conditions",
    override_reason   = "Established Relationship",
    override_detail   = "10+ year relationship. Agreed to 15% rate increase and driver DRV-2013 exclusion.",
)

override_count = spark.sql(f"SELECT COUNT(*) AS n FROM {C}.{S}.feedback_overrides").collect()[0]["n"]
print(f"Overrides recorded: {override_count}")

# COMMAND ----------
# MAGIC %md ## Quality Trends

# COMMAND ----------
display(spark.sql(f"""
SELECT
    DATE(created_at)                                    AS date,
    COUNT(*)                                            AS total,
    ROUND(100.0 * SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS satisfaction_pct
FROM {C}.{S}.copilot_feedback
GROUP BY date
ORDER BY date DESC
LIMIT 30
"""))
print("\n✅ Feedback loop complete")

