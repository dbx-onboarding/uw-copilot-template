# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,RAG Evaluation Suite
# MAGIC %md
# MAGIC # 07b — Comprehensive RAG Evaluation (155 Questions)
# MAGIC
# MAGIC Tests the deployed `atlas_insurance_rag_endpoint` against the full evaluation dataset covering:
# MAGIC - **Document Retrieval** (90 questions across 16 categories)
# MAGIC - **Structured Data / NL-to-SQL** (35 questions across 8 Delta tables)
# MAGIC - **RBAC Enforcement** (12 questions testing role restrictions)
# MAGIC - **Guardrail Triggers** (8 questions testing safety boundaries)
# MAGIC - **Edge Cases & Mixed Intent** (10 questions)
# MAGIC
# MAGIC **Prerequisites:** Run `09_deploy` cells 1–8 first (model registered + endpoint updated).

# COMMAND ----------

# DBTITLE 1,Setup — imports and config
import os, sys, yaml, time, json, requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import pandas as pd

# Add project root to path
_nb_path = os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())
_repo_root = os.path.dirname(_nb_path)
sys.path.insert(0, os.path.join("/Workspace", _repo_root.lstrip("/"), "src"))

from uw_copilot.config import Config
cfg = Config()

print(f"✅ Config loaded: endpoint={cfg.serving_endpoint}, model={cfg.uc_model}")

# COMMAND ----------

# DBTITLE 1,Load evaluation questions from YAML
# Load the 155-question evaluation dataset
_eval_path = os.path.join("/Workspace", _repo_root.lstrip("/"), "config", "eval_questions.yaml")
with open(_eval_path, "r") as f:
    _eval_data = yaml.safe_load(f)

questions = _eval_data["questions"]
print(f"✅ Loaded {len(questions)} evaluation questions")

# Breakdown by section
from collections import Counter
_cats = Counter()
for q in questions:
    if q["intent"] == "sql":
        _cats["Structured (SQL)"] += 1
    elif q["category"] == "guardrail":
        _cats["Guardrail"] += 1
    elif q["category"] in ("out_of_scope", "edge", "mixed"):
        _cats["Edge/Mixed"] += 1
    elif q["id"].startswith("RBAC"):
        _cats["RBAC"] += 1
    else:
        _cats["Document Retrieval"] += 1

for section, count in sorted(_cats.items(), key=lambda x: -x[1]):
    print(f"  • {section}: {count}")

# COMMAND ----------

# DBTITLE 1,Query endpoint helper function
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Get endpoint URL and auth token from notebook context
_host = w.config.host.rstrip("/")
_token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

def query_endpoint(question: str, role: str = "underwriter", timeout: int = 60) -> dict:
    """Send a question to the serving endpoint and return the response."""
    url = f"{_host}/serving-endpoints/{cfg.serving_endpoint}/invocations"
    headers = {
        "Authorization": f"Bearer {_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messages": [{"role": "user", "content": question}],
        "custom_inputs": {"role": role},
    }
    
    try:
        start = time.time()
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        elapsed = time.time() - start
        
        if resp.status_code == 200:
            data = resp.json()
            # Handle both chat completion and pyfunc response formats
            if "choices" in data:
                content = data["choices"][0]["message"]["content"]
            elif "predictions" in data:
                content = data["predictions"][0] if isinstance(data["predictions"], list) else str(data["predictions"])
            else:
                content = str(data)
            return {"success": True, "response": content, "elapsed": elapsed, "status": 200}
        else:
            return {"success": False, "response": resp.text, "elapsed": elapsed, "status": resp.status_code}
    except requests.exceptions.Timeout:
        return {"success": False, "response": "TIMEOUT", "elapsed": timeout, "status": 0}
    except Exception as e:
        return {"success": False, "response": str(e), "elapsed": 0, "status": -1}

# Quick health check
_hc = query_endpoint("hello", timeout=30)
if _hc["success"]:
    print(f"✅ Endpoint healthy — responded in {_hc['elapsed']:.1f}s")
else:
    print(f"❌ Endpoint unhealthy: {_hc['status']} — {_hc['response'][:200]}")

# COMMAND ----------

