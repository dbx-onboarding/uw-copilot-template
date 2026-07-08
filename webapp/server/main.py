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
from fastapi.responses import HTMLResponse, JSONResponse, Response
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
    # Display name from the email local-part only — never title-case the domain.
    local = (email.split("@")[0] if "@" in email else email) \
        or h.get("X-Forwarded-Preferred-Username") or "underwriter"
    name = local.replace(".", " ").replace("_", " ").title()
    return {"email": email, "name": name, "role": _resolve_role(email)}


# ═══════════════════════════════════════════════════════════════════════════════
# Request models
# ═══════════════════════════════════════════════════════════════════════════════
class ChatBody(BaseModel):
    question: str
    session_id: str
    history: List[Dict[str, str]] = []
    submission_id: str = ""
    submission_context: Optional[Dict[str, Any]] = None


class FeedbackBody(BaseModel):
    query: str
    response: str
    rating: str          # "thumbs_up" | "thumbs_down"
    session_id: str


class DecisionBody(BaseModel):
    submission_id: str
    decision: str        # Approve | Refer | Decline | Request Info | Override
    reason: Optional[str] = None


class SubjectivityBody(BaseModel):
    item: str
    status: str          # Open | Received | Waived
    note: Optional[str] = None


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


@app.get("/api/submissions/{sub_id}/pricing")
def pricing(sub_id: str):
    return data.pricing_for(sub_id)


@app.get("/api/submissions/{sub_id}/account-intel")
def account_intel(sub_id: str):
    return data.account_intel_for(sub_id)


@app.get("/api/submissions/{sub_id}/loss-dev")
def loss_dev(sub_id: str):
    return data.loss_dev_for(sub_id)


@app.get("/api/submissions/{sub_id}/vehicles")
def vehicles(sub_id: str):
    return {"vehicles": data.vehicles_for(sub_id)}


@app.get("/api/submissions/{sub_id}/policy")
def policy(sub_id: str):
    return data.policy_for(sub_id)


@app.get("/api/submissions/{sub_id}/referrals")
def referrals(sub_id: str):
    return {"referrals": data.referrals_for(sub_id)}


@app.get("/api/submissions/{sub_id}/subjectivities")
def subjectivities(sub_id: str):
    return data.subjectivities_for(sub_id)


@app.post("/api/submissions/{sub_id}/subjectivities")
def clear_subjectivity(sub_id: str, body: SubjectivityBody, request: Request):
    ident = identity(request)
    ok = data.record_subjectivity(sub_id, body.item, body.status,
                                  ident["email"] or ident["name"], body.note)
    return {"ok": ok, "item": body.item, "status": body.status}


@app.get("/api/submissions/{sub_id}/quote-letter")
def quote_letter(sub_id: str):
    dat = data.quote_letter_data(sub_id)
    if not dat:
        return JSONResponse({"error": "not found"}, status_code=404)
    fname = f"Quote_{sub_id}.pdf"
    try:
        pdf = _quote_pdf(dat)
        return Response(content=pdf, media_type="application/pdf",
                        headers={"Content-Disposition": f'inline; filename="{fname}"'})
    except Exception:
        # reportlab unavailable — return a print-ready HTML letter (Save as PDF works).
        return HTMLResponse(content=_quote_html(dat))


