# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,UW CoPilot Webapp — Local Test
# MAGIC %md
# MAGIC # 🧪 UW CoPilot Webapp — Local Test
# MAGIC
# MAGIC Runs the webapp backend directly on Databricks compute to validate all connections **before** deploying to Databricks Apps.
# MAGIC
# MAGIC | Step | What it checks |
# MAGIC |---|---|
# MAGIC | 1 | Install requirements |
# MAGIC | 2 | Config loads + resource names derived correctly |
# MAGIC | 3 | SQL Warehouse connectivity + live table queries |
# MAGIC | 4 | Vector Search index query |
# MAGIC | 5 | Serving endpoint (RAG chat) |
# MAGIC | 6 | Full FastAPI app smoke test (in-process) |

# COMMAND ----------

# DBTITLE 1,1 — Install requirements
# MAGIC %pip install fastapi>=0.110 uvicorn[standard]>=0.29 pydantic>=2.6 databricks-sdk>=0.40.0 pyyaml>=6.0 httpx -q

# COMMAND ----------

# DBTITLE 1,2 — Set up sys.path so imports resolve from repo root
import sys, os

# Repo root = two levels up from this notebook (uw-copilot-template/)
REPO_ROOT = "/Workspace/Users/krish.kilaru@lumenalta.com/uw-copilot-template"
assert os.path.isdir(REPO_ROOT), f"Repo root not found: {REPO_ROOT}"

# Add repo root + webapp to sys.path so 'server' and 'src' packages resolve
for p in [REPO_ROOT, os.path.join(REPO_ROOT, "webapp")]:
    if p not in sys.path:
        sys.path.insert(0, p)

print("✅ sys.path set")
print(f"   REPO_ROOT : {REPO_ROOT}")
print(f"   webapp    : {os.path.join(REPO_ROOT, 'webapp')}")

# COMMAND ----------

# DBTITLE 1,3 — Config: load and print derived resource names
import importlib.util

# Load Config directly by file path (same way data.py does it)
config_py = os.path.join(REPO_ROOT, "src", "uw_copilot", "config.py")
config_yaml = os.path.join(REPO_ROOT, "config", "company_config.yaml")

assert os.path.exists(config_py),   f"❌ config.py not found: {config_py}"
assert os.path.exists(config_yaml), f"❌ company_config.yaml not found: {config_yaml}"

spec = importlib.util.spec_from_file_location("uw_copilot_config", config_py)
mod  = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
Config = mod.Config

cfg = Config(config_yaml)
cfg.print_summary()

print()
print("🔑 Key runtime values:")
print(f"   warehouse_id     : {cfg.warehouse_id}")
print(f"   vs_index         : {cfg.vs_index}")
print(f"   serving_endpoint : {cfg.serving_endpoint}")
print(f"   catalog.schema   : {cfg.catalog}.{cfg.schema}")

# COMMAND ----------

# DBTITLE 1,4 — Warehouse: connectivity + live table row counts
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

def run_sql(sql):
    res = w.statement_execution.execute_statement(
        warehouse_id=cfg.warehouse_id,
        statement=sql,
        wait_timeout="30s",
    )
    state = res.status.state.value
    if state in ("FAILED", "CANCELED", "CLOSED"):
        return None, state
    cols = [c.name for c in res.manifest.schema.columns]
    rows = res.result.data_array or []
    return [{k: v for k, v in zip(cols, r)} for r in rows], state

# Check each operational table
tables = ["submissions", "insureds", "drivers", "claims", "loss_runs",
          "loss_ratios", "policies", "referrals", "parsed_documents"]

print(f"{'Table':<25} {'Rows':>8}  Status")
print("-" * 45)
for t in tables:
    fq = f"{cfg.catalog}.{cfg.schema}.{t}"
    rows, state = run_sql(f"SELECT COUNT(*) AS n FROM {fq}")
    if rows:
        count = rows[0]['n']
        flag  = "✅" if int(count) > 0 else "⚠️  empty"
        print(f"{t:<25} {count:>8}  {flag}")
    else:
        print(f"{t:<25} {'—':>8}  ❌ {state}")

# COMMAND ----------

# DBTITLE 1,5 — Vector Search: query the index
print(f"VS index: {cfg.vs_index}")

try:
    resp = w.vector_search_indexes.query_index(
        index_name=cfg.vs_index,
        columns=["chunk_id", "category", "chunk_text"],
        query_text="commercial trucking fleet loss ratio high risk",
        num_results=3,
        query_type="HYBRID",
    )
    rows = getattr(getattr(resp, "result", None), "data_array", None) or []
    print(f"✅ VS query returned {len(rows)} result(s)")
    for i, r in enumerate(rows, 1):
        print(f"   [{i}] chunk_id={r[0]}  category={r[1]}  text={str(r[2])[:80]}...")
except Exception as e:
    print(f"❌ VS query failed: {e}")

# COMMAND ----------

# DBTITLE 1,6 — Serving endpoint: single chat turn
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

print(f"Serving endpoint: {cfg.serving_endpoint}")

