"""
UW CoPilot — FastAPI backend for Databricks Apps.

Serves JSON APIs backed by the `uw_copilot` package (SQL Warehouse, Vector Search,
Model Serving) and mounts the compiled React frontend at `/`.

User identity is read SERVER-SIDE from Databricks Apps forwarded headers — never
trusted from the client — which is the correct fix for the old app's hardcoded
user and client-controlled role.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import data

app = FastAPI(title="UW CoPilot", docs_url="/api/docs", openapi_url="/api/openapi.json")

_HERE = os.path.dirname(os.path.abspath(__file__))
_STATIC_DIR = os.path.join(os.path.dirname(_HERE), "frontend", "dist")


# ═══════════════════════════════════════════════════════════════════════════════
# Identity — resolved from Databricks Apps forwarded headers
# ═══════════════════════════════════════════════════════════════════════════════
def _resolve_role(email: str) -> str:
    """
    Map the authenticated user to an RBAC role using the config's rbac policy.
    Falls back to 'underwriter'. Role is decided on the server, not the client.
    """
    cfg = data.get_config()
    policy = getattr(cfg, "rbac_policy", None) if cfg else None
    if isinstance(policy, dict):
        # Optional convention: rbac_policy may include an "emails" -> role map.
        emails = policy.get("emails") if isinstance(policy.get("emails"), dict) else None
        if emails and email in emails:
            return emails[email]
    return "underwriter"


def identity(request: Request) -> Dict[str, str]:
    h = request.headers
    email = (
        h.get("X-Forwarded-Email")
        or h.get("X-Forwarded-Preferred-Username")
        or h.get("X-Forwarded-User")
        or ""
    )
    name = h.get("X-Forwarded-Preferred-Username") or email.split("@")[0] or "Underwriter"
    name = name.replace(".", " ").replace("_", " ").title()
    return {"email": email, "name": name, "role": _resolve_role(email)}


# ═══════════════════════════════════════════════════════════════════════════════
# Request models
# ═══════════════════════════════════════════════════════════════════════════════
class ChatBody(BaseModel):
    question: str
    session_id: str
    history: List[Dict[str, str]] = []


class FeedbackBody(BaseModel):
    query: str
    response: str
    rating: str          # "thumbs_up" | "thumbs_down"
    session_id: str


class DecisionBody(BaseModel):
    submission_id: str
    decision: str        # Approve | Refer | Decline | Request Info | Override
    reason: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# API routes
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/me")
def me(request: Request):
    ident = identity(request)
    cfg = data.get_config()
    return {
        **ident,
        "company": getattr(cfg, "company_name", "Atlas Commercial Insurance") if cfg else "Atlas Commercial Insurance",
        "live_data": data.warehouse_ready(),
    }


@app.get("/api/submissions")
def submissions():
    subs = data.submission_queue()
    return {"submissions": subs, "kpis": _kpis(subs)}


@app.get("/api/submissions/{sub_id}")
def submission(sub_id: str):
    detail = data.submission_detail(sub_id)
    if detail is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    return detail


@app.get("/api/submissions/{sub_id}/claims")
def claims(sub_id: str):
    return {"claims": data.claims_for(sub_id)}


@app.get("/api/submissions/{sub_id}/loss_runs")
def loss_runs(sub_id: str):
    return {"loss_runs": data.loss_runs_for(sub_id)}


@app.get("/api/submissions/{sub_id}/drivers")
def drivers(sub_id: str):
    return {"drivers": data.drivers_for(sub_id)}


@app.get("/api/submissions/{sub_id}/documents")
def documents(sub_id: str):
    return {"documents": data.documents_for(sub_id)}


@app.get("/api/submissions/{sub_id}/similar")
def similar(sub_id: str):
    detail = data.submission_detail(sub_id) or {"id": sub_id}
    return {"similar": data.similar_risks(detail)}


@app.post("/api/chat")
def chat(body: ChatBody, request: Request):
    ident = identity(request)
    return data.chat(body.question, body.history, ident["role"], body.session_id)


@app.post("/api/feedback")
def feedback(body: FeedbackBody, request: Request):
    ident = identity(request)
    ok = data.record_feedback(
        user_id=ident["email"] or ident["name"], query=body.query,
        response=body.response, rating=body.rating,
        session_id=body.session_id, user_role=ident["role"],
    )
    return {"ok": ok}


@app.post("/api/decisions")
def decisions(body: DecisionBody, request: Request):
    ident = identity(request)
    ok = data.record_decision(
        submission_id=body.submission_id, user_id=ident["email"] or ident["name"],
        decision=body.decision, reason=body.reason,
    )
    return {"ok": ok, "decision": body.decision, "submission_id": body.submission_id}


def _kpis(subs: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(subs)
    high = sum(1 for s in subs if s.get("risk") == "High")
    refs = sum(1 for s in subs if s.get("referral"))
    new = sum(1 for s in subs if s.get("status") == "New")
    avg = int(sum(s.get("score") or 0 for s in subs) / n) if n else 0
    return {
        "active_queue": n,
        "new_submissions": new,
        "high_risk": high,
        "pending_referral": refs,
        "portfolio_score": avg,
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "live_data": data.warehouse_ready()}


# ═══════════════════════════════════════════════════════════════════════════════
# Static frontend (mounted last so /api/* takes precedence)
# ═══════════════════════════════════════════════════════════════════════════════
if os.path.isdir(_STATIC_DIR):
    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
else:
    @app.get("/")
    def _no_build():
        return JSONResponse(
            {"message": "Frontend not built. Run `npm --prefix frontend install && npm --prefix frontend run build`."},
            status_code=200,
        )