def _quote_pdf(d: Dict[str, Any]) -> bytes:
    from io import BytesIO
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                    TableStyle, ListFlowable, ListItem)

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER, leftMargin=0.9 * inch,
                            rightMargin=0.9 * inch, topMargin=0.9 * inch, bottomMargin=0.8 * inch)
    ss = getSampleStyleSheet()
    brand = colors.HexColor("#FF3621")
    h = ParagraphStyle("h", parent=ss["Title"], fontSize=18, textColor=brand, spaceAfter=2, alignment=0)
    sub = ParagraphStyle("sub", parent=ss["Normal"], fontSize=9, textColor=colors.grey, leading=13)
    body = ParagraphStyle("body", parent=ss["Normal"], fontSize=10.5, leading=15)

    story = [
        Paragraph(d["company"], h),
        Paragraph("Commercial Automobile — Quote / Indication Letter", sub),
        Spacer(1, 16),
        Paragraph(d["date"], body),
        Spacer(1, 8),
        Paragraph(f"<b>To:</b> {d['broker']}", body),
        Paragraph(f"<b>Re:</b> {d['insured']} — Submission {d['submission_id']} ({d['account_type']})", body),
        Spacer(1, 12),
        Paragraph(f"Dear {d['broker']},", body),
        Spacer(1, 6),
    ]
    intro = ("We are pleased to offer the following indication for the above-referenced "
             "risk, subject to the conditions set out below.") if d["verdict"] != "REFER" else \
            ("Thank you for the submission. The following indication is provided for "
             "discussion and remains subject to senior-underwriting referral and the "
             "conditions set out below.")
    story += [Paragraph(intro, body), Spacer(1, 12)]

    rows = [
        ["Coverage", "Commercial Automobile Liability"],
        ["Primary operation", d["operation"] + (f" · {d['commodity']}" if d["commodity"] else "")],
        ["Requested limits", d["limits"]],
        ["Quoted premium", d["quoted_premium"]],
        ["Indication basis", (f"Indicated {d['indicated_premium']} · adequacy: {d['adequacy']}"
                              if d.get("indicated_premium") else "—")],
        ["Quote valid until", d["valid_until"]],
    ]
    t = Table(rows, colWidths=[2.0 * inch, 4.1 * inch])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#5a6270")),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#e2e5ea")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story += [t, Spacer(1, 16),
              Paragraph("This quotation is expressly conditioned upon receipt and satisfactory "
                        "review of the following subjectivities prior to binding:", body),
              Spacer(1, 4)]
    items = [ListItem(Paragraph(s, body)) for s in d["subjectivities"]] or \
            [ListItem(Paragraph("Standard Atlas binding requirements.", body))]
    story += [ListFlowable(items, bulletType="bullet", leftIndent=14), Spacer(1, 16),
              Paragraph("This letter is an indication only and does not constitute a binder or "
                        "evidence of coverage. Terms are subject to the policy forms, Atlas "
                        "underwriting guidelines and applicable filings. Coverage is not in force "
                        "until confirmed in writing by Atlas.", sub),
              Spacer(1, 20),
              Paragraph("Sincerely,", body), Spacer(1, 4),
              Paragraph(f"<b>{d['underwriter']}</b>", body),
              Paragraph(f"Underwriter · {d['company']}", sub)]
    doc.build(story)
    return buf.getvalue()


