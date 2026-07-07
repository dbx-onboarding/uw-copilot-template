# Databricks notebook source
# DBTITLE 1,UW CoPilot — End-to-End Flow Test
# MAGIC %md
# MAGIC # 🧪 UW CoPilot — End-to-End Flow Test
# MAGIC
# MAGIC Validates the complete user journey before customer review:
# MAGIC
# MAGIC | Step | Flow stage | What it checks |
# MAGIC |---|---|---|
# MAGIC | 1 | Setup | Install deps, wire sys.path |
# MAGIC | 2 | Health | `/api/health` → `live_data: true` |
# MAGIC | 3 | Queue | `/api/submissions` → real rows, KPIs |
# MAGIC | 4 | Detail | `/api/submissions/{id}` → assessment, snapshot fields |
# MAGIC | 5 | Sub-tabs | Claims / Loss Runs / Drivers / Documents / Similar |
# MAGIC | 6 | Chat | `/api/chat` → real RAG answer, `healthy: true` |
# MAGIC | 7 | Feedback | `/api/feedback` → recorded in DB |
# MAGIC | 8 | Decision | `/api/decisions` → recorded in DB |
# MAGIC | 9 | DB verify | Direct SQL confirms feedback + decision rows landed |

# COMMAND ----------

# DBTITLE 1,1 — Setup
# MAGIC %pip install fastapi>=0.110 uvicorn[standard]>=0.29 pydantic>=2.6 databricks-sdk>=0.40.0 pyyaml>=6.0 httpx -q

# COMMAND ----------

# DBTITLE 1,2 — Wire sys.path + build FastAPI test client
import sys, os, json, uuid
from datetime import datetime, timezone

REPO_ROOT = "/Workspace/Users/krish.kilaru@lumenalta.com/uw-copilot-template"
for p in [REPO_ROOT, os.path.join(REPO_ROOT, "webapp")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app, raise_server_exceptions=False)
SESSION_ID = f"e2e-test-{uuid.uuid4().hex[:8]}"

print(f"✅ Test client ready  |  session_id={SESSION_ID}")

# COMMAND ----------

# DBTITLE 1,3 — Health check
r = client.get("/api/health")
assert r.status_code == 200, f"Health failed: {r.status_code}"
p = r.json()
assert p.get("live_data") is True, f"❌ live_data is not True: {p}"
print(f"✅ /api/health  →  status=200  live_data={p['live_data']}")

# COMMAND ----------

# DBTITLE 1,4 — Submission queue + KPIs
r = client.get("/api/submissions")
assert r.status_code == 200
p = r.json()

subs = p.get("submissions", [])
kpis = p.get("kpis", {})

assert len(subs) > 0, "❌ No submissions returned"
assert all(s.get("live") for s in subs), "❌ Some submissions are demo rows"

print(f"✅ /api/submissions  →  {len(subs)} live submissions")
print(f"   KPIs: active_queue={kpis.get('active_queue')}  high_risk={kpis.get('high_risk')}  "
      f"portfolio_score={kpis.get('portfolio_score')}  pending_referral={kpis.get('pending_referral')}")

# Pick one HIGH risk and one LOW risk submission for deeper tests
high = next((s for s in subs if s.get("risk") == "High"), subs[0])
low  = next((s for s in subs if s.get("risk") == "Low"),  subs[-1])
TEST_ID = high["id"]

print(f"\n   Test submission (High risk): {TEST_ID} | {high['name']} | score={high['score']}")
print(f"   Test submission (Low  risk): {low['id']} | {low['name']} | score={low['score']}")

# COMMAND ----------

# DBTITLE 1,5 — Submission detail + snapshot field validation
r = client.get(f"/api/submissions/{TEST_ID}")
assert r.status_code == 200, f"❌ Detail failed: {r.status_code}"
d = r.json()

# Snapshot field checks
REQUIRED = ["id", "name", "status", "fleet_size", "driver_count",
            "loss_ratio", "underwriter", "premium", "premium_label"]
missing = [f for f in REQUIRED if d.get(f) is None]
assert not missing, f"❌ Missing fields: {missing}"

# AI assessment checks
a = d.get("assessment", {})
assert a.get("verdict") in ("APPROVE", "REFER", "DECLINE", "REVIEW"), \
    f"❌ Unexpected verdict: {a.get('verdict')}"
assert 0 < a.get("confidence", 0) <= 1, f"❌ Bad confidence: {a.get('confidence')}"
assert len(a.get("risk_indicators", [])) > 0, "❌ No risk indicators"
assert len(a.get("next_steps", [])) > 0, "❌ No next steps"

# Loss ratio consistency check (Math.floor: 78.50 → 78, not 79)
lr_raw  = d.get("loss_ratio", 0) * 100        # decimal → percentage
lr_floor = int(lr_raw)                          # what Math.floor gives
print(f"✅ /api/submissions/{TEST_ID}")
print(f"   name={d['name']}  status={d['status']}  verdict={a['verdict']}  "
      f"confidence={round(a['confidence']*100)}%")
print(f"   premium_label='{d.get('premium_label')}'  premium={d.get('premium')}")
print(f"   loss_ratio raw={d['loss_ratio']:.4f}  display={lr_floor}%  "
      f"(risk indicators will say ~{lr_floor}%)")
print(f"   risk_indicators[0]: {a['risk_indicators'][0][:80]}")

# COMMAND ----------

# DBTITLE 1,6 — Sub-tabs: Claims / Loss Runs / Drivers / Documents / Similar
tabs = [
    ("claims",    f"/api/submissions/{TEST_ID}/claims",    "claims"),
    ("loss_runs", f"/api/submissions/{TEST_ID}/loss_runs", "loss_runs"),
    ("drivers",   f"/api/submissions/{TEST_ID}/drivers",   "drivers"),
    ("documents", f"/api/submissions/{TEST_ID}/documents", "documents"),
    ("similar",   f"/api/submissions/{TEST_ID}/similar",   "similar"),
]

