"""
Data access layer for the UW CoPilot web app.

Reuses the `uw_copilot` package (Config, FeedbackManager) and the SQL Warehouse /
Vector Search / Model Serving endpoints. Every method degrades gracefully to demo
data when a warehouse is not configured or a call fails, so the app renders
everywhere — including local development with no Databricks connection.
"""

from __future__ import annotations

import importlib.util
import os
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Dict, List, Optional

# webapp/server/data.py -> repo root is two levels up from webapp/
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CONFIG_PY = os.path.join(_REPO_ROOT, "src", "uw_copilot", "config.py")


def _load_config_class():
    """
    Load the `Config` class directly from src/uw_copilot/config.py by file path.

    We intentionally do NOT `import uw_copilot`, because that package's __init__
    imports the MLflow agent — pulling heavy serving deps into the web app. config.py
    is self-contained (only depends on PyYAML), so loading it in isolation keeps the
    app lightweight and decoupled.
    """
    if not os.path.exists(_CONFIG_PY):
        return None
    try:
        spec = importlib.util.spec_from_file_location("uw_copilot_config", _CONFIG_PY)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore
        return getattr(mod, "Config", None)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Lazy singletons
# ═══════════════════════════════════════════════════════════════════════════════
@lru_cache(maxsize=1)
def get_config():
    """Load Config from config/company_config.yaml. None if unavailable."""
    Config = _load_config_class()
    if Config is None:
        return None
    for candidate in (os.path.join(_REPO_ROOT, "config", "company_config.yaml"), None):
        try:
            return Config(candidate) if candidate else Config()
        except Exception:
            continue
    return None


@lru_cache(maxsize=1)
def get_client():
    """WorkspaceClient singleton. None when credentials are not present."""
    try:
        from databricks.sdk import WorkspaceClient
        return WorkspaceClient()
    except Exception:
        return None


def _cfg_attr(name: str, default: Any = None) -> Any:
    cfg = get_config()
    return getattr(cfg, name, default) if cfg else default


def warehouse_ready() -> bool:
    return bool(_cfg_attr("warehouse_id")) and get_client() is not None


# ═══════════════════════════════════════════════════════════════════════════════
# SQL helper
# ═══════════════════════════════════════════════════════════════════════════════
def _run_sql(sql: str, timeout: str = "30s") -> Optional[Dict[str, Any]]:
    """Execute SQL via the Statement Execution API. Returns {columns, rows} or None."""
    if not warehouse_ready():
        return None
    w = get_client()
    try:
        result = w.statement_execution.execute_statement(
            warehouse_id=_cfg_attr("warehouse_id"),
            statement=sql,
            wait_timeout=timeout,
        )
        state = getattr(getattr(result, "status", None), "state", None)
        if state and getattr(state, "value", None) in ("FAILED", "CANCELED", "CLOSED"):
            return None
        manifest = getattr(result, "manifest", None)
        columns = (
            [c.name for c in manifest.schema.columns]
            if manifest and manifest.schema and manifest.schema.columns
            else []
        )
        rows = getattr(getattr(result, "result", None), "data_array", None) or []
        return {"columns": columns, "rows": rows}
    except Exception:
        return None


def _fq(table: str) -> str:
    return f"{_cfg_attr('catalog', 'atlas')}.{_cfg_attr('schema', 'atlas_insurance_rag')}.{table}"