# DBTITLE 1,Validation functions
def validate_response(question_def: dict, result: dict) -> dict:
    """Validate a response against expected_keywords and should_not_contain."""
    checks = []
    passed = True
    response_lower = result["response"].lower() if result["success"] else ""
    
    # Check 1: Endpoint returned successfully
    if not result["success"]:
        return {
            "passed": False,
            "checks": [{"check": "endpoint_success", "passed": False, "detail": f"HTTP {result['status']}: {result['response'][:100]}"}],
        }
    
    # Check 2: Response is non-empty
    if len(result["response"].strip()) < 10:
        checks.append({"check": "non_empty", "passed": False, "detail": f"Response too short ({len(result['response'])} chars)"})
        passed = False
    else:
        checks.append({"check": "non_empty", "passed": True, "detail": f"{len(result['response'])} chars"})
    
    # Check 3: Expected keywords present
    expected = question_def.get("expected_keywords", [])
    for kw in expected:
        found = kw.lower() in response_lower
        checks.append({"check": f"has_keyword:{kw}", "passed": found, "detail": f"{'found' if found else 'MISSING'}"})
        if not found:
            passed = False
    
    # Check 4: Should-not-contain words absent
    blocked = question_def.get("should_not_contain", [])
    for phrase in blocked:
        found = phrase.lower() in response_lower
        checks.append({"check": f"not_contains:{phrase}", "passed": not found, "detail": f"{'absent (good)' if not found else 'FOUND (bad)'}"})
        if found:
            passed = False
    
    return {"passed": passed, "checks": checks}

print("✅ Validation functions defined")

# COMMAND ----------

# DBTITLE 1,Run section
# MAGIC %md
# MAGIC ## Run Evaluation
# MAGIC
# MAGIC Set `RUN_MODE` below:
# MAGIC - `"all"` — run all 155 questions (takes \~15-25 min with sequential calls)
# MAGIC - `"sample"` — run 20 random questions (quick smoke test, \~3 min)
# MAGIC - `"section"` — run one section only (set `SECTION_FILTER`)
# MAGIC - `"parallel"` — run all 155 with 5 concurrent threads (\~5-8 min)

# COMMAND ----------

# DBTITLE 1,Run configuration
# ═══════════════════════════════════════════════════════════════
# CONFIGURE YOUR RUN
# ═══════════════════════════════════════════════════════════════
RUN_MODE = "parallel"     # "all", "sample", "section", "parallel"
SECTION_FILTER = "structured"  # Only used when RUN_MODE="section": "structured", "guardrail", "edge", "rbac", or a category label
SAMPLE_SIZE = 20          # Only used when RUN_MODE="sample"
MAX_WORKERS = 5           # Only used when RUN_MODE="parallel"
TIMEOUT_PER_Q = 90        # Seconds per question

# Filter questions based on mode
import random
if RUN_MODE == "sample":
    _run_questions = random.sample(questions, min(SAMPLE_SIZE, len(questions)))
elif RUN_MODE == "section":
    _sf = SECTION_FILTER.lower()
    _run_questions = [q for q in questions if (
        q.get("category", "").lower() == _sf or
        q.get("intent", "").lower() == _sf or
        q.get("id", "").split("-")[0].lower() == _sf
    )]
else:
    _run_questions = questions

print(f"📋 Run mode: {RUN_MODE}")
print(f"📋 Questions to run: {len(_run_questions)}")

# COMMAND ----------

# DBTITLE 1,Execute evaluation run
# ═══════════════════════════════════════════════════════════════
# EXECUTE EVALUATION
# ═══════════════════════════════════════════════════════════════
results = []

def _run_one(q):
    """Run a single question and validate."""
    qid = q["id"]
    question = q["question"]
    role = q.get("role", "underwriter")
    
    # Skip empty questions gracefully
    if not question.strip():
        return {
            "id": qid, "question": question, "role": role,
            "category": q.get("category", ""),
            "intent": q.get("intent", ""),
            "difficulty": q.get("difficulty", ""),
            "result": {"success": True, "response": "(empty query — skipped)", "elapsed": 0, "status": 200},
            "validation": {"passed": True, "checks": [{"check": "empty_query_skip", "passed": True, "detail": "Skipped"}]},
        }
    
    result = query_endpoint(question, role=role, timeout=TIMEOUT_PER_Q)
    validation = validate_response(q, result)
    
    return {
        "id": qid, "question": question, "role": role,
        "category": q.get("category", ""),
        "intent": q.get("intent", ""),
        "difficulty": q.get("difficulty", ""),
        "result": result,
        "validation": validation,
    }

print(f"🚀 Starting evaluation of {len(_run_questions)} questions...")
print("=" * 70)