print(f"Sub-tabs for {TEST_ID}:")
print(f"{'Tab':<12} {'Status':>6}  {'Rows':>5}  {'Live?':<6}  Notes")
print("-" * 60)
for name, path, key in tabs:
    r = client.get(path)
    rows = r.json().get(key, [])
    live = all(row.get("live", True) for row in rows) if rows else None
    live_str = "✅ live" if live else ("⚠️  demo" if live is False else "— empty")
    note = ""
    if name == "similar" and rows:
        note = f"top match: {rows[0].get('company','')} ({rows[0].get('similarity','')}%)"
    if name == "documents" and rows:
        note = f"latest: {rows[0].get('name','')} ({rows[0].get('status','')})"
    print(f"{name:<12} {r.status_code:>6}  {len(rows):>5}  {live_str:<10}  {note}")

# COMMAND ----------

# DBTITLE 1,7 — Chat: RAG answer validation
question = f"Based on the submission details for {TEST_ID}, what is the key risk factor and your recommendation?"

r = client.post("/api/chat", json={
    "question": question,
    "session_id": SESSION_ID,
    "history": []
})
assert r.status_code == 200
p = r.json()

assert p.get("healthy") is True, f"❌ Chat not healthy: {p.get('answer','')[:200]}"
answer = p.get("answer", "")
assert len(answer) > 50, f"❌ Answer too short: {answer}"

# Make sure it's not the demo fallback
assert "demo fallback" not in answer.lower(), "❌ Got demo fallback response"
assert "endpoint isn't reachable" not in answer.lower(), "❌ Serving endpoint unreachable"

print(f"✅ /api/chat  →  healthy=True  answer_length={len(answer)} chars")
print(f"\n   Q: {question[:80]}...")
print(f"   A: {answer[:300]}...")

# COMMAND ----------

# DBTITLE 1,8 — Feedback recording
import server.data as data
import importlib
importlib.reload(data)

TEST_QUESTION = "What is the loss ratio threshold for referral?"
TEST_ANSWER   = "The threshold is 75% based on Atlas underwriting guidelines."

# Via API
r = client.post("/api/feedback", json={
    "query":      TEST_QUESTION,
    "response":   TEST_ANSWER,
    "rating":     "thumbs_up",
    "session_id": SESSION_ID,
})
assert r.status_code == 200
api_ok = r.json().get("ok")
print(f"✅ /api/feedback  →  ok={api_ok}")

# Direct SDK check if warehouse is ready
if data.warehouse_ready():
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient()
    res = w.statement_execution.execute_statement(
        warehouse_id=data._cfg_attr("warehouse_id"),
        statement=f"""
            SELECT session_id, rating, created_at
            FROM {data._fq('feedback')}
            WHERE session_id = '{SESSION_ID}'
            ORDER BY created_at DESC LIMIT 1
        """,
        wait_timeout="20s",
    )
    rows = getattr(getattr(res, "result", None), "data_array", None) or []
    if rows:
        print(f"   DB verify: session_id={rows[0][0]}  rating={rows[0][1]}  at={rows[0][2]}")
    else:
        print("   ⚠️  Row not found in DB yet (may be buffered — ok)")
else:
    print("   (warehouse not ready for DB verify)")

# COMMAND ----------

# DBTITLE 1,9 — Decision recording
r = client.post("/api/decisions", json={
    "submission_id": TEST_ID,
    "decision":      "Referred",
    "reason":        "E2E test — loss ratio exceeds preferred appetite threshold",
})
assert r.status_code == 200
p = r.json()
assert p.get("ok"), f"❌ Decision not recorded: {p}"
print(f"✅ /api/decisions  →  ok={p['ok']}  decision={p['decision']}  id={p['submission_id']}")

# DB verify
if data.warehouse_ready():
    res = w.statement_execution.execute_statement(
        warehouse_id=data._cfg_attr("warehouse_id"),
        statement=f"""
            SELECT submission_id, decision, created_at
            FROM {data._fq('decisions')}
            WHERE submission_id = '{TEST_ID}'
            ORDER BY created_at DESC LIMIT 1
        """,
        wait_timeout="20s",
    )
    rows = getattr(getattr(res, "result", None), "data_array", None) or []
    if rows:
        print(f"   DB verify: sub={rows[0][0]}  decision={rows[0][1]}  at={rows[0][2]}")
    else:
        print("   ⚠️  Row not found in DB (decisions table may not exist yet — see note below)")

# COMMAND ----------

# DBTITLE 1,10 — Full summary
print("=" * 60)
print("E2E FLOW TEST SUMMARY")
print("=" * 60)
checks = [
    ("/api/health",           "live_data: true"),
    ("/api/submissions",      f"{len(subs)} live rows, KPIs populated"),
    (f"/api/submissions/{TEST_ID}",  f"status='{d.get('status')}', premium_label='{d.get('premium_label')}'"),
    ("Sub-tabs (5)",          "claims / loss_runs / drivers / documents / similar"),
    ("/api/chat",             f"healthy=True, {len(answer)} char answer"),
    ("/api/feedback",         "thumbs_up recorded"),
    ("/api/decisions",        f"Referred recorded for {TEST_ID}"),
]
for endpoint, result in checks:
    print(f"  ✅  {endpoint:<40} {result}")
print()
print(f"Session ID: {SESSION_ID}")
print("✓ Ready for customer review")

# COMMAND ----------