def _quote_html(d: Dict[str, Any]) -> str:
    subs = "".join(f"<li>{s}</li>" for s in d["subjectivities"]) or "<li>Standard Atlas binding requirements.</li>"
    basis = (f"Indicated {d['indicated_premium']} · adequacy: {d['adequacy']}"
             if d.get("indicated_premium") else "—")
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Quote {d['submission_id']}</title>
<style>body{{font-family:Arial,Helvetica,sans-serif;color:#1b1f24;max-width:720px;margin:40px auto;padding:0 24px;line-height:1.5}}
h1{{color:#FF3621;margin:0;font-size:24px}}.sub{{color:#7a828e;font-size:12px}}
table{{border-collapse:collapse;width:100%;margin:14px 0}}td{{padding:7px 4px;border-bottom:1px solid #e2e5ea;font-size:14px;vertical-align:top}}
td.k{{color:#5a6270;width:190px}}td.v{{font-weight:700}}.fine{{color:#7a828e;font-size:12px}}
@media print{{body{{margin:0}}}}</style></head><body>
<h1>{d['company']}</h1><div class="sub">Commercial Automobile — Quote / Indication Letter</div>
<p>{d['date']}</p>
<p><b>To:</b> {d['broker']}<br><b>Re:</b> {d['insured']} — Submission {d['submission_id']} ({d['account_type']})</p>
<p>Dear {d['broker']},</p>
<p>We are pleased to offer the following indication for the above-referenced risk, subject to the conditions set out below.</p>
<table>
<tr><td class="k">Coverage</td><td class="v">Commercial Automobile Liability</td></tr>
<tr><td class="k">Primary operation</td><td class="v">{d['operation']}{(' · ' + d['commodity']) if d['commodity'] else ''}</td></tr>
<tr><td class="k">Requested limits</td><td class="v">{d['limits']}</td></tr>
<tr><td class="k">Quoted premium</td><td class="v">{d['quoted_premium']}</td></tr>
<tr><td class="k">Indication basis</td><td class="v">{basis}</td></tr>
<tr><td class="k">Quote valid until</td><td class="v">{d['valid_until']}</td></tr>
</table>
<p>This quotation is expressly conditioned upon receipt and satisfactory review of the following subjectivities prior to binding:</p>
<ul>{subs}</ul>
<p class="fine">This letter is an indication only and does not constitute a binder or evidence of coverage. Terms are subject to the policy forms, Atlas underwriting guidelines and applicable filings. Coverage is not in force until confirmed in writing by Atlas.</p>
<p>Sincerely,<br><b>{d['underwriter']}</b><br><span class="fine">Underwriter · {d['company']}</span></p>
</body></html>"""


@app.get("/api/claims")
def all_claims_route():
    return {"claims": data.all_claims()}


@app.get("/api/loss-control")
def loss_control_route():
    return {"insureds": data.loss_control_overview()}


@app.get("/api/documents")
def all_documents_route(q: str = "", category: str = ""):
    return data.search_documents(q, category)


@app.get("/api/settings")
def settings_route(request: Request):
    return {**data.settings_info(), "role": identity(request)["role"]}


@app.post("/api/chat")
def chat(body: ChatBody, request: Request):
    ident = identity(request)
    result = data.chat(body.question, body.history, ident["role"], body.session_id,
                       body.submission_id, body.submission_context or {})
    # Persist the exchange to conversation_sessions so history survives tab close / device.
    if result.get("healthy"):
        try:
            data.log_conversation(ident["email"] or ident["name"], body.session_id,
                                  body.question, result.get("answer", ""))
        except Exception:
            pass
    return result


@app.get("/api/history")
def history(request: Request):
    ident = identity(request)
    return data.conversation_history(ident["email"] or ident["name"])


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
    # Average 3-year loss ratio across the queue (normalized to %).
    lrs = []
    for s in subs:
        lr = s.get("loss_ratio")
        if lr is None:
            continue
        lrs.append(lr * 100 if lr <= 1 else lr)
    avg_lr = (sum(lrs) / len(lrs)) if lrs else 0
    high_share = (high / n * 100) if n else 0
    ref_share = (refs / n * 100) if n else 0
    # Portfolio health score (0–100): starts at 100, penalized by average loss
    # ratio and concentration of high-risk / referral accounts. Higher = healthier.
    pen_lr = 0.5 * avg_lr
    pen_high = 0.5 * high_share
    pen_ref = 0.2 * ref_share
    score = 100 - pen_lr - pen_high - pen_ref
    portfolio_score = max(0, min(100, round(score)))
    return {
        "active_queue": n,
        "new_submissions": new,
        "high_risk": high,
        "pending_referral": refs,
        "portfolio_score": portfolio_score,
        # Full decomposition so the score is never a black box.
        "portfolio_score_breakdown": {
            "base": 100,
            "formula": "100 − 0.5·avg loss ratio − 0.5·%high-risk − 0.2·%referral",
            "components": [
                {"label": "Avg 3-yr loss ratio", "value": f"{avg_lr:.0f}%", "penalty": -round(pen_lr, 1)},
                {"label": "High-risk share", "value": f"{high_share:.0f}%", "penalty": -round(pen_high, 1)},
                {"label": "Referral share", "value": f"{ref_share:.0f}%", "penalty": -round(pen_ref, 1)},
            ],
            "score": portfolio_score,
        },
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