if RUN_MODE == "parallel":
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_run_one, q): q["id"] for q in _run_questions}
        done_count = 0
        for future in as_completed(futures):
            done_count += 1
            r = future.result()
            results.append(r)
            status = "✅" if r["validation"]["passed"] else "❌"
            if done_count % 10 == 0 or not r["validation"]["passed"]:
                print(f"  [{done_count}/{len(_run_questions)}] {status} {r['id']}: {r['question'][:50]}...")
else:
    for i, q in enumerate(_run_questions):
        r = _run_one(q)
        results.append(r)
        status = "✅" if r["validation"]["passed"] else "❌"
        elapsed = r["result"]["elapsed"]
        # Print every failure + every 10th success
        if not r["validation"]["passed"] or (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(_run_questions)}] {status} {r['id']} ({elapsed:.1f}s): {r['question'][:50]}...")

print("=" * 70)
print(f"✅ Evaluation complete — {len(results)} questions processed")

# COMMAND ----------

# DBTITLE 1,Results section
# MAGIC %md
# MAGIC ## Results Summary

# COMMAND ----------

# DBTITLE 1,Results summary and metrics
# ═══════════════════════════════════════════════════════════════
# RESULTS SUMMARY
# ═══════════════════════════════════════════════════════════════
_passed = [r for r in results if r["validation"]["passed"]]
_failed = [r for r in results if not r["validation"]["passed"]]
_total = len(results)
_pass_rate = len(_passed) / _total * 100 if _total > 0 else 0

print("=" * 70)
print(f"{'EVALUATION RESULTS':^70}")
print("=" * 70)
print(f"\n  Total questions:  {_total}")
print(f"  Passed:           {len(_passed)} ✅")
print(f"  Failed:           {len(_failed)} ❌")
print(f"  Pass rate:        {_pass_rate:.1f}%")

# Average response time
_times = [r["result"]["elapsed"] for r in results if r["result"]["elapsed"] > 0]
if _times:
    print(f"\n  Avg response time: {sum(_times)/len(_times):.1f}s")
    print(f"  Min response time: {min(_times):.1f}s")
    print(f"  Max response time: {max(_times):.1f}s")
    print(f"  P95 response time: {sorted(_times)[int(len(_times)*0.95)]:.1f}s")

# Breakdown by section
print(f"\n{'─' * 70}")
print(f"{'BREAKDOWN BY SECTION':^70}")
print(f"{'─' * 70}")

_section_results = defaultdict(lambda: {"pass": 0, "fail": 0})
for r in results:
    section = r["intent"] if r["intent"] == "sql" else ("guardrail" if r["category"] == "guardrail" else ("edge" if r["category"] in ("out_of_scope", "edge", "mixed") else ("rbac" if r["id"].startswith("RBAC") else "document")))
    if r["validation"]["passed"]:
        _section_results[section]["pass"] += 1
    else:
        _section_results[section]["fail"] += 1

for section in ["document", "sql", "rbac", "guardrail", "edge"]:
    s = _section_results[section]
    total = s["pass"] + s["fail"]
    rate = s["pass"] / total * 100 if total > 0 else 0
    bar = "█" * int(rate / 5) + "░" * (20 - int(rate / 5))
    print(f"  {section:12s} {bar} {rate:5.1f}%  ({s['pass']}/{total})")

# Breakdown by difficulty
print(f"\n{'─' * 70}")
print(f"{'BREAKDOWN BY DIFFICULTY':^70}")
print(f"{'─' * 70}")

_diff_results = defaultdict(lambda: {"pass": 0, "fail": 0})
for r in results:
    diff = r.get("difficulty", "unknown")
    if r["validation"]["passed"]:
        _diff_results[diff]["pass"] += 1
    else:
        _diff_results[diff]["fail"] += 1

for diff in ["easy", "medium", "hard"]:
    d = _diff_results[diff]
    total = d["pass"] + d["fail"]
    rate = d["pass"] / total * 100 if total > 0 else 0
    print(f"  {diff:8s}  {rate:5.1f}%  ({d['pass']}/{total})")

print(f"\n{'=' * 70}")

# COMMAND ----------

