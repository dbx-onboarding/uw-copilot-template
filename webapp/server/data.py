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
from datetime import datetime, timedelta, timezone
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

    _today = datetime.now()
    _OPEN = {"received", "new", "in review", "pending info", "pending", "quoting"}
    out = []
    for r in rows:
        lr = float(r.get("loss_ratio_3yr") or 0)
        lr_dec = lr / 100.0 if lr > 1 else lr
        score = int(min(lr_dec * 100, 100))
        risk = "High" if lr_dec > 0.75 else "Medium" if lr_dec > 0.55 else "Low"
        status = r.get("submission_status") or "New"
        # Aging / SLA — days since the submission arrived; SLA target 7 business days.
        received = str(r.get("submission_date") or "")
        days = None
        try:
            days = (_today - datetime.strptime(received[:10], "%Y-%m-%d")).days
        except Exception:
            pass
        is_open = str(status).lower() in _OPEN
        if days is not None and is_open and days > 7:
            aging = "Overdue"
        elif days is not None and is_open and days >= 5:
            aging = "Due soon"
        else:
            aging = "On track"
        out.append({
            "id": r.get("submission_id"),
            "name": r.get("company_name"),
            "broker": r.get("broker_name"),
            "lob": "Commercial Auto",
            "received": received,
            "days_in_queue": days,
            "aging": aging,
            "status": status,
            "account_type": "Renewal" if r.get("expiring_premium") not in (None, 0) else "New Business",
            "score": score,
            "risk": risk,
            "referral": bool(r.get("referral_required")),
            "fleet_size": r.get("fleet_size"),
            "driver_count": r.get("driver_count"),
            "loss_ratio": lr_dec,
            "premium": _money(r.get("quoted_premium") or r.get("expiring_premium")),
            "premium_label": "Quoted Premium" if r.get("quoted_premium") else "Expiring Premium",
            "underwriter": r.get("underwriter"),
            "owner": r.get("underwriter") or "Unassigned",
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

    # New business vs. renewal: a renewal has an expiring Atlas policy to renew.
    exp = (row or {}).get("expiring_premium")
    has_expiring = exp not in (None, 0, "0", "")
    detail["account_type"] = "Renewal" if has_expiring else "New Business"
    detail["has_history"] = bool((row or {}).get("num_claims"))

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


def all_claims(limit: int = 200) -> List[Dict[str, Any]]:
    """Portfolio-wide claims (for the Claims section), joined to insured names."""
    sql = f"""
        SELECT c.claim_id, c.loss_date, c.loss_type, c.claim_status, c.total_incurred,
               c.total_paid, c.case_reserves, c.litigation_status, c.loss_description,
               i.company_name
        FROM {_fq('claims')} c
        LEFT JOIN {_fq('insureds')} i ON c.insured_id = i.insured_id
        ORDER BY c.total_incurred DESC LIMIT {int(limit)}
    """
    rows = _rows_as_dicts(_run_sql(sql))
    if rows:
        return [{
            "claim_id": r.get("claim_id"), "company": r.get("company_name"),
            "date": str(r.get("loss_date") or ""), "type": r.get("loss_type"),
            "status": r.get("claim_status"), "litigation": r.get("litigation_status"),
            "incurred": _money(r.get("total_incurred")), "paid": _money(r.get("total_paid")),
            "reserves": _money(r.get("case_reserves")), "description": r.get("loss_description"),
        } for r in rows]
    return [] if warehouse_ready() else _demo_all_claims()


def loss_control_overview(limit: int = 200) -> List[Dict[str, Any]]:
    """Fleet safety / CSA posture per insured (for the Loss Control section)."""
    sql = f"""
        SELECT company_name, state_domicile, fleet_size, driver_count, safety_rating,
               csa_unsafe_driving, csa_vehicle_maint, dashcam_coverage_pct,
               telematics_provider, risk_tier
        FROM {_fq('insureds')} ORDER BY csa_unsafe_driving DESC LIMIT {int(limit)}
    """
    rows = _rows_as_dicts(_run_sql(sql))
    if rows:
        return [{
            "company": r.get("company_name"), "state": r.get("state_domicile"),
            "fleet_size": r.get("fleet_size"), "driver_count": r.get("driver_count"),
            "safety_rating": r.get("safety_rating"),
            "csa_unsafe": r.get("csa_unsafe_driving"), "csa_maint": r.get("csa_vehicle_maint"),
            "dashcam_pct": r.get("dashcam_coverage_pct"),
            "telematics": r.get("telematics_provider") or "—", "risk_tier": r.get("risk_tier"),
        } for r in rows]
    return [] if warehouse_ready() else _demo_loss_control()


def settings_info() -> Dict[str, Any]:
    """Read-only configuration surface for the Settings section (no secrets)."""
    cfg = get_config()

    def g(k):
        return getattr(cfg, k, None) if cfg else None

    return {
        "company": g("company_name") or "Atlas Commercial Insurance",
        "catalog": g("catalog") or "—",
        "schema": g("schema") or "—",
        "warehouse_configured": bool(g("warehouse_id")),
        "warehouse_ready": warehouse_ready(),
        "serving_endpoint_configured": bool(g("serving_endpoint")),
        "vector_index_configured": bool(g("vs_index")),
    }


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


# ── Rate adequacy / pricing ─────────────────────────────────────────────────────
def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def pricing_for(sub_id: str) -> Dict[str, Any]:
    """Derive an indicated premium, rate need vs. expiring, and adequacy of the quote."""
    sql = f"""
        SELECT s.expiring_premium, s.quoted_premium, s.fleet_size, s.loss_ratio_3yr,
               s.primary_operation
        FROM {_fq('submissions')} s WHERE s.submission_id = '{_esc(sub_id)}' LIMIT 1
    """
    rows = _rows_as_dicts(_run_sql(sql))
    if not rows:
        return {} if warehouse_ready() else _demo_pricing()
    r = rows[0]
    exp = _num(r.get("expiring_premium"))
    quoted = _num(r.get("quoted_premium"))
    units = int(r.get("fleet_size") or 0)
    lr = _num(r.get("loss_ratio_3yr")) or 0
    lr = lr / 100.0 if lr > 1 else lr
    op = r.get("primary_operation") or ""

    TREND = 1.077  # ~1.5 yrs of 5% annual loss trend to mid-term
    incurred_3yr = exp * lr if (exp and lr) else None
    if exp and lr:
        indicated = incurred_3yr / _TARGET_LR * TREND
        basis = "Experience-rated from expiring earned premium and 3-yr loss ratio"
    else:
        bench = {"Long Haul": 8200, "Regional": 7000, "Intermediate": 6500,
                 "Local": 5200, "Intermodal": 6800, "Dedicated": 6000}.get(op, 7000)
        adj = (lr / _TARGET_LR) if lr else 1.0
        indicated = units * bench * max(0.85, min(adj, 2.0))
        basis = f"Class benchmark ${bench:,}/power unit (new business — no expiring premium)"
    indicated = round(indicated, -2)

    rate_need = (indicated / exp - 1) if exp else None
    rate_taken = (quoted / exp - 1) if (exp and quoted) else None
    if quoted:
        ratio = quoted / indicated if indicated else 1
        adequacy = "Adequate" if ratio >= 1.0 else "Marginal" if ratio >= 0.95 else "Inadequate"
    else:
        adequacy = "Indication only — no quote entered"

    return {
        "expiring_premium": _money(exp),
        "quoted_premium": _money(quoted),
        "indicated_premium": _money(indicated),
        "target_loss_ratio": f"{int(_TARGET_LR*100)}%",
        "loss_ratio_3yr": _pct(lr),
        "rate_need_pct": (f"{rate_need*100:+.1f}%" if rate_need is not None else None),
        "rate_taken_pct": (f"{rate_taken*100:+.1f}%" if rate_taken is not None else None),
        "adequacy": adequacy,
        "premium_per_unit_quoted": _money(quoted / units) if (quoted and units) else None,
        "premium_per_unit_indicated": _money(indicated / units) if units else None,
        "loss_cost_per_unit": _money(incurred_3yr / 3 / units) if (incurred_3yr and units) else None,
        "units": units,
        "basis": basis,
        "trend_note": "5% annual loss trend applied (~1.5 yr to mid-term).",
    }


# ── Authority, filings, market reason, FMCSA SMS posture ────────────────────────
def account_intel_for(sub_id: str) -> Dict[str, Any]:
    insured = _insured_id_for(sub_id)
    if not insured:
        return {} if warehouse_ready() else _demo_account_intel()
    sql = f"""
        SELECT authority_granted_date, prior_carrier, years_with_prior, reason_in_market,
               operating_radius, mcs150_current, mcs90_on_file, bmc91_on_file,
               oos_vehicle_pct, oos_driver_pct, national_oos_vehicle_avg,
               national_oos_driver_avg, crash_rate_per_100, csa_as_of, loss_runs_valued
        FROM {_fq('account_intel')} WHERE insured_id = '{_esc(insured)}' LIMIT 1
    """
    rows = _rows_as_dicts(_run_sql(sql))
    if not rows:
        return {} if warehouse_ready() else _demo_account_intel()
    r = rows[0]
    granted = str(r.get("authority_granted_date") or "")
    age = None
    try:
        gd = datetime.strptime(granted[:10], "%Y-%m-%d")
        age = round((datetime.now() - gd).days / 365.25, 1)
    except Exception:
        pass
    veh = _num(r.get("oos_vehicle_pct"))
    nveh = _num(r.get("national_oos_vehicle_avg"))
    drv = _num(r.get("oos_driver_pct"))
    ndrv = _num(r.get("national_oos_driver_avg"))
    return {
        "prior_carrier": r.get("prior_carrier"),
        "years_with_prior": r.get("years_with_prior"),
        "reason_in_market": r.get("reason_in_market"),
        "operating_radius": r.get("operating_radius"),
        "authority_granted": granted[:10],
        "authority_age_years": age,
        "new_authority": (age is not None and age < 3),
        "mcs150_current": bool(r.get("mcs150_current")),
        "mcs90_on_file": bool(r.get("mcs90_on_file")),
        "bmc91_on_file": bool(r.get("bmc91_on_file")),
        "oos_vehicle_pct": veh, "national_oos_vehicle_avg": nveh,
        "vehicle_oos_alert": (veh is not None and nveh is not None and veh > nveh),
        "oos_driver_pct": drv, "national_oos_driver_avg": ndrv,
        "driver_oos_alert": (drv is not None and ndrv is not None and drv > ndrv),
        "crash_rate_per_100": _num(r.get("crash_rate_per_100")),
        "csa_as_of": str(r.get("csa_as_of") or "")[:10],
        "loss_runs_valued": str(r.get("loss_runs_valued") or "")[:10],
    }


# ── Loss development (trend, severity, open reserves, as-of) ─────────────────────
def loss_dev_for(sub_id: str) -> Dict[str, Any]:
    insured = _insured_id_for(sub_id)
    if not insured:
        return {} if warehouse_ready() else _demo_loss_dev()
    sql = f"""
        SELECT policy_period, valuation_date, num_claims, total_incurred, total_paid,
               total_reserves, earned_premium, loss_ratio, large_losses, frequency, severity
        FROM {_fq('loss_runs')} WHERE insured_id = '{_esc(insured)}'
        ORDER BY policy_period ASC LIMIT 20
    """
    rows = _rows_as_dicts(_run_sql(sql))
    if not rows:
        return {} if warehouse_ready() else _demo_loss_dev()
    periods = [{
        "period": r.get("policy_period"),
        "valued": str(r.get("valuation_date") or "")[:10],
        "claims": r.get("num_claims"),
        "incurred": _money(r.get("total_incurred")),
        "paid": _money(r.get("total_paid")),
        "open_reserves": _money(r.get("total_reserves")),
        "earned_premium": _money(r.get("earned_premium")),
        "loss_ratio": _pct(r.get("loss_ratio")),
        "large_losses": r.get("large_losses"),
        "frequency": r.get("frequency"),
        "severity": _money(r.get("severity")),
    } for r in rows]
    first_lr = _num(rows[0].get("loss_ratio")) or 0
    last_lr = _num(rows[-1].get("loss_ratio")) or 0
    delta = last_lr - first_lr
    trend = "Deteriorating" if delta > 5 else "Improving" if delta < -5 else "Stable"
    summary = {
        "trend": trend,
        "trend_detail": f"3-yr loss ratio moved from {first_lr:.0f}% to {last_lr:.0f}%",
        "total_large_losses": sum(int(r.get("large_losses") or 0) for r in rows),
        "open_reserves": _money(sum(_num(r.get("total_reserves")) or 0 for r in rows)),
        "total_incurred": _money(sum(_num(r.get("total_incurred")) or 0 for r in rows)),
        "valued_as_of": str(rows[-1].get("valuation_date") or "")[:10],
    }
    return {"periods": periods, "summary": summary}


# ── Quote letter (broker-ready) ─────────────────────────────────────────────────
def quote_letter_data(sub_id: str) -> Optional[Dict[str, Any]]:
    """Assemble the fields for a broker-ready quote / indication letter."""
    d = submission_detail(sub_id)
    if not d:
        return None
    pr = pricing_for(sub_id) or {}
    a = d.get("assessment") or {}
    company = _cfg_attr("company_name") or "Atlas Commercial Insurance"
    now = datetime.now()
    return {
        "company": company,
        "date": now.strftime("%B %d, %Y"),
        "valid_until": (now + timedelta(days=30)).strftime("%B %d, %Y"),
        "broker": d.get("broker") or "Producing Broker",
        "insured": d.get("name") or "Insured",
        "submission_id": d.get("id") or sub_id,
        "account_type": d.get("account_type") or "New Business",
        "operation": d.get("operation") or "Commercial Auto",
        "commodity": d.get("commodity") or "",
        "fleet_size": d.get("fleet_size"),
        "limits": d.get("requested_limits") or "1,000,000 CSL",
        "quoted_premium": pr.get("quoted_premium") or d.get("premium") or "To be confirmed",
        "indicated_premium": pr.get("indicated_premium"),
        "adequacy": pr.get("adequacy"),
        "underwriter": d.get("underwriter") or "Atlas Underwriting",
        "verdict": a.get("verdict") or "REVIEW",
        "subjectivities": a.get("subjectivities") or [],
    }


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
         session_id: str, submission_id: str = "",
         submission_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    w = get_client()
    endpoint = _cfg_attr("serving_endpoint")
    if not (w and endpoint):
        return {
            "answer": (
                "_CoPilot endpoint isn't reachable in this environment (demo fallback)._\n\n"
                "When deployed on Databricks, answers are grounded in this account's own "
                "documents via Vector Search and every claim carries a citation, e.g.:\n\n"
                "> The 3-year loss ratio is 52%, driven by two BI claims in 2024–25. "
                "The account carries a Satisfactory DOT rating.\n\n"
                "**Sources:** Loss Run 2023–2026 (p.2) · ACORD 125 Application (p.1) · "
                "FMCSA SMS Snapshot (2026-06-01)\n\n"
                "If the documents don't contain the answer, the CoPilot says so rather than guessing."
            ),
            "healthy": False,
            "sources": [
                {"title": "Loss Run 2023–2026", "page": 2},
                {"title": "ACORD 125 Application", "page": 1},
                {"title": "FMCSA SMS Snapshot", "page": None},
            ],
        }
    try:
        from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
        msgs = [
            ChatMessage(role=ChatMessageRole(m["role"]), content=m["content"])
            for m in history[-10:] if m.get("role") in ("user", "assistant")
        ]
        # Prepend submission context so the RAG agent knows which account is open
        ctx_lines = []
        if submission_id:
            ctx_lines.append(f"Submission ID: {submission_id}")
        if submission_context:
            for k, v in submission_context.items():
                if v is not None and v != "":
                    ctx_lines.append(f"{k}: {v}")
        guidance = (
            "[Answering rules]\n"
            "Ground every statement in the retrieved Atlas documents. After your answer, add a "
            "'Sources:' line listing the source document(s) and page number(s) you used. If the "
            "documents do not contain the answer, say you don't know rather than guessing."
        )
        if ctx_lines:
            ctx_block = "[Current Submission Context]\n" + "\n".join(ctx_lines)
            enriched = f"{ctx_block}\n\n{guidance}\n\n[Question]\n{question}"
        else:
            enriched = f"{guidance}\n\n[Question]\n{question}"
        msgs.append(ChatMessage(role=ChatMessageRole.USER, content=enriched))
        resp = w.serving_endpoints.query(
            name=endpoint, messages=msgs,
            extra_params={"user_role": user_role, "session_id": session_id,
                          "submission_id": submission_id},
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
    ok = _run_sql(sql) is not None
    if ok:
        _STATUS_MAP = {
            "Approved":       "Quoted",
            "Referred":       "In Review",
            "Declined":       "Declined",
            "Info Requested": "In Review",
        }
        new_status = _STATUS_MAP.get(decision)
        if new_status:
            _run_sql(f"""
                UPDATE {_fq('submissions')}
                SET    submission_status = '{_esc(new_status)}'
                WHERE  submission_id     = '{_esc(submission_id)}'
            """)
    return ok


# ═══════════════════════════════════════════════════════════════════════════════
# Assessment logic (server-side, shared by list + detail)
# ═══════════════════════════════════════════════════════════════════════════════
_TARGET_LR = 0.65  # Atlas permissible/target loss ratio (RA-0001 §4.2)

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

    # ── Evidence: every driver carries its own rule reference so nothing is a
    #    black box. severity: adverse | caution | positive.
    ev: List[Dict[str, str]] = []
    if lr > 0.80:
        ev.append({"factor": "3-yr loss ratio", "value": f"{lr:.0%}",
                   "detail": f"exceeds the 80% referral threshold", "rule": "RA-0001 §4.2 Appetite", "severity": "adverse"})
    elif lr > _TARGET_LR:
        ev.append({"factor": "3-yr loss ratio", "value": f"{lr:.0%}",
                   "detail": f"above the {int(_TARGET_LR*100)}% target but within tolerance", "rule": "RA-0001 §4.2 Appetite", "severity": "caution"})
    else:
        ev.append({"factor": "3-yr loss ratio", "value": f"{lr:.0%}",
                   "detail": f"within the {int(_TARGET_LR*100)}% target", "rule": "RA-0001 §4.2 Appetite", "severity": "positive"})
    if csa > 65:
        ev.append({"factor": "CSA Unsafe Driving", "value": f"{csa:.0f}",
                   "detail": "above the 65th-percentile intervention threshold", "rule": "UW-0001 §6 CSA/SMS", "severity": "adverse"})
    elif csa > 50:
        ev.append({"factor": "CSA Unsafe Driving", "value": f"{csa:.0f}",
                   "detail": "elevated (50–65th percentile) — monitor", "rule": "UW-0001 §6 CSA/SMS", "severity": "caution"})
    elif csa > 0:
        ev.append({"factor": "CSA Unsafe Driving", "value": f"{csa:.0f}",
                   "detail": "below intervention thresholds", "rule": "UW-0001 §6 CSA/SMS", "severity": "positive"})
    if large > 1:
        ev.append({"factor": "Large losses", "value": f"{large}",
                   "detail": "two or more losses ≥$100K in the loss history", "rule": "CLM-0003 Large Loss", "severity": "adverse"})
    if safety in ("CONDITIONAL", "UNSATISFACTORY"):
        ev.append({"factor": "FMCSA safety rating", "value": safety.title(),
                   "detail": "non-Satisfactory DOT rating", "rule": "REG-0002 DOT/FMCSA", "severity": "adverse"})
    if fleet >= 40:
        ev.append({"factor": "Fleet size", "value": f"{fleet} units",
                   "detail": "large schedule — verify authority band and aggregation", "rule": "AUTH-0001 Authority", "severity": "caution"})
    if 0 < dashcam < 50:
        ev.append({"factor": "Dashcam coverage", "value": f"{dashcam:.0f}%",
                   "detail": "below the 50% telematics guideline", "rule": "LC-0009 Telematics", "severity": "caution"})
    if referral:
        ev.append({"factor": "Referral trigger", "value": "Yes",
                   "detail": "one or more mandatory referral conditions met", "rule": "AUTH-0001 Referral Matrix", "severity": "adverse"})

    adverse = [e for e in ev if e["severity"] == "adverse"]
    caution = [e for e in ev if e["severity"] == "caution"]

    if referral or lr > 0.80 or csa > 65 or safety in ("CONDITIONAL", "UNSATISFACTORY"):
        verdict = "REFER"
    elif lr > _TARGET_LR or caution:
        verdict = "REVIEW"
    else:
        verdict = "APPROVE"

    # Qualitative confidence = how clear-cut the evidence is (NOT a fake %).
    if not adverse and not caution:
        confidence_label = "High"
    elif len(adverse) <= 1:
        confidence_label = "Moderate"
    else:
        confidence_label = "Low"

    # Plain-language rationale.
    if verdict == "APPROVE":
        rationale = (f"Loss ratio {lr:.0%} is within appetite and no referral triggers fired; "
                     "clears for underwriting subject to standard subjectivities.")
    elif verdict == "REVIEW":
        lead = adverse[0] if adverse else (caution[0] if caution else None)
        why = f"{lead['factor'].lower()} {lead['value']}" if lead else "one or more caution items"
        rationale = (f"Within authority but {why} warrants a closer read before quoting; "
                     "not an automatic referral.")
    else:
        lead = adverse[0] if adverse else None
        why = f"{lead['factor'].lower()} ({lead['value']})" if lead else "a mandatory referral condition"
        rationale = (f"{why} breaches Atlas guidelines — refer to a senior underwriter per the "
                     "authority matrix before any indication is released.")

    indicators = [f"{e['factor']} {e['value']} — {e['detail']}" for e in (adverse + caution)] \
        or ["No adverse indicators identified"]

    steps: List[str] = []
    if referral:
        steps.append("Escalate to senior underwriter with a referral memo (AUTH-0001)")
    if lr > _TARGET_LR:
        steps.append("Pull 5-year loss runs and confirm reserve adequacy on open claims")
    if csa > 50 or safety in ("CONDITIONAL", "UNSATISFACTORY"):
        steps.append("Review FMCSA SMS profile and driver qualification files")
    steps.append("Verify current MVRs are on file for all scheduled drivers")
    steps.append("Confirm the written fleet-safety programme with the insured")

    # ── Recommended subjectivities to attach to a quote / bind.
    subs: List[str] = [
        "Signed, dated ACORD application(s) and MCS-150 verification current",
        "Current MVRs (within 60 days) for all scheduled drivers",
    ]
    if lr > _TARGET_LR:
        subs.append("Signed 5-year loss runs valued within 90 days of binding")
    if csa > 50 or safety in ("CONDITIONAL", "UNSATISFACTORY"):
        subs.append("Satisfactory fleet-safety survey / loss-control inspection within 60 days")
    if large > 1:
        subs.append("Prior-carrier large-loss detail and reserve confirmation on open claims")
    if 0 < dashcam < 50:
        subs.append("Plan to deploy inward/outward dashcams to ≥80% of the fleet within 90 days")

    return {
        "verdict": verdict,
        "confidence_label": confidence_label,
        "rationale": rationale,
        "evidence": ev,
        "risk_indicators": indicators[:6],
        "next_steps": steps[:4],
        "subjectivities": subs[:6],
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
        {"id": "SUB-26-12077", "name": "Ironhorse Freight Systems LLC", "broker": "Great Lakes Transport Insurance Brokers", "state": "IN", "lob": "Commercial Auto", "received": "2026-06-25", "status": "New", "score": 66, "risk": "Medium", "referral": False, "fleet_size": 8, "driver_count": 8, "loss_ratio": 0.66, "premium": "$118K", "annual_revenue": "$3.4M", "years_in_business": 9, "underwriter": "David Chen", "operation": "Regional", "commodity": "General Freight"},
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


def _demo_all_claims() -> List[Dict[str, Any]]:
    return [
        {"claim_id": "CLM-25-4522103", "company": "Eastern Seaboard Logistics LLC", "date": "2025-07-19", "type": "Combined", "status": "Open", "litigation": "Pre-Suit", "incurred": "$280K", "paid": "$0", "reserves": "$280K", "description": "Swoop-and-squat suspected staged collision; multiple claimants from one vehicle. SIU engaged."},
        {"claim_id": "CLM-25-3891045", "company": "Pacific Coast Carriers Inc", "date": "2025-08-18", "type": "Bodily Injury", "status": "Open", "litigation": "Suit Filed", "incurred": "$385K", "paid": "$120K", "reserves": "$265K", "description": "Third-party injury claim; litigation pending. Large open BI reserve under Reserve Committee review."},
        {"claim_id": "CLM-23-6789012", "company": "Summit Petroleum Transport LLC", "date": "2023-03-22", "type": "Bodily Injury", "status": "Closed", "litigation": "Settled", "incurred": "$310K", "paid": "$310K", "reserves": "$0", "description": "Tanker rollover on highway; no spill. Third-party occupant hospitalized with fractures. Settled."},
        {"claim_id": "CLM-26-7201452", "company": "Ironhorse Freight Systems LLC", "date": "2026-01-30", "type": "Cargo", "status": "Open", "litigation": "None", "incurred": "$42K", "paid": "$12K", "reserves": "$30K", "description": "Load shift damaged palletized goods in transit; salvage of undamaged units pursued."},
        {"claim_id": "CLM-25-7201451", "company": "Ironhorse Freight Systems LLC", "date": "2025-04-12", "type": "Physical Damage", "status": "Closed", "litigation": "None", "incurred": "$28K", "paid": "$28K", "reserves": "$0", "description": "Low-speed rear-end on I-70; bumper and trailer door damage. Clear liability, insured at fault."},
    ]


def _demo_loss_control() -> List[Dict[str, Any]]:
    return [
        {"company": "Eastern Seaboard Logistics LLC", "state": "NJ", "fleet_size": 55, "driver_count": 60, "safety_rating": "Conditional", "csa_unsafe": 52.1, "csa_maint": 55.3, "dashcam_pct": 65.0, "telematics": "KeepTruckin", "risk_tier": "Borderline"},
        {"company": "Lone Star Hauling Partners", "state": "TX", "fleet_size": 18, "driver_count": 20, "safety_rating": "Satisfactory", "csa_unsafe": 42.7, "csa_maint": 38.9, "dashcam_pct": 45.0, "telematics": "—", "risk_tier": "Borderline"},
        {"company": "Ironhorse Freight Systems LLC", "state": "IN", "fleet_size": 8, "driver_count": 8, "safety_rating": "Satisfactory", "csa_unsafe": 48.0, "csa_maint": 33.0, "dashcam_pct": 80.0, "telematics": "Samsara", "risk_tier": "Acceptable"},
        {"company": "Heartland Express Logistics", "state": "IL", "fleet_size": 85, "driver_count": 102, "safety_rating": "Satisfactory", "csa_unsafe": 22.4, "csa_maint": 18.7, "dashcam_pct": 92.0, "telematics": "Samsara", "risk_tier": "Preferred"},
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


def _demo_pricing() -> Dict[str, Any]:
    return {
        "expiring_premium": "$318K", "quoted_premium": "$342K", "indicated_premium": "$300K",
        "target_loss_ratio": "65%", "loss_ratio_3yr": "54%",
        "rate_need_pct": "-5.7%", "rate_taken_pct": "+7.5%", "adequacy": "Adequate",
        "premium_per_unit_quoted": "$7K", "premium_per_unit_indicated": "$6K",
        "loss_cost_per_unit": "$1K", "units": 47,
        "basis": "Experience-rated from expiring earned premium and 3-yr loss ratio (demo)",
        "trend_note": "5% annual loss trend applied (~1.5 yr to mid-term).",
    }


def _demo_account_intel() -> Dict[str, Any]:
    return {
        "prior_carrier": "Great West (demo)", "years_with_prior": 4,
        "reason_in_market": "Rate increase at renewal — testing the market",
        "operating_radius": "Long Haul (>500 mi)", "authority_granted": "2016-05-01",
        "authority_age_years": 10.2, "new_authority": False,
        "mcs150_current": True, "mcs90_on_file": True, "bmc91_on_file": True,
        "oos_vehicle_pct": 24.8, "national_oos_vehicle_avg": 20.7, "vehicle_oos_alert": True,
        "oos_driver_pct": 6.1, "national_oos_driver_avg": 5.5, "driver_oos_alert": True,
        "crash_rate_per_100": 3.1, "csa_as_of": "2026-06-01", "loss_runs_valued": "2026-05-15",
    }


def _demo_loss_dev() -> Dict[str, Any]:
    return {
        "periods": [
            {"period": "2023-2024", "valued": "2024-04-01", "claims": 4, "incurred": "$98K", "paid": "$98K", "open_reserves": "$0", "earned_premium": "$286K", "loss_ratio": "34%", "large_losses": 0, "frequency": 0.10, "severity": "$25K"},
            {"period": "2024-2025", "valued": "2025-04-01", "claims": 9, "incurred": "$291K", "paid": "$255K", "open_reserves": "$36K", "earned_premium": "$318K", "loss_ratio": "92%", "large_losses": 2, "frequency": 0.21, "severity": "$32K"},
            {"period": "2025-2026", "valued": "2026-06-15", "claims": 6, "incurred": "$186K", "paid": "$120K", "open_reserves": "$66K", "earned_premium": "$342K", "loss_ratio": "54%", "large_losses": 1, "frequency": 0.13, "severity": "$31K"},
        ],
        "summary": {
            "trend": "Improving", "trend_detail": "3-yr loss ratio moved from 34% to 54%",
            "total_large_losses": 3, "open_reserves": "$102K", "total_incurred": "$575K",
            "valued_as_of": "2026-06-15",
        },
    }
