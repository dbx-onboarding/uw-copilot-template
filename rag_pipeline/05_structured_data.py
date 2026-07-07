# Databricks notebook source
# MAGIC %md
# MAGIC # 05 — Structured Data Integration
# MAGIC
# MAGIC NL-to-SQL for the 8 operational Delta tables. The agent routes structured
# MAGIC queries (loss ratios, premiums, driver scores) through a SQL path instead
# MAGIC of Vector Search.
# MAGIC
# MAGIC Schema context is loaded from `prompts/schema_context.md` and injected
# MAGIC into the LLM prompt for accurate SQL generation.

# COMMAND ----------
import subprocess, sys

_nb_path   = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
_repo_root = "/Workspace/" + "/".join(_nb_path.strip("/").split("/")[:-2])
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-e", _repo_root], check=True)

# COMMAND ----------
dbutils.library.restartPython()

# COMMAND ----------
from pathlib import Path
from uw_copilot.config    import Config
from uw_copilot.retrieval import HybridRetriever, QueryIntent
from databricks.sdk       import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

cfg = Config()
w   = WorkspaceClient()
r   = HybridRetriever(cfg, w)

# Verify warehouse is configured
if not cfg.warehouse_id:
    print("⚠️  warehouse_id is empty in company_config.yaml — NL-to-SQL will fail.")
    print("   Set warehouse_id to a running SQL warehouse ID and re-run.")
else:
    print(f"Warehouse: {cfg.warehouse_id}")

# Load schema context
schema_ctx_path = Path(_repo_root) / "prompts" / "schema_context.md"
SCHEMA_CONTEXT  = schema_ctx_path.read_text() if schema_ctx_path.exists() else ""
print(f"Schema context: {len(SCHEMA_CONTEXT)} chars")

# COMMAND ----------
# MAGIC %md ## SQL Intent Detection

# COMMAND ----------
sql_questions = [
    "What is the loss ratio for Heartland Express?",
    "Show me all open claims over $250,000",
    "Which drivers have more than 3 accidents in the past 3 years?",
    "What is Pacific Coast Carriers' current premium?",
]
doc_questions = [
    "What are the underwriting guidelines for HAZMAT?",
    "How do I handle a fatality claim?",
]

print("Intent detection test:")
for q in sql_questions + doc_questions:
    intent = r.detect_intent(q)
    label  = "SQL " if intent == QueryIntent.SQL else "DOCS"
    print(f"  [{label}] {q[:60]}")

# COMMAND ----------
# MAGIC %md ## NL-to-SQL Test

# COMMAND ----------
def nl_to_sql(question: str, schema_context: str, catalog: str, schema: str) -> str:
    """Convert natural language to SQL using the LLM."""
    prompt = f"""You are a SQL expert for a commercial trucking insurance database.
Given the schema below, write a single SELECT SQL query to answer the question.
Use fully qualified table names: {catalog}.{schema}.<table>.
Return ONLY the SQL — no explanation, no markdown.

{schema_context}

Question: {question}
SQL:"""

    resp = w.serving_endpoints.query(
        name=cfg.chat_model,
        messages=[ChatMessage(role=ChatMessageRole.USER, content=prompt)],
        max_tokens=500,
        temperature=0.0,
    )
    sql = resp.choices[0].message.content.strip()
    # Strip markdown code fences if present
    if sql.startswith("```"):
        sql = "\n".join(sql.split("\n")[1:-1]).strip()
    return sql


# Test NL-to-SQL
if cfg.warehouse_id and SCHEMA_CONTEXT:
    test_q = "What is the average loss ratio per insured, sorted by highest first?"
    sql    = nl_to_sql(test_q, SCHEMA_CONTEXT, cfg.catalog, cfg.schema)
    print(f"Question: {test_q}")
    print(f"\nGenerated SQL:\n{sql}")

    # Execute the generated SQL
    try:
        result_df = spark.sql(sql)
        display(result_df.limit(10))
    except Exception as e:
        print(f"SQL execution error: {e}")
        print("If the query is syntactically correct, this may be a data/permissions issue.")
else:
    print("Skipping NL-to-SQL test — warehouse_id not set or schema_context.md missing")

# COMMAND ----------
print("\n✅ Structured data integration complete")

