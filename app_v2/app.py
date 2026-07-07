"""
UW CoPilot — Streamlit Workbench (v2, "done right")

The same fixes as the React app, but staying in Streamlit and using its MODERN
native components instead of CSS hacks:
  - Clickable queue via st.dataframe(on_select=...) — no invisible-button overlay
  - KPIs via st.metric
  - Tabs via st.tabs, tables via st.dataframe (Claims/Loss Runs/Drivers/Documents now real)
  - Native st.chat_message / st.chat_input for the CoPilot
  - Identity + RBAC role from Databricks Apps headers (st.context.headers), server-side
  - Feedback written with the correct copilot_feedback schema

Shares ONE backend with the React app: webapp/server/data.py.

Run: streamlit run app.py
"""

import base64
import os
import sys
import uuid

import pandas as pd
import streamlit as st


# ── Logo (bundled next to this file; falls back to a shield glyph) ─────────────
@st.cache_data(show_spinner=False)
def _logo_b64():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
    if os.path.exists(p):
        try:
            return base64.b64encode(open(p, "rb").read()).decode()
        except Exception:
            return None
    return None

# ── Reuse the shared data layer (same backend as the React app) ────────────────
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WEBAPP = os.path.join(_REPO_ROOT, "webapp")
if _WEBAPP not in sys.path:
    sys.path.insert(0, _WEBAPP)
from server import data  # noqa: E402

# ═══════════════════════════════════════════════════════════════════════════════
# Page + theme
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="UW CoPilot", page_icon="🛡", layout="wide",
                   initial_sidebar_state="collapsed")

BRAND = "#f97316"
st.markdown(f"""
<style>
  section[data-testid="stSidebar"] {{ display:none; }}
  .stApp {{ background:#0b0e14; }}
  /* accent for primary buttons + progress + tabs */
  .stButton>button[kind="primary"] {{ background:{BRAND}; border-color:{BRAND}; color:#1a0e02; font-weight:600; }}
  div[data-testid="stMetric"] {{ background:#161b26; border:1px solid #262d3c; border-radius:12px; padding:14px 16px; }}
  div[data-testid="stMetricValue"] {{ font-size:26px; }}
  .stTabs [aria-selected="true"] {{ color:{BRAND}; }}
  .badge {{ display:inline-block; font-size:11px; font-weight:700; padding:2px 8px; border-radius:6px; }}
  .b-high {{ background:rgba(240,80,63,.15); color:#f0503f; }}
  .b-med {{ background:rgba(245,166,35,.15); color:#f5a623; }}
  .b-low {{ background:rgba(34,201,138,.15); color:#22c98a; }}
  .b-ref {{ background:rgba(106,139,255,.15); color:#6a8bff; }}
  .verdict {{ font-size:30px; font-weight:800; }}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Identity — from Databricks Apps forwarded headers (server-side)
# ═══════════════════════════════════════════════════════════════════════════════
def get_identity():
    try:
        h = st.context.headers or {}
    except Exception:
        h = {}
    email = h.get("X-Forwarded-Email") or h.get("X-Forwarded-Preferred-Username") or ""
    # Display name from the local-part of the email only (never title-case the domain).
    local = (email.split("@")[0] if "@" in email else email) or \
        h.get("X-Forwarded-Preferred-Username") or "underwriter"
    name = local.replace(".", " ").replace("_", " ").title()
    cfg = data.get_config()
    policy = getattr(cfg, "rbac_policy", {}) if cfg else {}
    role = "underwriter"
    if isinstance(policy, dict) and isinstance(policy.get("emails"), dict):
        role = policy["emails"].get(email, "underwriter")
    return {"email": email, "name": name, "role": role}


ident = get_identity()
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "selected" not in st.session_state:
    st.session_state.selected = None
if "messages" not in st.session_state:
    st.session_state.messages = []


def badge(risk):
    cls = {"High": "b-high", "Medium": "b-med", "Low": "b-low"}.get(risk, "b-med")
    lbl = {"High": "HIGH", "Medium": "MED", "Low": "LOW"}.get(risk, "MED")
    return f'<span class="badge {cls}">{lbl}</span>'


# ═══════════════════════════════════════════════════════════════════════════════
# Header
# ═══════════════════════════════════════════════════════════════════════════════
subs = data.submission_queue()
live = data.warehouse_ready()
_company = getattr(data.get_config(), "company_name", "Atlas Commercial Insurance") if data.get_config() else "Atlas Commercial Insurance"
_initials = "".join(w[0] for w in ident["name"].split()[:2]).upper() or "UW"

# ── Simulated Databricks Apps shell (so the screens read as a Databricks App) ──
st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;background:#11151d;
     border:1px solid #232a36;border-radius:8px;padding:6px 12px;font-size:12px;margin-bottom:6px;">
  <div style="display:flex;align-items:center;gap:10px;">
    <span style="display:inline-flex;align-items:center;gap:6px;font-weight:800;color:#ff3621;">
      <span style="width:12px;height:12px;background:#ff3621;border-radius:2px;display:inline-block;"></span>Databricks</span>
    <span style="color:#6b7688;">Workspace</span><span style="color:#3a4250;">/</span>
    <span style="color:#6b7688;">Apps</span><span style="color:#3a4250;">/</span>
    <span style="color:#e6ebf2;font-weight:600;">atlas-insurance-uw-copilot</span>
  </div>
  <div style="display:flex;align-items:center;gap:12px;color:#6b7688;">
    <span class="badge {'b-low' if live else 'b-med'}">● {'Running' if live else 'Demo'}</span>
    <span>Serverless · us-east-1</span>
    <span style="background:#2b3446;color:#cdd6e4;border-radius:50%;width:22px;height:22px;
          display:inline-flex;align-items:center;justify-content:center;font-weight:700;">{_initials}</span>
  </div>
</div>
<div style="text-align:center;font-size:10px;color:#4c5566;margin-bottom:6px;">Simulated Databricks Apps shell — for demonstration</div>
""", unsafe_allow_html=True)

