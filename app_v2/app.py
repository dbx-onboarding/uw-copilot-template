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

import os
import sys
import uuid

import pandas as pd
import streamlit as st

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
    name = (h.get("X-Forwarded-Preferred-Username") or email.split("@")[0] or "Underwriter")
    name = name.replace(".", " ").replace("_", " ").title()
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

h1, h2, h3 = st.columns([5, 2, 2])
with h1:
    st.markdown("### 🛡 UW CoPilot")
    st.caption(getattr(data.get_config(), "company_name", "Atlas Commercial Insurance") if data.get_config() else "Atlas Commercial Insurance")
with h2:
    st.markdown(
        f'<div style="text-align:right;margin-top:14px;">'
        f'<span class="badge {"b-low" if live else "b-med"}">● {"LIVE DATA" if live else "DEMO DATA"}</span></div>',
        unsafe_allow_html=True)
with h3:
    st.markdown(
        f'<div style="text-align:right;margin-top:8px;"><b>{ident["name"]}</b><br>'
        f'<span style="color:#8a94a6;font-size:12px;">{ident["role"].title()}</span></div>',
        unsafe_allow_html=True)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# KPI row (native st.metric)
# ═══════════════════════════════════════════════════════════════════════════════
n = len(subs)
k = st.columns(5)
k[0].metric("Active Queue", n)
k[1].metric("New Submissions", sum(1 for s in subs if s.get("status") == "New"))
k[2].metric("High Risk Alerts", sum(1 for s in subs if s.get("risk") == "High"))
k[3].metric("Pending Referral", sum(1 for s in subs if s.get("referral")))
k[4].metric("Portfolio Score", int(sum(s.get("score") or 0 for s in subs) / n) if n else 0)

st.write("")


# ═══════════════════════════════════════════════════════════════════════════════
# QUEUE (native dataframe with row selection — no invisible-button hack)
# ═══════════════════════════════════════════════════════════════════════════════
def show_queue():
    st.subheader("Submission Queue")
    q = st.text_input("Search", placeholder="Search company, broker, underwriter...",
                      label_visibility="collapsed")
    rows = subs
    if q:
        ql = q.lower()
        rows = [s for s in subs if any(ql in str(s.get(k, "")).lower()
                for k in ("name", "id", "broker", "underwriter", "operation"))]

    df = pd.DataFrame([{
        "Company": s["name"], "ID": s["id"], "Operation": s.get("operation") or s.get("lob"),
        "Risk": s["risk"], "AI Score": s.get("score") or 0,
        "Loss Ratio": (s.get("loss_ratio") or 0), "Fleet": s.get("fleet_size"),
        "Premium": s.get("premium"), "Status": s.get("status"), "Referral": s.get("referral"),
    } for s in rows])

    event = st.dataframe(
        df, use_container_width=True, hide_index=True,
        on_select="rerun", selection_mode="single-row",
        column_config={
            "AI Score": st.column_config.ProgressColumn("AI Score", min_value=0, max_value=100, format="%d"),
            "Loss Ratio": st.column_config.NumberColumn("Loss Ratio", format="%.0f%%"),
            "Referral": st.column_config.CheckboxColumn("Ref"),
        },
    )
    sel = event.selection.rows if hasattr(event, "selection") else []
    if sel:
        st.session_state.selected = rows[sel[0]]
        st.session_state.messages = []
        st.rerun()


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
                snap = {"Fleet Size": detail.get("fleet_size"), "Drivers": detail.get("driver_count"),
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
                    st.toast(_outcome if ok else f"{_outcome} (not persisted — no warehouse configured)")

        with tabs[1]:
            st.dataframe(pd.DataFrame(data.claims_for(detail["id"])), hide_index=True, use_container_width=True)
        with tabs[2]:
            st.dataframe(pd.DataFrame(data.loss_runs_for(detail["id"])), hide_index=True, use_container_width=True)
        with tabs[3]:
            st.dataframe(pd.DataFrame(data.drivers_for(detail["id"])), hide_index=True, use_container_width=True)
        with tabs[4]:
            st.dataframe(pd.DataFrame(data.documents_for(detail["id"])), hide_index=True, use_container_width=True)
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
