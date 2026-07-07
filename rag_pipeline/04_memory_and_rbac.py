# Databricks notebook source
# MAGIC %md
# MAGIC # 04 — Session Memory & RBAC
# MAGIC
# MAGIC Smoke tests for:
# MAGIC - `SessionManager` — Delta-backed multi-turn conversation memory
# MAGIC - `HybridRetriever` RBAC filter — role-scoped chunk retrieval
# MAGIC
# MAGIC **Prerequisites:** 02_chunk_and_index (VS index must be ONLINE)

# COMMAND ----------
import subprocess, sys

_nb_path   = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
_repo_root = "/Workspace/" + "/".join(_nb_path.strip("/").split("/")[:-2])
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-e", _repo_root,
                "databricks-ai-search>=0.3.0"], check=True)

# COMMAND ----------
dbutils.library.restartPython()

# COMMAND ----------
from uw_copilot.config    import Config
from uw_copilot.session   import SessionManager
from uw_copilot.retrieval import HybridRetriever
from databricks.sdk       import WorkspaceClient

cfg = Config()
w   = WorkspaceClient()
sm  = SessionManager(spark, cfg)
r   = HybridRetriever(cfg, w)

# COMMAND ----------
# MAGIC %md ## Session Memory Smoke Test

# COMMAND ----------
import uuid

# 1. Create a session
session_id = str(uuid.uuid4())
print(f"Session: {session_id[:8]}...")

# 2. Add a few turns
sm.append_message(session_id, "user",      "Tell me about Pacific Coast Carriers.")
sm.append_message(session_id, "assistant", "Pacific Coast (INS-1002) is a 42-unit long-haul refrigerated fleet in Fontana, CA.")
sm.append_message(session_id, "user",      "What is their current loss ratio?")
sm.append_message(session_id, "assistant", "Their current term loss ratio is 235.79%.")

# 3. Retrieve history
history = sm.get_history(session_id, last_n=10)
print(f"History length: {len(history)} messages")
assert len(history) == 4, f"Expected 4 messages, got {len(history)}"

# 4. Verify Delta persistence
count = spark.sql(f"SELECT COUNT(*) AS n FROM {cfg.catalog}.{cfg.schema}.conversation_sessions WHERE session_id = '{session_id}'").collect()[0]["n"]
assert count == 4, f"Expected 4 rows in Delta, got {count}"
print("Delta persistence: OK")

# COMMAND ----------
# MAGIC %md ## Session Compression Test

# COMMAND ----------
# Fill session past compression threshold
for i in range(20):
    sm.append_message(session_id, "user",      f"Follow-up question #{i+5} about fleet risk.")
    sm.append_message(session_id, "assistant", f"Response to question #{i+5}.")

history = sm.get_history(session_id, last_n=10)
print(f"After 20+ turns, context window has {len(history)} messages (max={sm.MAX_MESSAGES})")
assert len(history) <= sm.MAX_MESSAGES, "History should be capped at MAX_MESSAGES"
print("Compression / windowing: OK")

# COMMAND ----------
# MAGIC %md ## RBAC Filter Test

# COMMAND ----------
# Test that different roles see different chunks
question = "What are the fleet inspection requirements?"
roles_to_test = ["underwriter", "broker", "claims_adjuster", "loss_control"]

print("RBAC filter results:")
print(f"{'Role':<20} {'Chunks':>6}")
print("-" * 28)
for role in roles_to_test:
    try:
        docs = r.search(question, user_role=role)
        print(f"{role:<20} {len(docs):>6}")
    except Exception as e:
        print(f"{role:<20}  ERROR: {e}")

# Underwriter should have >= access as broker
docs_uw  = r.search(question, user_role="underwriter")
docs_brk = r.search(question, user_role="broker")
assert len(docs_uw) >= len(docs_brk), "Underwriter should see >= docs than broker"
print("\nRBAC hierarchy: OK")

# COMMAND ----------
# Cleanup test session
spark.sql(f"DELETE FROM {cfg.catalog}.{cfg.schema}.conversation_sessions WHERE session_id = '{session_id}'")
print("\n✅ Memory and RBAC smoke tests passed")