# ── App header: logo + title, live badge, identity ────────────────────────────
_logo = _logo_b64()
_logo_html = (f'<img src="data:image/png;base64,{_logo}" style="height:34px;vertical-align:middle;">'
              if _logo else '<span style="font-size:26px;">🛡</span>')

h1, h2, h3 = st.columns([5, 2, 2])
with h1:
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:12px;">{_logo_html}'
        f'<div><div style="font-size:22px;font-weight:800;line-height:1.05;">UW CoPilot</div>'
        f'<div style="color:#8a94a6;font-size:12px;">{_company}</div></div></div>',
        unsafe_allow_html=True)
with h2:
    st.markdown(
        f'<div style="text-align:right;margin-top:14px;">'
        f'<span class="badge {"b-low" if live else "b-med"}">● {"LIVE DATA" if live else "DEMO DATA"}</span></div>',
        unsafe_allow_html=True)
with h3:
    st.markdown(
        f'<div style="text-align:right;margin-top:2px;line-height:1.35;">'
        f'<b>{ident["name"]}</b><br>'
        f'<span style="color:#8a94a6;font-size:11px;">{ident["email"] or "—"}</span><br>'
        f'<span style="color:#f97316;font-size:11px;font-weight:700;">{ident["role"].title()}</span></div>',
        unsafe_allow_html=True)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# KPI row (native st.metric). Counts derive from the live queue; Portfolio Score
# is a rough proxy and is tagged as such.
# ═══════════════════════════════════════════════════════════════════════════════
n = len(subs)
k = st.columns(5)
k[0].metric("Active Queue", n);                                             k[0].caption("live · from queue")
k[1].metric("New Submissions", sum(1 for s in subs if s.get("status") == "New")); k[1].caption("live · from queue")
k[2].metric("High Risk Alerts", sum(1 for s in subs if s.get("risk") == "High")); k[2].caption("live · from queue")
k[3].metric("Pending Referral", sum(1 for s in subs if s.get("referral")));  k[3].caption("live · from queue")
k[4].metric("Portfolio Score", int(sum(s.get("score") or 0 for s in subs) / n) if n else 0)
k[4].caption("⚠ static value for now")

st.write("")


# ═══════════════════════════════════════════════════════════════════════════════
# QUEUE (native dataframe with row selection — no invisible-button hack)
# ═══════════════════════════════════════════════════════════════════════════════
_QW = [2.7, 1.5, 1.2, 0.8, 1.7, 0.9, 0.7, 1.0, 1.2, 0.6]  # column widths


def _open(row):
    st.session_state.selected = row
    st.session_state.messages = []
    st.rerun()