try:
    resp = w.serving_endpoints.query(
        name=cfg.serving_endpoint,
        messages=[
            ChatMessage(role=ChatMessageRole.USER,
                        content="What is the maximum fleet size for a preferred risk?")
        ],
    )
    # Extract answer
    answer = None
    choices = getattr(resp, "choices", None)
    if choices:
        answer = getattr(getattr(choices[0], "message", None), "content", None)
    if not answer:
        answer = getattr(resp, "content", None) or str(resp)
    print(f"✅ Serving endpoint response:")
    print(f"   {str(answer)[:300]}")
except Exception as e:
    print(f"❌ Serving endpoint failed: {e}")

# COMMAND ----------

# DBTITLE 1,7 — data.py integration: exercise all API functions
# Import data.py — uses __file__-relative path resolution
# Since we added REPO_ROOT/webapp to sys.path, 'server' resolves correctly.
# data.py's _REPO_ROOT walks 3 levels up from server/data.py:
#   data.py → server/ → webapp/ → REPO_ROOT ✅
import importlib
import server.data as data
importlib.reload(data)  # ensure fresh import

print("=" * 55)
print("data.warehouse_ready()  :", data.warehouse_ready())
print("=" * 55)

# Submission queue
queue = data.submission_queue()
print(f"\n📋 submission_queue()  → {len(queue)} rows  (live={queue[0].get('live', False) if queue else 'n/a'})")
if queue:
    s = queue[0]
    print(f"   First: {s['id']} | {s['name']} | risk={s['risk']} | score={s['score']}")

# Submission detail (first ID from queue)
if queue:
    sid = queue[0]['id']
    detail = data.submission_detail(sid)
    print(f"\n🔍 submission_detail({sid})")
    print(f"   assessment keys: {list(detail.get('assessment', {}).keys()) if detail else '—'}")

    # Sub-tables
    claims   = data.claims_for(sid)
    loss_runs= data.loss_runs_for(sid)
    drivers  = data.drivers_for(sid)
    docs     = data.documents_for(sid)
    similar  = data.similar_risks(detail or {})
    print(f"\n📊 Sub-tables for {sid}:")
    print(f"   claims    : {len(claims)}")
    print(f"   loss_runs : {len(loss_runs)}")
    print(f"   drivers   : {len(drivers)}")
    print(f"   documents : {len(docs)}")
    print(f"   similar   : {len(similar)}")

print("\n✅ data.py integration complete")

# COMMAND ----------

# DBTITLE 1,8 — FastAPI smoke test (in-process HTTP)
# Spin up the FastAPI app in-process using HTTPX's async client — no port needed.
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app, raise_server_exceptions=False)

routes_to_test = [
    ("/api/health",      "GET",  None),
    ("/api/me",          "GET",  None),
    ("/api/submissions", "GET",  None),
]

print(f"{'Route':<30} {'Status':>6}  Notes")
print("-" * 65)
for path, method, body in routes_to_test:
    r = client.get(path) if method == "GET" else client.post(path, json=body)
    payload = r.json()
    note = ""
    if path == "/api/health":
        note = f"live_data={payload.get('live_data')}"
    elif path == "/api/me":
        note = f"company={payload.get('company')}  live={payload.get('live_data')}"
    elif path == "/api/submissions":
        subs = payload.get('submissions', [])
        note = f"{len(subs)} submissions  kpis={list(payload.get('kpis', {}).keys())}"
    status_emoji = "✅" if r.status_code == 200 else "❌"
    print(f"{path:<30} {r.status_code:>6}  {status_emoji} {note}")

# Chat endpoint
chat_r = client.post("/api/chat", json={
    "question": "What loss ratio threshold triggers a referral?",
    "session_id": "test-001",
    "history": []
})
chat_payload = chat_r.json()
print(f"\n/api/chat  →  status={chat_r.status_code}  healthy={chat_payload.get('healthy')}")
print(f"  answer[:200]: {str(chat_payload.get('answer', ''))[:200]}")

# COMMAND ----------

# DBTITLE 1,✅ Summary
# MAGIC %md
# MAGIC ## Results checklist
# MAGIC
# MAGIC After running all cells, confirm:
# MAGIC
# MAGIC - [ ] Config loads — resource names match `atlas_insurance_rag` / `atlas_insurance_vs_endpoint` / `atlas_insurance_rag_endpoint`
# MAGIC - [ ] All 8 operational tables have rows (`live=True` in submissions)
# MAGIC - [ ] VS query returns ≥ 1 result
# MAGIC - [ ] Serving endpoint returns a real answer (not the demo fallback)
# MAGIC - [ ] `/api/health` → `live_data: true`
# MAGIC - [ ] `/api/submissions` → real rows (not demo)
# MAGIC - [ ] `/api/chat` → `healthy: true`
# MAGIC
# MAGIC If all pass → run the deploy cell below.
# MAGIC
# MAGIC ```python
# MAGIC # Deploy when ready
# MAGIC import subprocess
# MAGIC subprocess.run([
# MAGIC     "databricks", "apps", "deploy", "atlas-insurance-uw-copilot-app",
# MAGIC     "--source-code-path", "/Workspace/Users/krish.kilaru@lumenalta.com/uw-copilot-template",
# MAGIC     "--no-wait"
# MAGIC ], check=True)
# MAGIC ```

# COMMAND ----------