def _rows_as_dicts(res: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not res or not res.get("rows"):
        return []
    cols = res["columns"]
    return [dict(zip(cols, r)) for r in res["rows"]]


# ═══════════════════════════════════════════════════════════════════════════════
# Submission queue
# ═══════════════════════════════════════════════════════════════════════════════
def submission_queue() -> List[Dict[str, Any]]:
    sql = f"""
        SELECT
            s.submission_id, s.company_name, s.broker_name, s.submission_date,
            s.submission_status, s.fleet_size, s.driver_count, s.primary_operation,
            s.primary_commodity, s.expiring_premium, s.quoted_premium,
            s.loss_ratio_3yr, s.underwriter, s.referral_required
        FROM {_fq('submissions')} s
        ORDER BY s.loss_ratio_3yr DESC NULLS LAST
        LIMIT 100
    """
    rows = _rows_as_dicts(_run_sql(sql))
    if not rows:
        return _demo_submissions()

    out = []
    for r in rows:
        lr = float(r.get("loss_ratio_3yr") or 0)
        lr_dec = lr / 100.0 if lr > 1 else lr
        score = int(min(lr_dec * 100, 100))
        risk = "High" if lr_dec > 0.75 else "Medium" if lr_dec > 0.55 else "Low"
        out.append({
            "id": r.get("submission_id"),
            "name": r.get("company_name"),
            "broker": r.get("broker_name"),
            "lob": "Commercial Auto",
            "received": str(r.get("submission_date") or ""),
            "status": r.get("submission_status") or "New",
            "score": score,
            "risk": risk,
            "referral": bool(r.get("referral_required")),
            "fleet_size": r.get("fleet_size"),
            "driver_count": r.get("driver_count"),
            "loss_ratio": lr_dec,
            "premium": _money(r.get("quoted_premium") or r.get("expiring_premium")),
            "premium_label": "Quoted Premium" if r.get("quoted_premium") else "Expiring Premium",
            "underwriter": r.get("underwriter"),
            "operation": r.get("primary_operation"),
            "commodity": r.get("primary_commodity"),
            "live": True,
        })
    return out


def submission_detail(sub_id: str) -> Optional[Dict[str, Any]]:
    queue = {s["id"]: s for s in submission_queue()}
    sel = queue.get(sub_id)

    sql = f"""
        SELECT
            s.submission_id, s.company_name, s.submission_status, s.fleet_size,
            s.driver_count, s.loss_ratio_3yr, s.referral_required, s.decline_reason,
            s.primary_operation, s.primary_commodity, s.quoted_premium, s.expiring_premium,
            s.requested_limits,
            i.safety_rating, i.csa_unsafe_driving, i.risk_tier, i.telematics_provider,
            i.dashcam_coverage_pct, i.annual_revenue, i.years_in_business, i.state_domicile,
            lr.num_claims, lr.large_losses, lr.frequency
        FROM {_fq('submissions')} s
        LEFT JOIN {_fq('insureds')} i ON s.insured_id = i.insured_id
        LEFT JOIN (
            SELECT insured_id, SUM(num_claims) AS num_claims,
                   SUM(large_losses) AS large_losses, AVG(frequency) AS frequency
            FROM {_fq('loss_runs')} GROUP BY insured_id
        ) lr ON i.insured_id = lr.insured_id
        WHERE s.submission_id = '{_esc(sub_id)}'
        LIMIT 1
    """
    rows = _rows_as_dicts(_run_sql(sql))
    row = rows[0] if rows else None

    if row is None and sel is None:
        return None

    base = sel or _demo_submission_by_id(sub_id) or {}
    assessment = _build_assessment(row, base)
    detail = dict(base)
    if row:
        detail.update({
            "annual_revenue": _money(row.get("annual_revenue")),
            "years_in_business": row.get("years_in_business"),
            "state": row.get("state_domicile") or base.get("state"),
            "safety_rating": row.get("safety_rating"),
            "risk_tier": row.get("risk_tier"),
            "requested_limits": row.get("requested_limits"),
            "num_claims": row.get("num_claims"),
        })
    detail["assessment"] = assessment
    return detail


# ── Operational sub-tables (these fill the previously-empty tabs) ───────────────
def claims_for(sub_id: str) -> List[Dict[str, Any]]:
    insured = _insured_id_for(sub_id)
    if insured:
        sql = f"""
            SELECT claim_id, loss_date, loss_type, claim_status, total_incurred,
                   total_paid, litigation_status, loss_description
            FROM {_fq('claims')} WHERE insured_id = '{_esc(insured)}'
            ORDER BY loss_date DESC LIMIT 50
        """
        rows = _rows_as_dicts(_run_sql(sql))
        if rows:
            return [{
                "claim_id": r.get("claim_id"),
                "date": str(r.get("loss_date") or ""),
                "type": r.get("loss_type"),
                "status": r.get("claim_status"),
                "incurred": _money(r.get("total_incurred")),
                "paid": _money(r.get("total_paid")),
                "litigation": r.get("litigation_status"),
                "description": r.get("loss_description"),
            } for r in rows]
    # In live mode, never show unrelated demo rows for an unlinked submission.
    return [] if warehouse_ready() else _demo_claims()


def loss_runs_for(sub_id: str) -> List[Dict[str, Any]]:
    insured = _insured_id_for(sub_id)
    if insured:
        sql = f"""
            SELECT policy_period, num_claims, total_incurred, earned_premium,
                   loss_ratio, large_losses, frequency
            FROM {_fq('loss_runs')} WHERE insured_id = '{_esc(insured)}'
            ORDER BY policy_period DESC LIMIT 20
        """
        rows = _rows_as_dicts(_run_sql(sql))
        if rows:
            return [{
                "period": r.get("policy_period"),
                "claims": r.get("num_claims"),
                "incurred": _money(r.get("total_incurred")),
                "earned_premium": _money(r.get("earned_premium")),
                "loss_ratio": _pct(r.get("loss_ratio")),
                "large_losses": r.get("large_losses"),
                "frequency": r.get("frequency"),
            } for r in rows]
    return [] if warehouse_ready() else _demo_loss_runs()


def drivers_for(sub_id: str) -> List[Dict[str, Any]]:
    insured = _insured_id_for(sub_id)
    if insured:
        sql = f"""
            SELECT driver_id, first_name, last_name, cdl_class, years_cdl_experience,
                   mvr_points, driver_status, accidents_3yr, violations_3yr,
                   hazmat_endorsement, telematics_score
            FROM {_fq('drivers')} WHERE insured_id = '{_esc(insured)}'
            ORDER BY mvr_points DESC LIMIT 100
        """
        rows = _rows_as_dicts(_run_sql(sql))
        if rows:
            return [{
                "driver_id": r.get("driver_id"),
                "name": f"{r.get('first_name','')} {r.get('last_name','')}".strip(),
                "cdl_class": r.get("cdl_class"),
                "experience": r.get("years_cdl_experience"),
                "mvr_points": r.get("mvr_points"),
                "status": r.get("driver_status"),
                "accidents": r.get("accidents_3yr"),
                "violations": r.get("violations_3yr"),
                "hazmat": bool(r.get("hazmat_endorsement")),
                "telematics": r.get("telematics_score"),
            } for r in rows]
    return [] if warehouse_ready() else _demo_drivers()


def documents_for(sub_id: str) -> List[Dict[str, Any]]:
    # parsed_documents doesn't carry insured_id; show recent parsed docs if available.
    sql = f"""
        SELECT file_name, category, page_count, parsed_at
        FROM {_fq('parsed_documents')}
        ORDER BY parsed_at DESC LIMIT 25
    """
    rows = _rows_as_dicts(_run_sql(sql))
    if rows:
        return [{
            "name": r.get("file_name"),
            "type": r.get("category"),
            "pages": r.get("page_count"),
            "status": "Indexed",
            "date": str(r.get("parsed_at") or "")[:10],
        } for r in rows]
    return [] if warehouse_ready() else _demo_documents()


# ═══════════════════════════════════════════════════════════════════════════════
# Similar risks (Vector Search)
# ═══════════════════════════════════════════════════════════════════════════════
_EXCLUDE_CATS = {"underwriting_manual", "risk_appetite", "endorsement", "regulatory", "form", "iso_form"}


def similar_risks(sub: Dict[str, Any]) -> List[Dict[str, Any]]:
    w = get_client()
    idx = _cfg_attr("vs_index")
    if not (w and idx):
        return _demo_similar_risks()
    lr = float(sub.get("loss_ratio") or 0)
    query = (
        f"commercial trucking fleet {sub.get('fleet_size') or ''} vehicles "
        f"{sub.get('state') or ''} loss ratio {lr:.0%} submission loss run claims history"
    )
    try:
        resp = w.vector_search_indexes.query_index(
            index_name=idx,
            columns=["chunk_id", "parent_id", "chunk_text", "category", "source_path"],
            query_text=query, num_results=20, query_type="HYBRID",
        )
        rows = getattr(getattr(resp, "result", None), "data_array", None) or []
        seen: Dict[str, Dict] = {}
        for row in rows:
            if len(row) < 5:
                continue
            category = (row[3] or "").strip().lower()
            if category in _EXCLUDE_CATS:
                continue
            source = row[4] or ""
            score = float(row[5]) if len(row) > 5 else 0.0
            fname = source.rstrip("/").split("/")[-1]
            key = fname.rsplit(".", 1)[0] if fname else source[:60]
            if not key:
                continue
            if key not in seen or score > seen[key]["score"]:
                seen[key] = {
                    "company": _fmt_doc_name(key),
                    "category": category.replace("_", " ").title(),
                    "score": score,
                    "similarity": min(int(score * 100), 99),
                    "live": True,
                }
        out = sorted(seen.values(), key=lambda x: -x["score"])[:4]
        return out or _demo_similar_risks()
    except Exception:
        return _demo_similar_risks()


# ═══════════════════════════════════════════════════════════════════════════════
# Chat (Model Serving proxy)
# ═══════════════════════════════════════════════════════════════════════════════
def chat(question: str, history: List[Dict[str, str]], user_role: str,
         session_id: str) -> Dict[str, Any]:
    w = get_client()
    endpoint = _cfg_attr("serving_endpoint")
    if not (w and endpoint):
        return {
            "answer": (
                "_CoPilot endpoint isn't reachable in this environment._\n\n"
                "This is the demo fallback. Once deployed on Databricks with the serving "
                "endpoint live, answers stream from your RAG agent with citations."
            ),
            "healthy": False,
        }
    try:
        from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
        msgs = [
            ChatMessage(role=ChatMessageRole(m["role"]), content=m["content"])
            for m in history[-10:] if m.get("role") in ("user", "assistant")
        ]
        msgs.append(ChatMessage(role=ChatMessageRole.USER, content=question))
        resp = w.serving_endpoints.query(
            name=endpoint, messages=msgs,
            extra_params={"user_role": user_role, "session_id": session_id},
        )
        return {"answer": resp.choices[0].message.content, "healthy": True}
    except Exception as e:
        return {"answer": f"Unable to reach the CoPilot endpoint.\n\n_{e}_", "healthy": False}


def record_feedback(user_id: str, query: str, response: str, rating: str,
                    session_id: str, user_role: str) -> bool:
    """
    Write feedback directly with the CORRECT copilot_feedback schema:
      columns question/answer/created_at, rating stored as INT (1 / -1),
      and session_id populated (the table column is NOT NULL).
    This avoids the column/type mismatches in uw_copilot.feedback.
    """
    if not warehouse_ready():
        return False
    import uuid
    rating_int = 1 if rating == "thumbs_up" else -1
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    sql = f"""
        INSERT INTO {_fq('copilot_feedback')}
            (feedback_id, session_id, user_id, question, answer, rating, comment, created_at)
        VALUES ('{uuid.uuid4()}', '{_esc(session_id)}', '{_esc(user_id)}',
                '{_esc(query)}', '{_esc(response)}', {rating_int}, NULL,
                TIMESTAMP '{now}')
    """
    return _run_sql(sql) is not None


def record_decision(submission_id: str, user_id: str, decision: str,
                    ai_recommendation: str = "", reason: Optional[str] = None,
                    session_id: str = "") -> bool:
    """
    Persist an underwriting decision to feedback_overrides. Captures the AI
    recommendation alongside the human decision so overrides are auditable.
    """
    if not warehouse_ready():
        return False
    import uuid
    insured = _insured_id_for(submission_id) or ""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    reason_sql = f"'{_esc(reason)}'" if reason else "NULL"
    sql = f"""
        INSERT INTO {_fq('feedback_overrides')}
            (override_id, session_id, user_id, submission_id, ai_recommendation,
             uw_decision, override_reason, override_detail, created_at)
        VALUES ('{uuid.uuid4()}', '{_esc(session_id)}', '{_esc(user_id)}',
                '{_esc(submission_id)}', '{_esc(ai_recommendation)}',
                '{_esc(decision)}', {reason_sql}, '{_esc(insured)}',
                TIMESTAMP '{now}')
    """
    return _run_sql(sql) is not None


# ═══════════════════════════════════════════════════════════════════════════════
# Assessment logic (server-side, shared by list + detail)
# ═══════════════════════════════════════════════════════════════════════════════
def _build_assessment(row: Optional[Dict[str, Any]], base: Dict[str, Any]) -> Dict[str, Any]:
    def g(k, d=None):
        if row and row.get(k) is not None:
            return row.get(k)
        return base.get(k, d)

    lr = float(g("loss_ratio_3yr", base.get("loss_ratio", 0)) or 0)
    lr = lr / 100.0 if lr > 1 else lr
    safety = str(g("safety_rating", "") or "").upper()
    csa = float(g("csa_unsafe_driving", 0) or 0)
    referral = bool(g("referral_required", base.get("referral", False)))
    fleet = int(g("fleet_size", 0) or 0)
    large = int(g("large_losses", 0) or 0)
    dashcam = float(g("dashcam_coverage_pct", 0) or 0)

    if referral or lr > 0.80 or csa > 65:
        verdict = "REFER"
    elif safety in ("CONDITIONAL", "UNSATISFACTORY"):
        verdict = "REFER"
    elif lr > 0.65:
        verdict = "REVIEW"
    else:
        verdict = "APPROVE"

    confidence = 0.88 if (lr < 0.75 and not referral) else 0.72

    indicators: List[str] = []
    if lr > 0.75:
        indicators.append(f"Loss ratio {lr:.0%} exceeds 75% appetite threshold")
    elif lr > 0.55:
        indicators.append(f"Loss ratio {lr:.0%} approaching appetite limit")
    if csa > 65:
        indicators.append(f"CSA Unsafe Driving score {csa:.0f} above 65 threshold")
    if large > 1:
        indicators.append(f"{large} large losses (>$100K) in loss history")
    if fleet >= 40:
        indicators.append(f"Large fleet ({fleet} units) — concentration risk")
    if safety in ("CONDITIONAL", "UNSATISFACTORY"):
        indicators.append(f"FMCSA safety rating: {safety.title()}")
    if 0 < dashcam < 50:
        indicators.append(f"Dashcam coverage only {dashcam:.0f}% of fleet")
    if not indicators:
        indicators.append("No adverse indicators identified")

    steps: List[str] = []
    if referral:
        steps.append("Escalate to senior underwriter with referral memo")
    if lr > 0.65:
        steps.append("Request 5-year loss runs and loss control report")
    if csa > 50:
        steps.append("Review FMCSA CSA profile and driver qualification files")
    steps.append("Verify MVR reports are on file for all drivers")
    steps.append("Confirm safety programme documentation with insured")

    return {
        "verdict": verdict,
        "confidence": round(confidence, 2),
        "risk_indicators": indicators[:5],
        "next_steps": steps[:4],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Small utilities
# ═══════════════════════════════════════════════════════════════════════════════
def _esc(s: str) -> str:
    return str(s).replace("'", "''")


def _money(v) -> Optional[str]:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return None
    if n >= 1_000_000:
        return f"${n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"${n/1_000:.0f}K"
    return f"${n:,.0f}"


def _pct(v) -> Optional[str]:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return None
    return f"{n:.0f}%" if n > 1 else f"{n*100:.0f}%"


def _fmt_doc_name(stem: str) -> str:
    for suffix in ("_lr_", "_loss_run", "_submission", "_application", "_policy",
                   "_acord", "_mvr", "_claims", "_2020", "_2021", "_2022",
                   "_2023", "_2024", "_2025", "_2026"):
        idx = stem.lower().find(suffix)
        if idx > 0:
            stem = stem[:idx]
            break
    return stem.replace("_", " ").replace("-", " ").title().strip()


@lru_cache(maxsize=64)
def _insured_id_for(sub_id: str) -> Optional[str]:
    res = _run_sql(f"SELECT insured_id FROM {_fq('submissions')} WHERE submission_id = '{_esc(sub_id)}' LIMIT 1")
    rows = _rows_as_dicts(res)
    return rows[0].get("insured_id") if rows else None


# ═══════════════════════════════════════════════════════════════════════════════
# Demo data (used when no warehouse is configured)
# ═══════════════════════════════════════════════════════════════════════════════
def _demo_submissions() -> List[Dict[str, Any]]:
    return [
        {"id": "SUB-2026-00147", "name": "ABC Trucking Co.", "broker": "Marsh McLennan", "state": "TX", "lob": "Commercial Auto", "received": "2026-07-07", "status": "New", "score": 92, "risk": "High", "referral": True, "fleet_size": 47, "driver_count": 58, "loss_ratio": 0.84, "premium": "$385K", "annual_revenue": "$12.4M", "years_in_business": 8, "underwriter": "Sarah Chen", "operation": "Long Haul", "commodity": "General Freight"},
        {"id": "SUB-2026-00146", "name": "Blue Ridge Freight LLC", "broker": "Aon", "state": "NC", "lob": "Commercial Auto", "received": "2026-07-07", "status": "New", "score": 88, "risk": "High", "referral": True, "fleet_size": 32, "driver_count": 40, "loss_ratio": 0.71, "premium": "$245K", "annual_revenue": "$8.7M", "years_in_business": 5, "underwriter": "Sarah Chen", "operation": "Regional", "commodity": "Refrigerated"},
        {"id": "SUB-2026-00145", "name": "Pacific Coast Carriers", "broker": "WTW", "state": "CA", "lob": "Commercial Auto", "received": "2026-07-07", "status": "In Review", "score": 68, "risk": "Medium", "referral": False, "fleet_size": 28, "driver_count": 33, "loss_ratio": 0.58, "premium": "$178K", "annual_revenue": "$6.2M", "years_in_business": 12, "underwriter": "Michael Torres", "operation": "Regional", "commodity": "General Freight"},
        {"id": "SUB-2026-00144", "name": "Delta Express Freight", "broker": "Brown & Brown", "state": "GA", "lob": "Commercial Auto", "received": "2026-07-06", "status": "In Review", "score": 56, "risk": "Medium", "referral": False, "fleet_size": 19, "driver_count": 22, "loss_ratio": 0.52, "premium": "$112K", "annual_revenue": "$4.1M", "years_in_business": 7, "underwriter": "Sarah Chen", "operation": "Local", "commodity": "General Freight"},
        {"id": "SUB-2026-00143", "name": "Lone Star Logistics Grp", "broker": "Gallagher", "state": "TX", "lob": "Commercial Auto", "received": "2026-07-06", "status": "Pending Info", "score": 38, "risk": "Low", "referral": False, "fleet_size": 12, "driver_count": 14, "loss_ratio": 0.38, "premium": "$67K", "annual_revenue": "$2.8M", "years_in_business": 15, "underwriter": "Jennifer Park", "operation": "Local", "commodity": "General Freight"},
        {"id": "SUB-2026-00142", "name": "Summit Transport Group", "broker": "HUB", "state": "CO", "lob": "Commercial Auto", "received": "2026-07-06", "status": "New", "score": 31, "risk": "Low", "referral": False, "fleet_size": 8, "driver_count": 9, "loss_ratio": 0.31, "premium": "$42K", "annual_revenue": "$1.9M", "years_in_business": 22, "underwriter": "Unassigned", "operation": "Local", "commodity": "General Freight"},
    ]


def _demo_submission_by_id(sub_id: str) -> Optional[Dict[str, Any]]:
    return next((s for s in _demo_submissions() if s["id"] == sub_id), None)


def _demo_claims() -> List[Dict[str, Any]]:
    return [
        {"claim_id": "CLM-26-0004821", "date": "2026-03-15", "type": "Collision", "status": "Closed", "incurred": "$45K", "paid": "$45K", "litigation": "None", "description": "Rear-end collision on I-35"},
        {"claim_id": "CLM-25-0009142", "date": "2025-11-02", "type": "Cargo", "status": "Closed", "incurred": "$29K", "paid": "$29K", "litigation": "None", "description": "Load shift damage during transit"},
        {"claim_id": "CLM-25-0007733", "date": "2025-08-18", "type": "Bodily Injury", "status": "Open", "incurred": "$112K", "paid": "$38K", "litigation": "Suit Filed", "description": "Third-party injury claim, litigation pending"},
    ]


def _demo_loss_runs() -> List[Dict[str, Any]]:
    return [
        {"period": "2025-2026", "claims": 6, "incurred": "$186K", "earned_premium": "$342K", "loss_ratio": "54%", "large_losses": 1, "frequency": 0.13},
        {"period": "2024-2025", "claims": 9, "incurred": "$291K", "earned_premium": "$318K", "loss_ratio": "92%", "large_losses": 2, "frequency": 0.21},
        {"period": "2023-2024", "claims": 4, "incurred": "$98K", "earned_premium": "$286K", "loss_ratio": "34%", "large_losses": 0, "frequency": 0.10},
    ]


def _demo_drivers() -> List[Dict[str, Any]]:
    return [
        {"driver_id": "DRV-1042", "name": "Marcus Webb", "cdl_class": "A", "experience": 14, "mvr_points": 6, "status": "Active", "accidents": 2, "violations": 3, "hazmat": True, "telematics": 71.5},
        {"driver_id": "DRV-1043", "name": "Denise Kohler", "cdl_class": "A", "experience": 9, "mvr_points": 2, "status": "Active", "accidents": 0, "violations": 1, "hazmat": False, "telematics": 88.0},
        {"driver_id": "DRV-1044", "name": "Ray Alonzo", "cdl_class": "A", "experience": 3, "mvr_points": 5, "status": "Active", "accidents": 1, "violations": 2, "hazmat": False, "telematics": 64.2},
        {"driver_id": "DRV-1045", "name": "Tom Farrell", "cdl_class": "B", "experience": 21, "mvr_points": 0, "status": "Active", "accidents": 0, "violations": 0, "hazmat": True, "telematics": 95.1},
    ]


def _demo_documents() -> List[Dict[str, Any]]:
    return [
        {"name": "ACORD 125 Application", "type": "Application", "status": "Indexed", "pages": 6, "date": "2026-07-07"},
        {"name": "Loss Run Summary 2023-2026", "type": "Loss Run", "status": "Indexed", "pages": 12, "date": "2026-07-07"},
        {"name": "Driver MVR Reports", "type": "Driver Info", "status": "Pending", "pages": None, "date": "—"},
        {"name": "Fleet Schedule", "type": "Vehicle", "status": "Indexed", "pages": 3, "date": "2026-07-06"},
        {"name": "Safety Program Documentation", "type": "Compliance", "status": "Pending", "pages": None, "date": "—"},
    ]


def _demo_similar_risks() -> List[Dict[str, Any]]:
    return [
        {"company": "Gulf Coast Haulers", "category": "Loss Run", "similarity": 94, "score": 0.94, "live": False},
        {"company": "Midwest Express", "category": "Submission", "similarity": 89, "score": 0.89, "live": False},
        {"company": "Eastern Freight Corp", "category": "Loss Run", "similarity": 82, "score": 0.82, "live": False},
    ]