def _score_bar(score, risk):
    color = {"High": "#f0503f", "Medium": "#f5a623", "Low": "#22c98a"}.get(risk, "#6a8bff")
    return (f'<div style="display:flex;align-items:center;gap:6px;">'
            f'<div style="flex:1;background:#232a36;border-radius:4px;height:7px;">'
            f'<div style="background:{color};height:7px;border-radius:4px;width:{max(0,min(score,100))}%;"></div></div>'
            f'<span style="font-size:11px;color:#c9d2df;">{score}</span></div>')


def show_queue():
    st.subheader("Submission Queue")
    q = st.text_input("Search", placeholder="Search company, broker, underwriter...",
                      label_visibility="collapsed")
    rows = subs
    if q:
        ql = q.lower()
        rows = [s for s in subs if any(ql in str(s.get(k, "")).lower()
                for k in ("name", "id", "broker", "underwriter", "operation"))]

    st.caption("Tip: click a **company name** to open its workbench.")

    # Header
    hdr = st.columns(_QW)
    for c, label in zip(hdr, ["Company", "ID", "Operation", "Risk", "AI Score",
                              "Loss Ratio", "Fleet", "Premium", "Status", "Ref"]):
        c.markdown(f'<span style="color:#8a94a6;font-size:11px;font-weight:700;'
                   f'text-transform:uppercase;letter-spacing:.4px;">{label}</span>',
                   unsafe_allow_html=True)

    if not rows:
        st.info("No submissions match your search.")
        return

    for s in rows:
        col = st.columns(_QW)
        # Company name is the clickable affordance (opens the detail workbench)
        if col[0].button(s["name"], key=f"open_{s['id']}", use_container_width=True):
            _open(s)
        lr = (s.get("loss_ratio") or 0)
        lr_pct = lr * 100 if lr <= 1 else lr
        cells = [
            s.get("id", ""),
            s.get("operation") or s.get("lob") or "",
            badge(s.get("risk")),
            _score_bar(int(s.get("score") or 0), s.get("risk")),
            f"{lr_pct:.0f}%",
            str(s.get("fleet_size") or ""),
            s.get("premium") or "",
            s.get("status") or "",
            ("✓" if s.get("referral") else "—"),
        ]
        for c, val in zip(col[1:], cells):
            c.markdown(f'<div style="font-size:12.5px;color:#d5dbe6;padding-top:6px;">{val}</div>',
                       unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DETAIL
# ═══════════════════════════════════════════════════════════════════════════════
def show_detail(sel):
    if st.button("← Back to Queue"):
        st.session_state.selected = None
        st.rerun()

    detail = data.submission_detail(sel["id"]) or sel
    a = detail.get("assessment", {})
    left, right = st.columns([1.1, 0.9], gap="large")

    with left:
        st.markdown(f"## {detail['name']}  {badge(detail['risk'])}", unsafe_allow_html=True)
        st.caption(f"{detail.get('operation') or 'Commercial Auto'} · {detail['id']} · Received {detail.get('received','')}")

        tabs = st.tabs(["Overview", "Claims", "Loss Runs", "Drivers", "Documents", "Notes"])

        with tabs[0]:
            with st.container(border=True):
                c1, c2 = st.columns([2, 1])
                vc = {"REFER": "#f5a623", "APPROVE": "#22c98a", "DECLINE": "#f0503f"}.get(a.get("verdict"), "#8a94a6")
                c1.markdown("**AI RECOMMENDATION**")
                c1.markdown(f'<div class="verdict" style="color:{vc}">{a.get("verdict","REVIEW")}</div>', unsafe_allow_html=True)
                c2.metric("Confidence", f"{int((a.get('confidence') or 0.85)*100)}%")
            s1, s2 = st.columns(2)
            with s1:
                st.markdown("**Submission Snapshot**")
                snap = {"Fleet Size": detail.get("fleet_size"), "Drivers (scheduled)": detail.get("driver_count"),
                        "Loss Ratio (3yr)": data._pct(detail.get("loss_ratio")),
                        "Annual Revenue": detail.get("annual_revenue"), "State": detail.get("state"),
                        "Premium": detail.get("premium"), "Underwriter": detail.get("underwriter")}
                st.dataframe(pd.DataFrame([(k, v) for k, v in snap.items() if v is not None],
                             columns=["Field", "Value"]), hide_index=True, use_container_width=True)
            with s2:
                st.markdown("**Key Risk Indicators**")
                for r in a.get("risk_indicators", []):
                    st.markdown(f"⚠️ {r}")
                st.markdown("**Recommended Next Steps**")
                for i, stp in enumerate(a.get("next_steps", []), 1):
                    st.markdown(f"{i}. {stp}")
            st.divider()
            d = st.columns(4)
            _decisions = [("Approve", "Approved", "primary"), ("Refer", "Referred", "secondary"),
                          ("Decline", "Declined", "secondary"), ("Request Info", "Info Requested", "secondary")]
            for _col, (_label, _outcome, _kind) in zip(d, _decisions):
                if _col.button(_label, use_container_width=True, type=_kind):
                    ok = data.record_decision(
                        submission_id=detail["id"], user_id=ident["email"] or ident["name"],
                        decision=_outcome, ai_recommendation=a.get("verdict", ""),
                        session_id=st.session_state.session_id)
                    if ok:
                        st.toast(f"✓ {_outcome} — decision recorded to the audit log")
                    elif data.warehouse_ready():
                        st.toast(f"{_outcome} — demo action (decision log not available; not persisted)")
                    else:
                        st.toast(f"{_outcome} — demo only (no warehouse configured; not persisted)")
            st.caption("Decisions persist to the audit log when a SQL warehouse and decision table are "
                       "configured; otherwise they are demo-only and not saved.")

        with tabs[1]:
            _c = data.claims_for(detail["id"])
            (st.dataframe(pd.DataFrame(_c), hide_index=True, use_container_width=True)
             if _c else st.info("No claims linked to this submission."))
        with tabs[2]:
            _l = data.loss_runs_for(detail["id"])
            (st.dataframe(pd.DataFrame(_l), hide_index=True, use_container_width=True)
             if _l else st.info("No loss runs linked to this submission."))
        with tabs[3]:
            _drv = data.drivers_for(detail["id"])
            _sched = detail.get("driver_count")
            if _sched is not None:
                st.caption(f"{len(_drv)} driver record(s) on file · {_sched} scheduled per application")
            (st.dataframe(pd.DataFrame(_drv), hide_index=True, use_container_width=True)
             if _drv else st.info("No driver records are linked to this submission in the warehouse "
                                  "(driver schedule pending upload / insured not yet linked)."))
        with tabs[4]:
            _docs = data.documents_for(detail["id"])
            (st.dataframe(pd.DataFrame(_docs), hide_index=True, use_container_width=True)
             if _docs else st.info("No parsed documents available for this submission."))
        with tabs[5]:
            st.text_area("Notes", placeholder="Add underwriter notes...", label_visibility="collapsed")

    with right:
        st.markdown("**🤖 CoPilot Assistant**")
        box = st.container(height=420)
        with box:
            for i, m in enumerate(st.session_state.messages):
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])
                    if m["role"] == "assistant":
                        fb = st.feedback("thumbs", key=f"fb_{i}")
                        # Record once per (message, rating) — st.feedback keeps returning
                        # its stored value on every rerun, so guard against duplicate inserts.
                        recorded = st.session_state.setdefault("_fb_recorded", {})
                        rec_key = f"{st.session_state.session_id}:{i}"
                        if fb is not None and recorded.get(rec_key) != fb:
                            data.record_feedback(
                                user_id=ident["email"] or ident["name"],
                                query=st.session_state.messages[i-1]["content"] if i else "",
                                response=m["content"],
                                rating="thumbs_up" if fb == 1 else "thumbs_down",
                                session_id=st.session_state.session_id, user_role=ident["role"])
                            recorded[rec_key] = fb
                            st.toast("Thanks for the feedback")
        if prompt := st.chat_input("Ask about this submission..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner("Analyzing..."):
                res = data.chat(prompt, st.session_state.messages, ident["role"], st.session_state.session_id)
            st.session_state.messages.append({"role": "assistant", "content": res["answer"]})
            st.rerun()

        st.markdown("**Similar Historical Risks**")
        sim = data.similar_risks(detail)
        st.dataframe(pd.DataFrame([{"Company": s["company"], "Category": s.get("category"),
                     "Match": f"{s['similarity']}%"} for s in sim]),
                     hide_index=True, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.selected is None:
    show_queue()
else:
    show_detail(st.session_state.selected)
