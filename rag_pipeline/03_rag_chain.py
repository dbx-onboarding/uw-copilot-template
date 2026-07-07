# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — RAG Chain Integration Test
# MAGIC
# MAGIC Validates the end-to-end retrieval + generation pipeline before deployment.
# MAGIC Tests all three intent paths: HYBRID (semantic), KEYWORD (exact ID), and SQL.
# MAGIC
# MAGIC **Prerequisites:** 02_chunk_and_index must have run and the VS index must be ONLINE.

# COMMAND ----------

import subprocess, sys

_nb_path   = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
_repo_root = "/Workspace/" + "/".join(_nb_path.strip("/").split("/")[:-2])
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-e", _repo_root,
                "databricks-ai-search>=0.3.0"], check=True)

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Config + VS health check
import os
from uw_copilot.config    import Config
from uw_copilot.retrieval import HybridRetriever, QueryIntent
from databricks.sdk       import WorkspaceClient

cfg = Config()
w   = WorkspaceClient()
cfg.print_summary()
r   = HybridRetriever(cfg, w)

# ── VS endpoint + index health check ───────────────────────────────────────────
print(f"\n{'─'*60}")
ep       = w.vector_search_endpoints.get_endpoint(cfg.vs_endpoint)
ep_state = ep.endpoint_status.state if ep.endpoint_status else "UNKNOWN"
print(f"VS endpoint  [{cfg.vs_endpoint}]: {ep_state}")

idx       = w.vector_search_indexes.get_index(cfg.vs_index)
idx_ok    = idx.status.ready if idx.status else False
idx_state = idx.status.detailed_state if idx.status else "UNKNOWN"
idx_rows  = getattr(idx.status, "indexed_row_count", "?") if idx.status else "?"
print(f"VS index     state={idx_state}  ready={idx_ok}  rows={idx_rows}")

if not idx_ok:
    print("  ⚠️  Index not ready — retrieval will return empty results.")
    print("  Run 02_chunk_and_index to populate the index first.")

# COMMAND ----------

# DBTITLE 1,Intent routing validation
# ── Verify all three intent paths route correctly ───────────────────────────────
cases = [
    ("What are HAZMAT referral triggers?",                    QueryIntent.HYBRID),
    ("Minimum CDL experience for flatbed operations?",         QueryIntent.HYBRID),
    ("Show me claim CLM-25-3891045",                          QueryIntent.KEYWORD),
    ("Review submission SUB-26-11065",                        QueryIntent.KEYWORD),
    ("What is the loss ratio for Heartland Express?",          QueryIntent.SQL),
    ("How many open claims does INS-1002 have?",               QueryIntent.SQL),
    ("What is the written premium for ACI-AL-25-732053?",      QueryIntent.SQL),
]

all_ok = True
for q, expected in cases:
    got    = r.detect_intent(q)
    ok     = got == expected
    all_ok = all_ok and ok
    print(f"  {'OK' if ok else 'FAIL'} [{expected:<8}] {q[:65]}")

assert all_ok, "Intent routing mismatch — check SQL_INTENT_KEYWORDS and REFERENCE_ID_PATTERN in retrieval.py"
print("\n✅ All 3 intent routes verified")

# COMMAND ----------

# MAGIC %md ## Test 1 — HYBRID search (semantic query)

# COMMAND ----------

# DBTITLE 1,Test 1 — HYBRID retrieval + LLM generation
from databricks.sdk.service.serving import ChatMessage as SDKMsg, ChatMessageRole

# HYBRID: ANN semantic search + BM25 blend — best for general policy/procedure questions
question = "What are the HAZMAT fleet referral triggers and minimum eligibility requirements?"
intent   = r.detect_intent(question)
assert intent == QueryIntent.HYBRID, f"Expected HYBRID, got {intent}"
print(f"Intent: {intent}\n")

# Retrieval
docs = r.search(question, user_role="underwriter", intent=intent)
ctx  = r.build_context(docs)
print(f"Retrieved {len(docs)} chunk(s):")
for d in docs[:5]:
    fname = d.source_path.split("/")[-1] if d.source_path else "?"
    print(f"  [{d.score:.3f}] [{d.category:<30}] {fname}")
print(f"\nContext block: {len(ctx)} chars")

# LLM generation
system = (
    "You are an expert commercial insurance underwriting assistant. "
    "Answer only from the provided context. Always cite the source document."
)
resp = w.serving_endpoints.query(
    name        = cfg.chat_model,
    messages    = [
        SDKMsg(role=ChatMessageRole.SYSTEM, content=f"{system}\n\n{ctx}"),
        SDKMsg(role=ChatMessageRole.USER,   content=question),
    ],
    max_tokens  = 600,
    temperature = 0.1,
)
answer = resp.choices[0].message.content
print(f"\n{chr(9472)*60}")
print(f"Q: {question}")
print(f"\nA: {answer[:700]}")