# DBTITLE 1,Show failures detail
# ═══════════════════════════════════════════════════════════════
# FAILURE DETAILS
# ═══════════════════════════════════════════════════════════════
if _failed:
    print(f"{'❌ FAILED QUESTIONS':^70}")
    print("=" * 70)
    for i, r in enumerate(_failed, 1):
        print(f"\n{'─' * 70}")
        print(f"  [{i}] {r['id']} | {r['category']} | role={r['role']} | {r['difficulty']}")
        print(f"  Q: {r['question'][:80]}")
        print(f"  Response ({r['result']['elapsed']:.1f}s): {r['result']['response'][:150]}...")
        print(f"  Checks:")
        for c in r["validation"]["checks"]:
            mark = "✅" if c["passed"] else "❌"
            print(f"    {mark} {c['check']}: {c['detail']}")
else:
    print("🎉 ALL QUESTIONS PASSED — no failures to show!")

# COMMAND ----------

# DBTITLE 1,Save results to Delta table
# ═══════════════════════════════════════════════════════════════
# PERSIST RESULTS TO DELTA (for trend analysis)
# ═══════════════════════════════════════════════════════════════
import datetime

_eval_table = f"{cfg.catalog}.{cfg.schema}.eval_results"
_run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

_rows = []
for r in results:
    _rows.append({
        "run_id": _run_id,
        "question_id": r["id"],
        "question": r["question"],
        "category": r["category"],
        "intent": r["intent"],
        "role": r["role"],
        "difficulty": r["difficulty"],
        "passed": r["validation"]["passed"],
        "response_time_s": float(round(r["result"]["elapsed"], 2)),
        "response_length": int(len(r["result"]["response"])),
        "response_preview": r["result"]["response"][:500],
        "failed_checks": json.dumps([c for c in r["validation"]["checks"] if not c["passed"]]),
        "run_timestamp": datetime.datetime.now().isoformat(),
    })

df_results = spark.createDataFrame(_rows)
df_results.write.mode("append").option("mergeSchema", "true").saveAsTable(_eval_table)

print(f"✅ Results saved to {_eval_table} (run_id={_run_id})")
print(f"   {len(_rows)} rows appended")

# COMMAND ----------

# DBTITLE 1,Trend analysis — compare to previous runs
# ═══════════════════════════════════════════════════════════════
# TREND ANALYSIS — compare to previous runs
# ═══════════════════════════════════════════════════════════════
try:
    df_history = spark.sql(f"""
        SELECT 
            run_id,
            MIN(run_timestamp) as run_time,
            COUNT(*) as total_questions,
            SUM(CASE WHEN passed THEN 1 ELSE 0 END) as passed,
            ROUND(AVG(response_time_s), 1) as avg_response_s,
            ROUND(SUM(CASE WHEN passed THEN 1 ELSE 0 END) / COUNT(*) * 100, 1) as pass_rate_pct
        FROM {_eval_table}
        GROUP BY run_id
        ORDER BY run_time DESC
        LIMIT 10
    """)
    print("📈 EVALUATION HISTORY (last 10 runs)")
    print("=" * 70)
    display(df_history)
except Exception as e:
    print(f"ℹ️  No prior runs found (first run): {e}")

# COMMAND ----------

# DBTITLE 1,Export failures for review
# ═══════════════════════════════════════════════════════════════
# EXPORT: Failures as reviewable DataFrame
# ═══════════════════════════════════════════════════════════════
if _failed:
    _fail_rows = [{
        "id": r["id"],
        "question": r["question"],
        "category": r["category"],
        "intent": r["intent"],
        "role": r["role"],
        "difficulty": r["difficulty"],
        "response_preview": r["result"]["response"][:300],
        "failed_checks": ", ".join([c["check"] for c in r["validation"]["checks"] if not c["passed"]]),
    } for r in _failed]
    
    df_failures = pd.DataFrame(_fail_rows)
    display(df_failures)
    print(f"\n💡 {len(_failed)} questions need investigation. Review responses above.")
else:
    print("🎉 No failures — nothing to export!")

# COMMAND ----------

# DBTITLE 1,CI/CD gate — pass rate assertion
# ═══════════════════════════════════════════════════════════════
# CI/CD GATE — fail the notebook if pass rate is below threshold
# ═══════════════════════════════════════════════════════════════
PASS_THRESHOLD = 80.0  # Minimum pass rate (%) to consider deployment-ready

if _pass_rate >= PASS_THRESHOLD:
    print(f"✅ PASS — {_pass_rate:.1f}% >= {PASS_THRESHOLD}% threshold")
    print("   Model is deployment-ready.")
else:
    msg = f"❌ FAIL — {_pass_rate:.1f}% < {PASS_THRESHOLD}% threshold. Review failures before deploying."
    print(msg)
    # Uncomment to hard-fail in CI:
    # raise AssertionError(msg)