# COMMAND ----------

# MAGIC %md ## Test 2 — KEYWORD search (exact ID lookup)

# COMMAND ----------

# DBTITLE 1,Test 2 — KEYWORD retrieval + generation
from databricks.sdk.service.serving import ChatMessage as SDKMsg, ChatMessageRole

# KEYWORD: BM25-only — reference IDs are better served by exact string match than ANN
question = "Review submission SUB-26-11065 and summarise the key risk factors"
intent   = r.detect_intent(question)
assert intent == QueryIntent.KEYWORD, f"Expected KEYWORD, got {intent}"
print(f"Intent: {intent}\n")

# Retrieval
docs = r.search(question, user_role="senior_underwriter", intent=intent)
ctx  = r.build_context(docs)
print(f"Retrieved {len(docs)} chunk(s) for SUB-26-11065:")
for d in docs[:4]:
    fname = d.source_path.split("/")[-1] if d.source_path else "?"
    print(f"  [{d.score:.3f}] [{d.category:<30}] {fname}")

# LLM generation (only if index has data)
if docs and ctx:
    resp = w.serving_endpoints.query(
        name        = cfg.chat_model,
        messages    = [
            SDKMsg(role=ChatMessageRole.SYSTEM,
                   content=f"Answer from the provided context. Cite source documents.\n\n{ctx}"),
            SDKMsg(role=ChatMessageRole.USER, content=question),
        ],
        max_tokens  = 400,
        temperature = 0.1,
    )
    print(f"\nA: {resp.choices[0].message.content[:500]}")
else:
    print("\nNo chunks returned — run 02_chunk_and_index to populate the VS index first.")

# COMMAND ----------

# DBTITLE 1,Test 3 — SQL path header
# MAGIC %md ## Test 3 — SQL intent path (structured data queries)

# COMMAND ----------

# DBTITLE 1,Test 3 — SQL intent detection + Delta table queries
# SQL path: HybridRetriever.search() returns [] for SQL intent
# The caller (agent) is responsible for routing to structured Delta tables
sql_cases = [
    "What is the loss ratio for Heartland Express Logistics?",
    "How many open claims does INS-1002 have?",
    "What is the written premium for ACI-AL-25-732053?",
]

print("Intent classification for SQL questions:")
for q in sql_cases:
    intent = r.detect_intent(q)
    assert intent == QueryIntent.SQL, f"Expected SQL, got {intent} for: {q}"
    # Confirm search() correctly returns [] — caller handles SQL routing
    docs = r.search(q, user_role="underwriter", intent=intent)
    assert docs == [], f"Expected [] from search() for SQL intent, got {len(docs)} docs"
    print(f"  ✅ SQL (search=[]) | {q[:65]}")

# ── Execute structured queries against the Delta tables ──────────────────────
C, S = cfg.catalog, cfg.schema

print("\n── Loss runs for INS-1001 (past 3 periods) ")
display(spark.sql(f"""
    SELECT policy_period, claim_count, earned_premium,
           total_incurred, loss_ratio
    FROM   {C}.{S}.loss_runs
    WHERE  insured_id = 'INS-1001'
    ORDER  BY policy_period DESC
    LIMIT  3
"""))

print("── Open claims for INS-1002 ")
display(spark.sql(f"""
    SELECT claim_id, claim_type, total_incurred, reserve_amount, litigation_flag
    FROM   {C}.{S}.claims
    WHERE  insured_id = 'INS-1002'
      AND  claim_status = 'Open'
    ORDER  BY total_incurred DESC
"""))

# COMMAND ----------

# MAGIC %md ## Test 3 — RBAC filter (broker sees subset)

# COMMAND ----------

# DBTITLE 1,Test 4 — RBAC filter (3-role comparison)
# RBAC: category filter applied server-side at VS query layer — cannot be bypassed
question = "What are the product guidelines and underwriting procedures?"

roles = {
    "underwriter":     "all categories",
    "broker":          "Product Guides / UW Guidelines / Policy Docs",
    "claims_adjuster": "Claims / Loss Runs / Regulatory",
}
results = {}
for role, desc in roles.items():
    docs = r.search(question, user_role=role, n_results=10)
    results[role] = docs
    cats = sorted({d.category for d in docs})
    print(f"  {role:<20} {len(docs):2d} chunks   {cats or '(empty)'}")

# Restricted roles must see <= unrestricted underwriter
assert len(results["broker"])          <= len(results["underwriter"]), "Broker RBAC failed"
assert len(results["claims_adjuster"]) <= len(results["underwriter"]), "Claims RBAC failed"

# Broker docs must only appear in allowed categories
broker_allowed = set(cfg.categories_for_role("broker") or [])
broker_got     = {d.category for d in results["broker"]}
unexpected     = broker_got - broker_allowed
assert not unexpected, f"Broker saw unexpected categories: {unexpected}"

print("\n✅ RBAC filter: correct across all 3 roles")

# COMMAND ----------

# DBTITLE 1,Step 2 — Local agent header
# MAGIC %md ## Step 2 — End-to-end: UWCopilotAgent.predict() (local, no serving endpoint)

# COMMAND ----------

# DBTITLE 1,Step 2 — UWCopilotAgent local end-to-end test
from uw_copilot.agent import UWCopilotAgent

# Initialize in-process: load_context(None) bootstraps cfg, w, retriever,
# guardrails, and system_prompt from prompts/system_prompt.md.
# This is equivalent to what the serving endpoint does on startup.
agent = UWCopilotAgent()
agent.load_context(None)
print(f"Agent ready  | model:  {agent.cfg.chat_model}")
print(f"             | vs:     {agent.cfg.vs_endpoint}")
print(f"             | prompt: {len(agent.system_prompt)} chars")

# Full pipeline: detect_intent → search → build_context → LLM → guardrails → response
question = "What are the referral thresholds for a fleet with a loss ratio above 75%?"
resp = agent.predict(
    context  = None,
    messages = [{"role": "user", "content": question}],
    params   = {"user_role": "underwriter"},
)
answer  = resp.choices[0].message.content
sources = (resp.metadata or {}).get("sources", [])

print(f"\n{chr(9472)*60}")
print(f"Q: {question}")
print(f"\nA: {answer[:700]}")
if sources:
    print(f"\nSources ({len(sources)}): {sources[:3]}")

# COMMAND ----------

# MAGIC %md ## Test 4 — End-to-end via serving endpoint (if deployed)

# COMMAND ----------

# DBTITLE 1,Step 3 — Serving endpoint smoke test
from databricks.sdk.service.serving import ChatMessage as SDKMsg, ChatMessageRole

try:
    resp = w.serving_endpoints.query(
        name        = cfg.serving_endpoint,
        messages    = [
            SDKMsg(
                role    = ChatMessageRole.USER,
                content = "What are the CSA thresholds that trigger an underwriting referral?",
            )
        ],
        max_tokens  = 300,
        temperature = 0.1,
    )
    answer = resp.choices[0].message.content if resp.choices else str(resp)
    print(f"✅ Endpoint [{cfg.serving_endpoint}] responded:")
    print(f"\n{answer[:500]}")
except Exception as e:
    print(f"Endpoint not available (expected before 09_deploy runs).")
    print(f"  {type(e).__name__}: {str(e)[:200]}")
    print(f"\nRun rag_pipeline/09_deploy to deploy the model first.")

# COMMAND ----------

# DBTITLE 1,Summary
print("✅ 03_rag_chain — integration tests complete")
print("   Intent routing:   HYBRID | KEYWORD | SQL  (all 3 paths)")
print("   RBAC enforcement: verified across underwriter / broker / claims_adjuster")
print("   LLM generation:   HYBRID + KEYWORD paths")
print("   Local agent:      UWCopilotAgent.predict() end-to-end")
print(f"\nNext: run 04_memory_and_rbac")

# COMMAND ----------

# DBTITLE 1,Step 4 — Register header
# MAGIC %md
# MAGIC ## Step 4 — Log & Register to Unity Catalog (optional)
# MAGIC
# MAGIC This is also executed by `09_deploy` for production registration.
# MAGIC Set `RUN_REGISTRATION = True` to register the current code as a new model version.

# COMMAND ----------

# DBTITLE 1,Step 4 — log_and_register_agent
from uw_copilot.agent import log_and_register_agent

RUN_REGISTRATION = False   # Set True to register this version

if RUN_REGISTRATION:
    model_uri = log_and_register_agent(cfg)
    print(f"\n✅ Registered: {model_uri}")
    print(f"\nNext: run 09_deploy to configure the serving endpoint traffic routing.")
else:
    print("Registration skipped (RUN_REGISTRATION = False).")
    print(f"  Target model:  {cfg.uc_model}")
    print(f"  Alias:         champion")
    print(f"\nSet RUN_REGISTRATION = True to register, or run 09_deploy for full deployment.")
