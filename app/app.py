"""
UW CoPilot — AI-Powered Underwriting Intelligence Platform

Enterprise underwriting workbench on Databricks Apps.
Designed for Fortune 500 commercial insurance carriers.

Architecture:
  - Header:     Global navigation, search, notifications, profile
  - KPI Bar:    Real-time queue metrics
  - Left:       Submission queue with search, filters, sort
  - Center:     Workbench with tabbed views (Overview, Documents, Claims, etc.)
  - Right:      AI companion panel (chat, similar risks, citations)

Run: streamlit run app.py
"""

import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

import streamlit as st
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

# ─── Locate the package ───────────────────────────────────────────────────────
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_repo_root, "src") not in sys.path:
    sys.path.insert(0, os.path.join(_repo_root, "src"))

from uw_copilot.config import Config  # noqa: E402
import base64 as _b64

def _load_logo_b64():
    _lp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "logo.png")
    if os.path.exists(_lp):
        with open(_lp, "rb") as _f:
            return _b64.b64encode(_f.read()).decode()
    return None

_LOGO_B64 = _load_logo_b64()
_LOGO_HTML = (
    f'<img src="data:image/png;base64,{_LOGO_B64}" style="height:36px;width:auto;max-width:130px;object-fit:contain;border-radius:8px;box-shadow:0 1px 6px rgba(0,0,0,0.35);" />'
    if _LOGO_B64 else '<div class="uw-logo-ring">🛡</div>'
)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="UW CoPilot",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# ═══════════════════════════════════════════════════════════════════════════════
# DESIGN TOKENS
# ═══════════════════════════════════════════════════════════════════════════════
class Colors:
    PRIMARY  = "#E05C0A"      # Primary blue
    ACCENT   = "#F97316"                   # Lighter orange
    SUCCESS  = "#10B981"                   # Emerald
    WARNING  = "#F59E0B"                   # Amber
    DANGER   = "#EF4444"                   # Red
    BG       = "#070F1E"                   # Main background
    SURFACE  = "#0D1B2E"                   # Panel surface
    CARD     = "#0F2035"                   # Card background
    BORDER   = "rgba(255,255,255,0.08)"    # Subtle border
    TEXT     = "#F1F5F9"                   # Primary text
    MUTED    = "#94A3B8"                   # Muted text
    SUBTLE   = "#475569"                   # Very muted


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM STYLES
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 13px;
}}
[data-testid="stHeader"] {{ display: none !important; }}
section[data-testid="stSidebar"] {{ display: none !important; }}
.stApp {{ background: {'#13171F' if st.session_state.dark_mode else '#F0F2F5'} !important; }}
.block-container {{ padding: 0 1.5rem 2rem !important; max-width: 100% !important; }}

/* ── TOPBAR — target the st.columns row that holds .tb-logo ── */
[data-testid="stHorizontalBlock"]:has(.tb-logo) {{
    background: {'#1C2130' if st.session_state.dark_mode else '#FFFFFF'} !important;
    margin: 0 -1.5rem 1.2rem !important;
    padding: 0 20px !important;
    position: sticky !important; top: 0 !important; z-index: 200 !important;
    border-bottom: 1px solid {'rgba(255,255,255,0.08)' if st.session_state.dark_mode else 'rgba(0,0,0,0.09)'} !important;
    min-height: 52px !important; align-items: center !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.2) !important;
}}
[data-testid="stHorizontalBlock"]:has(.tb-logo) [data-testid="column"] {{
    display: flex !important; align-items: center !important;
    padding-top: 0 !important; padding-bottom: 0 !important;
}}
.tb-logo {{ display:flex; align-items:center; justify-content:center; height:52px; padding:0 4px; }}
.tb-logo img {{ height:36px; width:auto; max-width:130px; object-fit:contain; border-radius:8px; box-shadow:0 1px 6px rgba(0,0,0,0.35); }}
.tb-title-block {{ text-align:center; }}
.tb-title {{ font-size:22px; font-weight:800; line-height:1; }}
.tb-subtitle {{ font-size:12px; color:#64748B; margin-top:4px; }}
.tb-center {{ display:flex; align-items:center; height:52px; }}
.tb-icon {{
    display:flex; align-items:center; justify-content:center; height:52px;
    font-size:16px; cursor:pointer; color:{'#94A3B8' if st.session_state.dark_mode else '#64748B'};
}}
.tb-user {{ display:flex; align-items:center; gap:8px; height:52px; }}
.tb-uname {{ font-size:11px; font-weight:600; }}
.tb-urole {{ font-size:9px; color:#64748B; }}
/* Theme toggle button inside the topbar columns row */
[data-testid="stHorizontalBlock"]:has(.tb-logo) .stButton > button {{
    background: transparent !important;
    border: 1px solid {'rgba(255,255,255,0.18)' if st.session_state.dark_mode else 'rgba(0,0,0,0.15)'} !important;
    color: {'#E2E8F0' if st.session_state.dark_mode else '#1E293B'} !important;
    width:30px !important; height:30px !important; min-height:30px !important;
    padding:0 !important; border-radius:8px !important; font-size:15px !important; line-height:1 !important;
}}
[data-testid="stHorizontalBlock"]:has(.tb-logo) .stButton > button:hover {{
    background: {'rgba(255,255,255,0.1)' if st.session_state.dark_mode else 'rgba(0,0,0,0.07)'} !important;
}}

/* ── KPI CARDS ── */
.kpi-card {{ background:{'#1C2130' if st.session_state.dark_mode else '#FFFFFF'}; border:1px solid {'rgba(255,255,255,0.07)' if st.session_state.dark_mode else 'rgba(0,0,0,0.08)'}; border-radius:10px; padding:14px 16px; }}
.kpi-icon-wrap {{ width:32px; height:32px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:15px; margin-bottom:8px; }}
.kpi-value {{ font-size:22px; font-weight:800; color:{'#E2E8F0' if st.session_state.dark_mode else '#1E293B'}; line-height:1; }}
.kpi-label {{ font-size:12px; color:{'#94A3B8' if st.session_state.dark_mode else '#64748B'}; margin:4px 0 5px; font-weight:500; }}
.kpi-delta {{ font-size:10px; font-weight:600; }}
.kpi-delta.up {{ color:#22C55E; }} .kpi-delta.neutral {{ color:#64748B; }} .kpi-delta.down {{ color:#EF4444; }}

/* ── SEARCH ── */
.stTextInput input {{ background:{'#1C2130' if st.session_state.dark_mode else '#FFFFFF'} !important; border:1px solid {'rgba(255,255,255,0.12)' if st.session_state.dark_mode else 'rgba(0,0,0,0.12)'} !important; color:{'#E2E8F0' if st.session_state.dark_mode else '#1E293B'} !important; caret-color:{'#E2E8F0' if st.session_state.dark_mode else '#1E293B'} !important; border-radius:8px !important; font-size:13px !important; padding:9px 14px !important; }}
.stTextInput input::placeholder {{ color:#64748B !important; opacity:1 !important; }}
.stTextInput input:focus {{ border-color:rgba(59,130,246,0.5) !important; box-shadow:0 0 0 2px rgba(59,130,246,0.12) !important; }}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {{ background:{'#1C2130' if st.session_state.dark_mode else '#E8EBF0'}; border-radius:8px; padding:3px; gap:2px; margin-bottom:14px; border:1px solid {'rgba(255,255,255,0.07)' if st.session_state.dark_mode else 'rgba(0,0,0,0.08)'}; }}
.stTabs [data-baseweb="tab"] {{ height:32px; background:transparent; border-radius:6px; color:#64748B !important; font-size:12px !important; font-weight:600 !important; padding:0 16px !important; border:none !important; }}
.stTabs [aria-selected="true"] {{ background:{'#232B3E' if st.session_state.dark_mode else '#FFFFFF'} !important; color:{'#E2E8F0' if st.session_state.dark_mode else '#1E293B'} !important; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display:none !important; }}

/* ── BUTTONS ── */
.stButton > button {{ background:{'#1C2130' if st.session_state.dark_mode else '#F1F3F5'} !important; border:1px solid {'rgba(255,255,255,0.1)' if st.session_state.dark_mode else 'rgba(0,0,0,0.1)'} !important; color:{'#E2E8F0' if st.session_state.dark_mode else '#1E293B'} !important; border-radius:6px !important; font-size:12px !important; font-weight:500 !important; padding:6px 14px !important; transition:all 0.15s !important; }}
.stButton > button:hover {{ background:{'#232B3E' if st.session_state.dark_mode else '#E2E6EA'} !important; border-color:rgba(59,130,246,0.45) !important; }}
.stButton > button[kind="primary"] {{ background:#1D4ED8 !important; border-color:#1D4ED8 !important; color:#fff !important; font-weight:600 !important; }}
.stButton > button[kind="primary"]:hover {{ background:#2563EB !important; border-color:#2563EB !important; }}

/* ── CHAT ── */
.stChatMessage {{ background:{'#1C2130' if st.session_state.dark_mode else '#FFFFFF'} !important; border-radius:8px !important; border:1px solid {'rgba(255,255,255,0.06)' if st.session_state.dark_mode else 'rgba(0,0,0,0.07)'} !important; }}
.stChatMessage p, .stChatMessage li, .stChatMessage span {{ font-size:12px !important; color:{'#E2E8F0' if st.session_state.dark_mode else '#1E293B'} !important; }}
.stChatInput textarea {{ background:{'#1C2130' if st.session_state.dark_mode else '#FFFFFF'} !important; border:1px solid {'rgba(255,255,255,0.1)' if st.session_state.dark_mode else 'rgba(0,0,0,0.12)'} !important; color:{'#E2E8F0' if st.session_state.dark_mode else '#1E293B'} !important; border-radius:8px !important; font-size:12px !important; }}
.new-chat-btn {{ background:#1D4ED8; color:#fff; font-size:10px; font-weight:600; padding:5px 12px; border-radius:6px; cursor:pointer; }}

/* ── AI REC CARD ── */
.ai-rec-card {{ background:{'#1C2130' if st.session_state.dark_mode else '#FFFFFF'}; border:1px solid rgba(59,130,246,0.2); border-radius:10px; padding:16px 18px; margin-bottom:14px; }}
.ai-rec-header {{ font-size:9px; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:1px; margin-bottom:10px; }}
.ai-rec-body {{ display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:10px; }}
.ai-rec-verdict {{ font-size:26px; font-weight:900; letter-spacing:3px; text-transform:uppercase; }}
.verdict-refer {{ color:#F59E0B; }} .verdict-approve {{ color:#22C55E; }} .verdict-decline {{ color:#EF4444; }} .verdict-review {{ color:#94A3B8; }}
.ai-conf-label {{ font-size:9px; color:#64748B; text-transform:uppercase; letter-spacing:0.5px; text-align:center; }}
.ai-conf-value {{ font-size:32px; font-weight:800; color:{'#E2E8F0' if st.session_state.dark_mode else '#1E293B'}; line-height:1; text-align:center; }}
.ai-rec-note {{ font-size:11px; color:#94A3B8; padding-top:10px; border-top:1px solid {'rgba(255,255,255,0.06)' if st.session_state.dark_mode else 'rgba(0,0,0,0.06)'}; }}

/* ── SNAPSHOT / RISK / COVERAGE ── */
.snap-table {{ width:100%; border-collapse:collapse; }}
.snap-row {{ border-bottom:1px solid {'rgba(255,255,255,0.05)' if st.session_state.dark_mode else 'rgba(0,0,0,0.05)'}; }}
.snap-label {{ color:#64748B; font-size:11px; padding:5px 0; width:45%; }}
.snap-value {{ color:{'#E2E8F0' if st.session_state.dark_mode else '#1E293B'}; font-size:11px; padding:5px 0; font-weight:500; }}
.risk-item {{ display:flex; align-items:flex-start; gap:7px; padding:5px 0; border-bottom:1px solid {'rgba(255,255,255,0.04)' if st.session_state.dark_mode else 'rgba(0,0,0,0.04)'}; font-size:11px; color:{'#CBD5E1' if st.session_state.dark_mode else '#334155'}; line-height:1.45; }}
.risk-icon {{ color:#F59E0B; flex-shrink:0; }}
.cov-row {{ display:flex; justify-content:space-between; padding:5px 0; border-bottom:1px solid {'rgba(255,255,255,0.04)' if st.session_state.dark_mode else 'rgba(0,0,0,0.04)'}; }}
.cov-label {{ font-size:11px; color:#64748B; }} .cov-value {{ font-size:11px; color:{'#E2E8F0' if st.session_state.dark_mode else '#1E293B'}; font-weight:600; }}
.missing-docs {{ background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.2); border-radius:8px; padding:10px 12px; margin-top:10px; }}
.missing-docs-title {{ font-size:10px; font-weight:700; color:#FCA5A5; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:6px; }}
.missing-doc-tag {{ display:inline-block; background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.25); border-radius:4px; padding:2px 7px; font-size:10px; color:#FCA5A5; margin:2px 3px 2px 0; }}

/* ── BADGES ── */
.badge {{ display:inline-flex; align-items:center; padding:2px 7px; border-radius:4px; font-size:9px; font-weight:700; letter-spacing:0.4px; }}
.badge-high {{ background:rgba(239,68,68,0.15); color:#FCA5A5; border:1px solid rgba(239,68,68,0.3); }}
.badge-med  {{ background:rgba(245,158,11,0.15); color:#FCD34D; border:1px solid rgba(245,158,11,0.3); }}
.badge-low  {{ background:rgba(34,197,94,0.15);  color:#86EFAC; border:1px solid rgba(34,197,94,0.3); }}
.badge-ref  {{ background:rgba(99,102,241,0.15); color:#C4B5FD; border:1px solid rgba(99,102,241,0.3); }}

/* ── STATUS ── */
.uw-status-live {{ background:rgba(34,197,94,0.15); color:#4ADE80; border:1px solid rgba(34,197,94,0.3); font-size:9px; font-weight:700; padding:3px 8px; border-radius:20px; letter-spacing:0.5px; }}
.uw-status-offline {{ background:rgba(239,68,68,0.15); color:#FCA5A5; border:1px solid rgba(239,68,68,0.3); font-size:9px; font-weight:700; padding:3px 8px; border-radius:20px; }}
.uw-avatar {{ width:28px; height:28px; border-radius:50%; background:linear-gradient(135deg,#3B82F6,#6366F1); display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:800; color:#fff; }}

/* ── MISC ── */
.section-header {{ font-size:9px !important; font-weight:700 !important; color:#64748B !important; text-transform:uppercase !important; letter-spacing:0.7px !important; margin:10px 0 6px !important; padding-bottom:4px !important; border-bottom:1px solid {'rgba(255,255,255,0.06)' if st.session_state.dark_mode else 'rgba(0,0,0,0.06)'} !important; }}
.panel-title {{ font-size:12px; font-weight:700; color:{'#E2E8F0' if st.session_state.dark_mode else '#1E293B'}; text-transform:uppercase; letter-spacing:0.5px; display:flex; align-items:center; gap:8px; margin-bottom:12px; }}
.sec-div {{ border:none; border-top:1px solid {'rgba(255,255,255,0.06)' if st.session_state.dark_mode else 'rgba(0,0,0,0.06)'}; margin:12px 0; }}
.empty {{ display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:200px; text-align:center; color:#64748B; }}
.back-bar {{ display:flex; align-items:center; gap:8px; margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid {'rgba(255,255,255,0.06)' if st.session_state.dark_mode else 'rgba(0,0,0,0.06)'}; }}
.breadcrumb-sep {{ color:#475569; font-size:11px; }} .breadcrumb-cur {{ font-size:12px; font-weight:600; color:{'#E2E8F0' if st.session_state.dark_mode else '#1E293B'}; }}
.sim-table {{ width:100%; border-collapse:collapse; font-size:11px; }}
.sim-th {{ color:#475569; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; padding:4px 0; border-bottom:1px solid {'rgba(255,255,255,0.08)' if st.session_state.dark_mode else 'rgba(0,0,0,0.08)'}; text-align:left; }}
.sim-td {{ color:{'#CBD5E1' if st.session_state.dark_mode else '#334155'}; padding:5px 4px 5px 0; border-bottom:1px solid {'rgba(255,255,255,0.04)' if st.session_state.dark_mode else 'rgba(0,0,0,0.04)'}; }}
.sim-score {{ display:inline-block; background:rgba(34,197,94,0.12); color:#22C55E; padding:1px 5px; border-radius:4px; font-size:9px; font-weight:700; }}

/* ── Queue row: HTML display + transparent overlay button ── */
[data-testid="element-container"]:has(.q-row-html) + [data-testid="element-container"] {{
    margin-top: -44px !important; position: relative !important; z-index: 10 !important;
}}
[data-testid="element-container"]:has(.q-row-html) + [data-testid="element-container"] .stButton > button {{
    background: transparent !important; border: none !important;
    height: 44px !important; width: 100% !important; min-height: 44px !important;
    cursor: pointer !important; color: transparent !important;
    border-radius: 0 !important; padding: 0 !important; box-shadow: none !important;
}}
[data-testid="element-container"]:has(.q-row-html) + [data-testid="element-container"] .stButton > button:hover {{
    background: {'rgba(59,130,246,0.08)' if st.session_state.dark_mode else 'rgba(59,130,246,0.06)'} !important;
}}









/* ══════════════════════════════════════════════════════
   TOPBAR — zero every layer of Streamlit padding/margin
   ══════════════════════════════════════════════════════ */
/* Row itself */
[data-testid="stHorizontalBlock"]:has(.tb-logo) {{
    gap: 0 !important;
    align-items: stretch !important;
    background: {'#13171F' if st.session_state.dark_mode else '#F0F2F5'};
    border-bottom: 1px solid {'rgba(255,255,255,0.07)' if st.session_state.dark_mode else 'rgba(0,0,0,0.08)'};
    padding: 0 !important;
    margin: 0 -1.5rem 1.2rem !important;
    position: sticky; top: 0; z-index: 200;
}}
/* Every column cell */
[data-testid="stHorizontalBlock"]:has(.tb-logo) > [data-testid="column"] {{
    padding: 0 !important;
    min-width: 0 !important;
}}
/* Vertical block inside column */
[data-testid="stHorizontalBlock"]:has(.tb-logo) > [data-testid="column"] > [data-testid="stVerticalBlock"] {{
    gap: 0 !important;
    padding: 0 !important;
}}
/* element-container wrappers */
[data-testid="stHorizontalBlock"]:has(.tb-logo) > [data-testid="column"] [data-testid="element-container"] {{
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
}}
/* Helper class for HTML content cells */
.tb-cell {{
    height: 52px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    cursor: default;
    white-space: nowrap;
}}

</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG & CLIENT
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def load_config() -> Config:
    config_path = os.path.join(_repo_root, "config", "company_config.yaml")
    return Config(config_path)

@st.cache_resource
def get_client() -> WorkspaceClient:
    return WorkspaceClient()

cfg = load_config()
w = get_client()


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════
DEFAULT_STATE = {
    "session_id":           str(uuid.uuid4()),
    "messages":             [],
    "selected_submission":  None,
    "selected_tab":         "Overview",
    "user_role":            "underwriter",
    "user_name":            "Sarah Chen",
    "endpoint_healthy":     True,
    "search_query":         "",
    "filter_risk":          [],
    "filter_status":        [],
    "sort_by":              "score_desc",
    "decided_today":       0,
}

for k, v in DEFAULT_STATE.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Data Loaders ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_submission_queue():
    """Load submissions from Delta table via SQL warehouse."""
    if not cfg.warehouse_id:
        return _demo_submissions()
    try:
        result = w.statement_execution.execute_statement(
            warehouse_id=cfg.warehouse_id,
            statement=f"""
                SELECT
                    s.submission_id,
                    s.company_name,
                    s.submission_date,
                    s.submission_status,
                    CASE
                        WHEN s.loss_ratio_3yr > 1
                        THEN LEAST(CAST(s.loss_ratio_3yr AS INT), 100)
                        ELSE CAST(s.loss_ratio_3yr * 100 AS INT)
                    END AS ai_score,
                    CASE
                        WHEN (s.loss_ratio_3yr > 1  AND s.loss_ratio_3yr > 75)
                          OR (s.loss_ratio_3yr <= 1 AND s.loss_ratio_3yr > 0.75) THEN 'High'
                        WHEN (s.loss_ratio_3yr > 1  AND s.loss_ratio_3yr > 55)
                          OR (s.loss_ratio_3yr <= 1 AND s.loss_ratio_3yr > 0.55) THEN 'Medium'
                        ELSE 'Low'
                    END AS risk_level,
                    s.referral_required,
                    s.fleet_size,
                    s.loss_ratio_3yr
                FROM {cfg.catalog}.{cfg.schema}.submissions s
                ORDER BY s.loss_ratio_3yr DESC NULLS LAST
                LIMIT 100
            """,
            wait_timeout="30s",
        )
        if result.status and result.status.state and result.status.state.value == "FAILED":
            return _demo_submissions()
        rows = result.result.data_array or []
        return [
            {"id": r[0], "name": r[1], "received": str(r[2]),
             "status": r[3], "score": int(r[4] or 0), "risk": r[5],
             "referral": bool(r[6]), "fleet_size": r[7], "loss_ratio": float(r[8] or 0)}
            for r in rows
        ]
    except Exception:
        return _demo_submissions()


def _demo_submissions() -> List[Dict]:
    return [
        {"id": "SUB-2026-00147", "name": "ABC Trucking Co.",       "broker": "Marsh McLennan",       "state": "TX", "lob": "Commercial Auto", "received": "2026-07-07 09:23", "status": "New",          "score": 92, "risk": "High",   "referral": True,  "priority": "Urgent", "assigned": "Sarah Chen",     "fleet_size": 47, "annual_revenue": "$12.4M", "years_in_business": 8,  "loss_ratio": 0.84, "premium": "$385,000", "coverage_limit": "$2M",   "deductible": "$25,000"},
        {"id": "SUB-2026-00146", "name": "Blue Ridge Freight LLC", "broker": "Aon Risk Solutions",   "state": "NC", "lob": "Commercial Auto", "received": "2026-07-07 08:15", "status": "New",          "score": 88, "risk": "High",   "referral": True,  "priority": "High",   "assigned": "Sarah Chen",     "fleet_size": 32, "annual_revenue": "$8.7M",  "years_in_business": 5,  "loss_ratio": 0.71, "premium": "$245,000", "coverage_limit": "$1M",   "deductible": "$15,000"},
        {"id": "SUB-2026-00145", "name": "Pacific Coast Carriers", "broker": "Willis Towers Watson", "state": "CA", "lob": "Commercial Auto", "received": "2026-07-07 07:42", "status": "In Review",    "score": 76, "risk": "Medium", "referral": False, "priority": "Normal", "assigned": "Michael Torres", "fleet_size": 28, "annual_revenue": "$6.2M",  "years_in_business": 12, "loss_ratio": 0.58, "premium": "$178,000", "coverage_limit": "$1M",   "deductible": "$10,000"},
        {"id": "SUB-2026-00144", "name": "Delta Express Freight",  "broker": "Brown & Brown",        "state": "GA", "lob": "Commercial Auto", "received": "2026-07-06 16:30", "status": "In Review",    "score": 61, "risk": "Medium", "referral": False, "priority": "Normal", "assigned": "Sarah Chen",     "fleet_size": 19, "annual_revenue": "$4.1M",  "years_in_business": 7,  "loss_ratio": 0.52, "premium": "$112,000", "coverage_limit": "$1M",   "deductible": "$10,000"},
        {"id": "SUB-2026-00143", "name": "Lone Star Logistics Grp","broker": "Gallagher",            "state": "TX", "lob": "Commercial Auto", "received": "2026-07-06 14:18", "status": "Pending Info", "score": 44, "risk": "Low",    "referral": False, "priority": "Low",    "assigned": "Jennifer Park",  "fleet_size": 12, "annual_revenue": "$2.8M",  "years_in_business": 15, "loss_ratio": 0.38, "premium": "$67,000",  "coverage_limit": "$500K", "deductible": "$5,000"},
        {"id": "SUB-2026-00142", "name": "Summit Transport Group", "broker": "HUB International",   "state": "CO", "lob": "Commercial Auto", "received": "2026-07-06 11:05", "status": "New",          "score": 38, "risk": "Low",    "referral": False, "priority": "Low",    "assigned": "Unassigned",     "fleet_size": 8,  "annual_revenue": "$1.9M",  "years_in_business": 22, "loss_ratio": 0.31, "premium": "$42,000",  "coverage_limit": "$500K", "deductible": "$5,000"},
    ]


def _demo_risk_indicators() -> List[str]:
    return [
        "High driver turnover (>40% annually)",
        "3 at-fault accidents in past 12 months",
        "Loss ratio exceeds 75% threshold",
        "Owner-operator model increases liability",
        "Routes include high-risk corridors (I-10)",
    ]


def _demo_next_steps() -> List[str]:
    return [
        "Request updated MVR reports for all drivers",
        "Verify safety program documentation",
        "Review fleet maintenance records",
        "Confirm cargo types and hazmat endorsements",
        "Discuss loss control recommendations with broker",
    ]


def _demo_similar_risks() -> List[Dict]:
    return [
        {"company": "Gulf Coast Haulers",  "fleet": 42, "premium": "$340K", "loss_ratio": "84%", "claims": 7, "outcome": "Declined", "similarity": 94},
        {"company": "Midwest Express LLC", "fleet": 38, "premium": "$298K", "loss_ratio": "71%", "claims": 4, "outcome": "Referred", "similarity": 89},
        {"company": "Eastern Freight Corp","fleet": 51, "premium": "$412K", "loss_ratio": "62%", "claims": 3, "outcome": "Approved", "similarity": 82},
    ]


def _demo_claims() -> List[Dict]:
    return [
        {"date": "2026-03-15", "type": "Collision", "amount": "$45,200",  "status": "Closed", "description": "Rear-end collision on I-35"},
        {"date": "2025-11-02", "type": "Cargo",     "amount": "$28,500",  "status": "Closed", "description": "Load shift damage during transit"},
        {"date": "2025-08-18", "type": "Liability", "amount": "$112,000", "status": "Open",   "description": "Third-party property damage claim"},
    ]


def _demo_documents() -> List[Dict]:
    return [
        {"name": "ACORD 125 Application",         "type": "Application", "status": "Received", "date": "2026-07-07"},
        {"name": "Loss Run Summary 2023-2026",    "type": "Loss Run",   "status": "Received", "date": "2026-07-07"},
        {"name": "Driver MVR Reports",            "type": "Driver Info","status": "Pending",  "date": "—"},
        {"name": "Fleet Schedule",                "type": "Vehicle",   "status": "Received", "date": "2026-07-06"},
        {"name": "Safety Program Documentation", "type": "Compliance", "status": "Pending",  "date": "—"},
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# AI CHAT
# ═══════════════════════════════════════════════════════════════════════════════
def query_copilot(question: str) -> Dict:
    """Query the RAG endpoint."""
    try:
        history = [
            ChatMessage(role=ChatMessageRole(m["role"]), content=m["content"])
            for m in st.session_state.messages[-10:]
        ] + [ChatMessage(role=ChatMessageRole.USER, content=question)]

        response = w.serving_endpoints.query(
            name=cfg.serving_endpoint,
            messages=history,
            extra_params={
                "user_role":  st.session_state.user_role,
                "session_id": st.session_state.session_id,
            },
        )
        st.session_state.endpoint_healthy = True
        return {"answer": response.choices[0].message.content}
    except Exception as e:
        st.session_state.endpoint_healthy = False
        return {"answer": f"Unable to reach the CoPilot endpoint. Please try again.\n\n_Error: {e}_"}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════
def get_risk_color(risk: str) -> str:
    return {"High": "#EF4444", "Medium": "#F59E0B", "Low": "#10B981"}.get(risk, "#475569")

def get_score_color(score: int) -> str:
    if score >= 80: return "#EF4444"
    if score >= 60: return Colors.WARNING
    return Colors.SUCCESS

def format_badge(text: str, variant: str = "pending") -> str:
    return f'<span class="badge badge-{variant}">{text}</span>'

def _risk_badge(risk: str) -> str:
    mapping = {"High": "high", "Medium": "medium", "Med": "medium", "Low": "low"}
    cls   = mapping.get(risk, "medium")
    label = "HIGH" if risk == "High" else "MED" if risk in ("Medium", "Med") else "LOW"
    return f'<span class="badge badge-{cls}">{label}</span>'

def _score_bar(score) -> str:
    s = int(score or 0)
    c = Colors.DANGER if s >= 80 else Colors.WARNING if s >= 60 else Colors.SUCCESS
    return (
        f'<div style="background:#E5E7EB;border-radius:3px;height:5px;overflow:hidden;margin-top:6px;">'
        f'<div style="background:{c};height:100%;width:{s}%;"></div></div>'
    )

def load_submission_summary(sub_id: str, sel: dict | None = None) -> dict | None:
    """
    Build an AI risk assessment dict for a submission.

    Tries a warehouse JOIN (submissions + insureds + loss_runs) first.
    Falls back to deriving the assessment directly from the queue `sel` dict
    so the panel always shows data, even when IDs are demo data.

    Returns:
        {
            "assessment":     str,         # e.g. "REFER TO SENIOR UNDERWRITER"
            "confidence":     float,        # 0–1
            "risk_indicators": List[str],
            "next_steps":     List[str],
        }
        or None if nothing is available.
    """
    if not cfg.warehouse_id:
        return _derive_summary_from_sel(sel) if sel else None
    try:
        result = w.statement_execution.execute_statement(
            warehouse_id=cfg.warehouse_id,
            statement=f"""
                SELECT
                    s.submission_id,   s.company_name,     s.submission_status,
                    s.fleet_size,      s.driver_count,     s.loss_ratio_3yr,
                    s.referral_required, s.decline_reason,
                    s.primary_operation, s.primary_commodity,
                    i.safety_rating,   i.csa_unsafe_driving, i.risk_tier,
                    i.telematics_provider, i.dashcam_coverage_pct,
                    lr.num_claims,     lr.large_losses,    lr.frequency
                FROM {cfg.catalog}.{cfg.schema}.submissions s
                JOIN {cfg.catalog}.{cfg.schema}.insureds i
                     ON s.insured_id = i.insured_id
                LEFT JOIN (
                    SELECT insured_id,
                           SUM(num_claims)   AS num_claims,
                           SUM(large_losses) AS large_losses,
                           AVG(frequency)    AS frequency
                    FROM {cfg.catalog}.{cfg.schema}.loss_runs
                    GROUP BY insured_id
                ) lr ON i.insured_id = lr.insured_id
                WHERE s.submission_id = '{sub_id}'
                LIMIT 1
            """,
            wait_timeout="30s",
        )
        if result.status and result.status.state and result.status.state.value == "FAILED":
            return _derive_summary_from_sel(sel)
        rows = result.result.data_array or []
        if not rows:
            return _derive_summary_from_sel(sel)
        cols = [c.name for c in result.manifest.schema.columns]
        row  = dict(zip(cols, rows[0]))
        return _build_assessment(row)
    except Exception:
        return _derive_summary_from_sel(sel)


def _derive_summary_from_sel(sel: dict | None) -> dict | None:
    """Derive a summary dict from the queue item data (demo or live queue row)."""
    if not sel:
        return None
    score      = int(sel.get("score") or 0)
    risk       = sel.get("risk", "Low")
    referral   = sel.get("referral", False)
    loss_ratio = float(sel.get("loss_ratio") or 0)
    if loss_ratio > 1:           # stored as percentage (e.g. 78.5) → convert to decimal
        loss_ratio = loss_ratio / 100.0
    fleet_size = int(sel.get("fleet_size") or 0)

    # Assessment label
    if referral or risk == "High":
        assessment = "REFER TO SENIOR UNDERWRITER"
    elif risk == "Medium":
        assessment = "REVIEW REQUIRED"
    else:
        assessment = "WITHIN APPETITE"

    # Confidence from score (score 0–100 → confidence 0.0–1.0)
    confidence = round(min(0.97, max(0.45, score / 100)), 2)

    # Risk indicators from available data
    indicators = []
    if loss_ratio > 0.75:
        indicators.append(f"Loss ratio {loss_ratio:.0%} exceeds 75% appetite threshold")
    if loss_ratio > 0.55 and not indicators:
        indicators.append(f"Loss ratio {loss_ratio:.0%} approaching appetite limit")
    if fleet_size >= 40:
        indicators.append(f"Large fleet ({fleet_size} units) — elevated exposure")
    if risk == "High":
        indicators.append("AI risk model flagged as High — manual review required")
    if referral:
        indicators.append("Referral triggered — senior underwriter sign-off required")

    # Next steps
    steps = []
    if loss_ratio > 0.75:
        steps.append("Request 5-year loss runs and obtain loss control report")
    if referral:
        steps.append("Escalate to senior underwriter with referral memo")
    if risk in ("High", "Medium"):
        steps.append("Verify MVR reports for all listed drivers")
        steps.append("Confirm fleet maintenance programme is documented")
    steps.append("Confirm coverage limits and deductible structure with broker")

    return {
        "assessment":      assessment,
        "confidence":      confidence,
        "risk_indicators": indicators or ["No adverse indicators at this time"],
        "next_steps":      steps[:4],
    }


def _build_assessment(row: dict) -> dict:
    """Build a rich assessment dict from a warehouse join row."""
    loss_ratio   = float(row.get("loss_ratio_3yr") or 0)
    if loss_ratio > 1:           # stored as percentage (e.g. 78.5) → convert to decimal
        loss_ratio = loss_ratio / 100.0
    safety       = str(row.get("safety_rating") or "").upper()
    csa_unsafe   = float(row.get("csa_unsafe_driving") or 0)
    risk_tier    = str(row.get("risk_tier") or "Standard")
    referral     = bool(row.get("referral_required"))
    fleet_size   = int(row.get("fleet_size") or 0)
    large_losses = int(row.get("large_losses") or 0)
    dashcam      = float(row.get("dashcam_coverage_pct") or 0)
    telematics   = row.get("telematics_provider") or ""

    # Assessment
    if referral or loss_ratio > 0.80 or csa_unsafe > 65:
        assessment = "REFER TO SENIOR UNDERWRITER"
    elif loss_ratio > 0.65 or risk_tier == "Non-standard":
        assessment = "REVIEW REQUIRED"
    elif safety in ("CONDITIONAL", "UNSATISFACTORY"):
        assessment = "REFER — SAFETY CONCERN"
    else:
        assessment = "WITHIN APPETITE"

    # Confidence
    confidence = 0.88 if loss_ratio < 0.75 and not referral else 0.72

    # Risk indicators
    indicators = []
    if loss_ratio > 0.75:
        indicators.append(f"Loss ratio {loss_ratio:.0%} exceeds 75% appetite threshold")
    if csa_unsafe > 65:
        indicators.append(f"CSA Unsafe Driving score {csa_unsafe} > 65 threshold")
    if large_losses > 1:
        indicators.append(f"{large_losses} large losses (>$100K) in loss history")
    if fleet_size >= 40:
        indicators.append(f"Large fleet ({fleet_size} units) — concentration risk")
    if safety in ("CONDITIONAL", "UNSATISFACTORY"):
        indicators.append(f"FMCSA safety rating: {safety}")
    if dashcam < 50:
        indicators.append(f"Dashcam coverage only {dashcam:.0f}% of fleet")
    if telematics:
        pass  # positive signal — not a risk
    if not indicators:
        indicators.append("No adverse indicators identified")

    # Next steps
    steps = []
    if referral:
        steps.append("Escalate to senior underwriter with referral memo")
    if loss_ratio > 0.65:
        steps.append("Request 5-year loss runs and loss control report")
    if csa_unsafe > 50:
        steps.append("Review FMCSA CSA profile and driver qualification files")
    steps.append("Verify MVR reports are on file for all drivers")
    steps.append("Confirm safety programme documentation with insured")

    return {
        "assessment":      assessment,
        "confidence":      confidence,
        "risk_indicators": indicators[:5],
        "next_steps":      steps[:4],
    }


# ─── Chat persistence + feedback helpers ──────────────────────────────────────
def _persist_message(session_id: str, role: str, content: str) -> None:
    """Write a single chat turn to conversation_sessions (best-effort)."""
    if not cfg.warehouse_id:
        return
    _esc = lambda s: str(s).replace("'", "''")
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    try:
        w.statement_execution.execute_statement(
            warehouse_id=cfg.warehouse_id,
            statement=(
                f"INSERT INTO {cfg.catalog}.{cfg.schema}.conversation_sessions "
                f"(session_id, role, content, user_id, created_at) VALUES ("
                f"'{_esc(session_id)}', '{_esc(role)}', '{_esc(content)}', "
                f"'{_esc(st.session_state.get('user_name', ''))}', "
                f"TIMESTAMP '{now}')"
            ),
            wait_timeout="10s",
        )
    except Exception:
        pass


def _record_feedback(query: str, response: str, rating: str) -> None:
    """Record a thumbs-up/down rating via FeedbackManager (best-effort)."""
    try:
        from uw_copilot.feedback import FeedbackManager
        FeedbackManager(cfg, w).record(
            user_id=st.session_state.get("user_name", ""),
            query=query,
            response=response,
            rating=rating,
            session_id=st.session_state.get("session_id") or str(__import__("uuid").uuid4()),
            user_role=st.session_state.get("user_role", "underwriter"),
        )
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# SIMILAR RISKS — live Vector Search
# ═══════════════════════════════════════════════════════════════════════════════

def _fmt_doc_name(stem: str) -> str:
    """Turn a file stem like 'Gulf_Coast_Haulers_LR_2024' into 'Gulf Coast Haulers'."""
    for suffix in (
        "_lr_", "_loss_run", "_submission", "_application", "_policy",
        "_acord", "_mvr", "_claims",
        "_2020", "_2021", "_2022", "_2023", "_2024", "_2025", "_2026",
    ):
        idx = stem.lower().find(suffix)
        if idx > 0:
            stem = stem[:idx]
            break
    return stem.replace("_", " ").replace("-", " ").title().strip()


@st.cache_data(ttl=300, show_spinner=False)
def get_similar_risks(
    sub_id: str,
    fleet_size: int,
    loss_ratio: float,
    state: str,
    lob: str,
    years: int,
) -> List[Dict]:
    """
    Query the VS index for documents similar to this submission's risk profile.
    Results are grouped by source document and ranked by best chunk score.
    Falls back to _demo_similar_risks() if VS is unreachable or returns nothing.
    """
    query = (
        f"commercial trucking fleet {fleet_size} vehicles {state} "
        f"{lob} loss ratio {min(loss_ratio, 1.0) if loss_ratio <= 1 else loss_ratio/100:.0%} {years} years in business "
        "submission loss run claims history"
    )
    # Categories likely to belong to historical submission / loss-run documents.
    # Underwriting guidelines / manuals are excluded — they won't be 'similar accounts'.
    _EXCLUDE_CATS = {
        "underwriting_manual", "risk_appetite", "endorsement",
        "regulatory", "form", "iso_form",
    }
    try:
        resp = w.vector_search_indexes.query_index(
            index_name=cfg.vs_index,
            columns=["chunk_id", "parent_id", "chunk_text", "category", "source_path"],
            query_text=query,
            num_results=20,
            query_type="HYBRID",
        )
        rows = getattr(getattr(resp, "result", None), "data_array", None) or []

        # Group best score per unique source document
        seen: Dict[str, Dict] = {}
        for row in rows:
            if len(row) < 5:
                continue
            chunk_text = row[2] or ""
            category   = (row[3] or "").strip().lower()
            source     = row[4] or ""
            score      = float(row[5]) if len(row) > 5 else 0.0

            if category in _EXCLUDE_CATS:
                continue

            fname   = source.rstrip("/").split("/")[-1] if source else ""
            doc_key = fname.rsplit(".", 1)[0] if fname else source[:60]
            if not doc_key:
                continue

            if doc_key not in seen or score > seen[doc_key]["score"]:
                seen[doc_key] = {
                    "company":    _fmt_doc_name(doc_key),
                    "source":     fname,
                    "category":   category.replace("_", " ").title(),
                    "snippet":    chunk_text[:100].strip().rstrip(".") + "\u2026" if chunk_text else "",
                    "score":      score,
                    "similarity": min(int(score * 100), 99),
                    "live":       True,
                }

        results = sorted(seen.values(), key=lambda x: -x["score"])[:3]
        return results if results else _demo_similar_risks()

    except Exception:
        return _demo_similar_risks()


# ═══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════════════════
all_subs = load_submission_queue()

# ═══════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════
_healthy    = st.session_state.endpoint_healthy
_status_cls = "uw-status-live" if _healthy else "uw-status-offline"
_status_txt = "● LIVE" if _healthy else "● OFFLINE"
_role_disp  = st.session_state.user_role.replace("_", " ").title()
_user_name  = st.session_state.get("user_name", "Sarah Chen")
_initials   = "".join(p[0].upper() for p in _user_name.split()[:2])

# ── Topbar rendered as native columns so theme toggle sits next to bell ──────
_dm_now = st.session_state.dark_mode
# Flat 7-column topbar — no sub-columns, CSS zeros every layer of padding
_tbc = st.columns([1.6, 5.5, 0.65, 0.32, 0.32, 2.2], gap="small")
_tc  = "#E2E8F0" if _dm_now else "#1E293B"

with _tbc[0]:
    st.markdown(f'<div class="tb-logo">{_LOGO_HTML}</div>', unsafe_allow_html=True)

with _tbc[1]:
    st.markdown(
        f'<div class="tb-title-block">'        f'<div class="tb-title" style="color:{_tc}">UW CoPilot</div>'        f'<div class="tb-subtitle">AI Powered Underwriting Intelligence Platform</div>'        f'</div>',
        unsafe_allow_html=True,
    )

with _tbc[2]:
    st.markdown(
        f'<div class="tb-cell" style="justify-content:flex-end;">'        f'<span class="{_status_cls}">{_status_txt}</span></div>',
        unsafe_allow_html=True,
    )

with _tbc[3]:
    st.markdown('<div class="tb-cell">🔔</div>', unsafe_allow_html=True)

with _tbc[4]:
    st.markdown('<div class="tb-cell" style="font-size:15px;font-weight:600;color:#94A3B8;">?</div>', unsafe_allow_html=True)

with _tbc[5]:
    st.markdown(
        f'<div class="tb-cell" style="gap:7px;justify-content:flex-start;padding-left:10px;border-left:1px solid rgba(255,255,255,0.12);">'        f'<div class="uw-avatar">{_initials}</div>'        f'<div><div style="font-size:11px;font-weight:600;color:{_tc};">{_user_name}</div>'        f'<div style="font-size:9px;color:#64748B;">{_role_disp}</div></div>'        f'</div>',
        unsafe_allow_html=True,
    )

# ═══════════════════════════════════════════════════════════════════════
# KPI BAR
# ═══════════════════════════════════════════════════════════════════════
_n_high = sum(1 for s in all_subs if s.get("risk") == "High")
_n_refs = sum(1 for s in all_subs if s.get("referral"))
_n_new  = sum(1 for s in all_subs if s.get("status") == "New")
_avg_sc = int(sum(s.get("score") or 0 for s in all_subs) / len(all_subs)) if all_subs else 0

_kpi_cols = st.columns(6)
_kpi_data = [
    ("📥", "Active Queue",       len(all_subs), "↑ +1 vs yesterday",    "up",      "rgba(37,99,235,0.15)"),
    ("📬", "New Submissions",    _n_new,        "↑ +1 vs yesterday",    "up",      "rgba(99,102,241,0.15)"),
    ("🚨", "High Risk Alerts",   _n_high,       "— No change",          "neutral", "rgba(239,68,68,0.15)"),
    ("🔄", "Pending Referral",   _n_refs,       "— No change",          "neutral", "rgba(139,92,246,0.15)"),
    ("⏱",  "Avg Turnaround",    "2h 14m",      "↓ −8hrs vs yesterday", "up",      "rgba(16,185,129,0.15)"),
    ("🎯", "Portfolio Score",   _avg_sc,       "↑ +5 vs yesterday",    "up",      "rgba(245,158,11,0.15)"),
]
for _kc, (_icon, _lbl, _val, _delta, _dir, _ibg) in zip(_kpi_cols, _kpi_data):
    _kc.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-icon-wrap" style="background:{_ibg}">{_icon}</div>'
        f'<div class="kpi-value">{_val}</div>'
        f'<div class="kpi-label">{_lbl}</div>'
        f'<div class="kpi-delta {_dir}">{_delta}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# THREE-PANEL LAYOUT
# ═══════════════════════════════════════════════════════════════════════
# ── Search bar just below the header ─────────────────────────────────────────
_q = st.text_input(
    "",
    placeholder="Search submissions, insureds, brokers...",
    key="queue_search",
    label_visibility="collapsed",
).strip().lower()

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# Filter all_subs by search term
if _q:
    _vis = [
        s for s in all_subs
        if _q in s.get("name",   "").lower()
        or _q in s.get("id",     "").lower()
        or _q in s.get("lob",    "").lower()
        or _q in s.get("broker", "").lower()
        or _q in s.get("state",  "").lower()
    ]
else:
    _vis = all_subs

_n_vis_refs = sum(1 for s in _vis if s.get("referral"))
_n_vis_high = sum(1 for s in _vis if s.get("risk") == "High")

# === STATE MACHINE: no selection -> Home Queue | selection -> Detail+Chat ===
_sel = st.session_state.selected_submission

if _sel is None:
    # == HOME SCREEN ==========================================================
    _hc1, _hc2 = st.columns([3, 1])
    _hc1.markdown(
        f'<div class="panel-title">Submission Queue '
        f'<span style="margin-left:8px;background:rgba(37,99,235,0.15);color:#93C5FD;'
        f'font-size:10px;font-weight:700;padding:2px 8px;border-radius:10px;'
        f'border:1px solid rgba(37,99,235,0.3);">{len(_vis)}</span></div>',
        unsafe_allow_html=True,
    )

    _ft_all, _ft_ref, _ft_high = st.tabs([
        f"All ({len(_vis)})",
        f"Referrals ({_n_vis_refs})",
        f"High Risk ({_n_vis_high})",
    ])

    def _home_grid(subs, tab_key="all"):
        """Styled HTML rows with invisible overlay button — single click on any row opens submission."""
        if not subs:
            st.markdown('<div class="empty"><div style="font-size:28px;margin-bottom:10px">📭</div>'
                        '<div style="font-size:13px;font-weight:600">No submissions match</div></div>',
                        unsafe_allow_html=True)
            return
        _dm   = st.session_state.dark_mode
        _tbg  = "#1C2130" if _dm else "#FFFFFF"
        _hbg  = "#13171F" if _dm else "#F8FAFC"
        _bdr  = "rgba(255,255,255,0.07)" if _dm else "rgba(0,0,0,0.08)"
        _tc   = "#E2E8F0" if _dm else "#1E293B"
        _sc   = "#94A3B8" if _dm else "#64748B"

        # Table header
        st.markdown(
            f'<div style="display:grid;grid-template-columns:3fr 1.5fr 80px 120px 70px 90px 110px;'
            f'gap:0;padding:6px 14px;background:{_hbg};'
            f'border:1px solid {_bdr};border-radius:8px 8px 0 0;border-bottom:2px solid {_bdr};">'
            f'<span style="font-size:9px;font-weight:700;color:{_sc};text-transform:uppercase;letter-spacing:0.6px">Company</span>'
            f'<span style="font-size:9px;font-weight:700;color:{_sc};text-transform:uppercase;letter-spacing:0.6px">LOB</span>'
            f'<span style="font-size:9px;font-weight:700;color:{_sc};text-transform:uppercase;letter-spacing:0.6px">Risk</span>'
            f'<span style="font-size:9px;font-weight:700;color:{_sc};text-transform:uppercase;letter-spacing:0.6px">Score</span>'
            f'<span style="font-size:9px;font-weight:700;color:{_sc};text-transform:uppercase;letter-spacing:0.6px">Fleet</span>'
            f'<span style="font-size:9px;font-weight:700;color:{_sc};text-transform:uppercase;letter-spacing:0.6px">Loss Ratio</span>'
            f'<span style="font-size:9px;font-weight:700;color:{_sc};text-transform:uppercase;letter-spacing:0.6px">Received</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        for _idx, _sub in enumerate(subs):
            _r    = _sub.get("risk", "Low")
            _sc_v = int(_sub.get("score") or 0)
            _rc   = "#EF4444" if _r == "High" else "#F59E0B" if _r in ("Medium","Med") else "#22C55E"
            _rl   = "HIGH" if _r == "High" else "MED" if _r in ("Medium","Med") else "LOW"
            _bc   = "badge-high" if _r == "High" else "badge-med" if _r in ("Medium","Med") else "badge-low"
            _lr   = float(_sub.get("loss_ratio") or 0)
            _lp   = f"{int(_lr*100)}%" if _lr <= 1 else f"{int(min(_lr,100))}%"
            _fs   = _sub.get("fleet_size") or "—"
            _rb   = ' <span class="badge badge-ref" style="font-size:8px;padding:1px 5px">REF</span>' if _sub.get("referral") else ""
            _last = "border-radius:0 0 8px 8px;" if _idx == len(subs)-1 else ""

            # HTML row — visible display
            st.markdown(
                f'<div class="q-row-html" style="display:grid;grid-template-columns:3fr 1.5fr 80px 120px 70px 90px 110px;'
                f'align-items:center;gap:0;padding:10px 14px;background:{_tbg};'
                f'border-left:1px solid {_bdr};border-right:1px solid {_bdr};border-bottom:1px solid {_bdr};{_last}">'
                f'<span style="font-size:13px;font-weight:600;color:{_tc}">{_sub["name"]}{_rb}</span>'
                f'<span style="font-size:11px;color:{_sc}">{_sub.get("lob","Commercial Auto")}</span>'
                f'<span class="badge {_bc}" style="font-size:9px">{_rl}</span>'
                f'<span style="display:flex;align-items:center;gap:5px">'
                f'  <div style="flex:1;height:4px;background:rgba(255,255,255,0.1);border-radius:2px;overflow:hidden">'
                f'    <div style="width:{_sc_v}%;height:100%;background:{_rc};border-radius:2px"></div>'
                f'  </div>'
                f'  <span style="font-size:11px;font-weight:700;color:{_rc};min-width:22px">{_sc_v}</span>'
                f'</span>'
                f'<span style="font-size:11px;color:{_tc}">{_fs}</span>'
                f'<span style="font-size:11px;color:{_tc}">{_lp}</span>'
                f'<span style="font-size:11px;color:{_sc}">{_sub.get("received","")}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            # Transparent overlay button — single click opens submission directly
            if st.button(" ", key=f"row_{tab_key}_{_sub['id']}", use_container_width=True):
                st.session_state.selected_submission = _sub
                st.session_state.messages = []
                st.rerun()

    with _ft_all:
        _home_grid(_vis, "all")
    with _ft_ref:
        _home_grid([s for s in _vis if s.get("referral")], "ref")
    with _ft_high:
        _home_grid([s for s in _vis if s.get("risk") == "High"], "high")

else:
    # == DETAIL VIEW: 50/50 ===================================================
    if st.button("Back to Queue", key="back_to_queue"):
        st.session_state.selected_submission = None
        st.rerun()

    st.markdown(
        f'<div class="back-bar">'
        f'<span class="breadcrumb-sep">Queue</span>'
        f'<span class="breadcrumb-sep"> > </span>'
        f'<span class="breadcrumb-cur">{_sel["name"]}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    _det_col, _chat_col = st.columns([1, 1], gap="large")

    with _det_col:
        risk   = _sel.get("risk", "Low")
        score  = int(_sel.get("score") or 0)
        rc     = "#EF4444" if risk=="High" else "#F59E0B" if risk in ("Medium","Med") else "#10B981"
        rl     = "HIGH"    if risk=="High" else "MED"    if risk in ("Medium","Med") else "LOW"
        bcl    = "badge-high" if risk=="High" else "badge-med" if risk in ("Medium","Med") else "badge-low"
        ref_b  = '<span class="badge badge-ref" style="margin-left:6px">REFER</span>' if _sel.get("referral") else ""
        summary = load_submission_summary(_sel["id"], _sel)
        verdict = str(summary.get("assessment","REVIEW REQUIRED")).upper() if summary else "REVIEW REQUIRED"
        verdict_short = ("REFER" if "REFER" in verdict else "APPROVE" if "APPROV" in verdict else "DECLINE" if "DECLIN" in verdict else "REVIEW")
        vc = "#F59E0B" if verdict_short=="REFER" else "#10B981" if verdict_short=="APPROVE" else "#EF4444" if verdict_short=="DECLINE" else "#94A3B8"

        st.markdown(
            f'<div style="margin-bottom:14px;">'
            f'<div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:4px;">'
            f'<span style="font-size:16px;font-weight:800;color:#F1F5F9;">{_sel["name"]}</span>'
            f'<div style="display:flex;gap:5px;"><span class="badge {bcl}">{rl}</span>{ref_b}</div>'
            f'</div>'
            f'<div style="font-size:10px;color:#64748B;">{_sel.get("lob","Commercial Auto")} &nbsp;|&nbsp; {_sel["id"]} &nbsp;|&nbsp; Received {_sel.get("received","")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        _t_ovw, _t_clm, _t_lrn, _t_drv, _t_doc, _t_nt = st.tabs(["Overview","Claims History","Loss Runs","Drivers","Documents","Notes"])

        with _t_ovw:
            conf = int(float(summary.get("confidence") or 0.88) * 100) if summary else 88
            vclass = {"REFER":"verdict-refer","APPROVE":"verdict-approve","DECLINE":"verdict-decline"}.get(verdict_short,"verdict-review")
            _note = "High risk indicators detected -- review required" if verdict_short in ("REFER","DECLINE") else "Submission meets standard underwriting criteria"
            st.markdown(
                f'<div class="ai-rec-card">'
                f'<div class="ai-rec-header">AI Recommendation</div>'
                f'<div class="ai-rec-body"><div class="ai-rec-verdict {vclass}">{verdict_short}</div>'
                f'<div><div class="ai-conf-label">Confidence Score</div><div class="ai-conf-value">{conf}%</div></div></div>'
                f'<div class="ai-rec-note">{_note} <span style="color:#E05C0A;font-weight:600;cursor:pointer;">See Details</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            _sv_l, _sv_r = st.columns([1, 1])
            with _sv_l:
                st.markdown('<div class="section-header">Submission Snapshot</div>', unsafe_allow_html=True)
                _lr_raw = float(_sel.get("loss_ratio") or 0)
                _lr_disp = f"{int(_lr_raw * 100)}%" if _lr_raw <= 1 else f"{int(min(_lr_raw, 100))}%"
                _snap = [
                    ("Insured Name",      _sel.get("name","---")),
                    ("Policy Type",       _sel.get("lob","Commercial Auto")),
                    ("Fleet Size",        str(_sel.get("fleet_size") or "---")),
                    ("Loss Ratio (3yr)",  _lr_disp),
                    ("Annual Revenue",    _sel.get("annual_revenue","---")),
                    ("Years in Business", str(_sel.get("years_in_business") or "---")),
                    ("State",             _sel.get("state","---")),
                    ("Premium",           _sel.get("premium","---")),
                ]
                _rows = "".join(f'<tr class="snap-row"><td class="snap-label">{k}</td><td class="snap-value">{v}</td></tr>' for k, v in _snap if v and v != "---")
                st.markdown(f'<table class="snap-table">{_rows}</table>', unsafe_allow_html=True)
            with _sv_r:
                st.markdown('<div class="section-header">Key Risk Indicators</div>', unsafe_allow_html=True)
                _inds = (summary.get("risk_indicators") or []) if summary else []
                if _inds:
                    _ihtml = "".join(f'<div class="risk-item"><span class="risk-icon">!</span><span>{i}</span></div>' for i in _inds[:5])
                    st.markdown(f'<div>{_ihtml}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="color:#64748B;font-size:11px;padding:8px 0">No risk indicators flagged</div>', unsafe_allow_html=True)
                st.markdown('<div class="section-header" style="margin-top:14px">Coverage & Limits</div>', unsafe_allow_html=True)
                _cov = [("Liability Limits", _sel.get("coverage_limit","$1,000,000")), ("Property Damage", _sel.get("property_damage","$500,000"))]
                _chtml = "".join(f'<div class="cov-row"><span class="cov-label">{k}</span><span class="cov-value">{v}</span></div>' for k, v in _cov)
                st.markdown(f'<div>{_chtml}</div>', unsafe_allow_html=True)
                _miss = _sel.get("missing_docs", [])
                if _miss:
                    _tags = "".join(f'<span class="missing-doc-tag">{d}</span>' for d in _miss)
                    st.markdown(f'<div class="missing-docs"><div class="missing-docs-title">Missing ({len(_miss)})</div><div>{_tags}</div></div>', unsafe_allow_html=True)

            st.markdown('<hr style="border:none;border-top:1px solid rgba(255,255,255,0.07);margin:14px 0 10px">', unsafe_allow_html=True)
            _da, _db, _dc = st.columns(3)
            if _da.button("Approve", key="btn_approve", use_container_width=True, type="primary"): st.session_state.decided_today += 1; st.toast("Approved")
            if _db.button("Refer",   key="btn_refer",   use_container_width=True): st.session_state.decided_today += 1; st.toast("Referred to Senior UW")
            if _dc.button("Decline", key="btn_decline", use_container_width=True): st.session_state.decided_today += 1; st.toast("Declined")
            _dd, _de, _ = st.columns(3)
            if _dd.button("Request Info", key="btn_request",  use_container_width=True): st.toast("Info requested")
            if _de.button("Override",     key="btn_override", use_container_width=True): st.toast("Override applied")

        with _t_clm:
            st.markdown('<div style="color:#64748B;font-size:12px;padding:30px;text-align:center">Claims history available via atlas.atlas_insurance_rag.claims</div>', unsafe_allow_html=True)
        with _t_lrn:
            st.markdown('<div style="color:#64748B;font-size:12px;padding:30px;text-align:center">Loss runs available via atlas.atlas_insurance_rag.loss_runs</div>', unsafe_allow_html=True)
        with _t_drv:
            st.markdown('<div style="color:#64748B;font-size:12px;padding:30px;text-align:center">Driver records available via atlas.atlas_insurance_rag.drivers</div>', unsafe_allow_html=True)
        with _t_doc:
            st.markdown('<div style="color:#64748B;font-size:12px;padding:30px;text-align:center">Documents -- connect to document store</div>', unsafe_allow_html=True)
        with _t_nt:
            st.text_area("Notes", key="sub_notes", height=150, label_visibility="collapsed", placeholder="Add underwriter notes...")

    with _chat_col:
        st.markdown(
            '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">'
            '<div style="font-size:11px;font-weight:700;color:#F1F5F9;text-transform:uppercase;letter-spacing:0.7px;">CoPilot Assistant</div>'
            '<span class="new-chat-btn">+ New Chat</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        chat_box = st.container(height=580)
        with chat_box:
            if not st.session_state.messages:
                st.markdown(
                    '<div class="empty" style="padding:40px 20px">'
                    '<div style="font-size:28px;margin-bottom:10px">\U0001f916</div>'
                    '<div style="font-size:12px;font-weight:600;color:#94A3B8;margin-bottom:6px">Ask me anything about this submission</div>'
                    '<div style="font-size:10px;color:#475569;line-height:1.6">"Summarize the loss history" | "Key risk drivers?" | "Compare to similar accounts"</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )
            else:
                for _i, _msg in enumerate(st.session_state.messages):
                    with st.chat_message(_msg["role"]):
                        st.markdown(_msg["content"])
                    if _msg["role"] == "assistant" and _i > 0:
                        _mq = st.session_state.messages[_i - 1].get("content", "")
                        _ma = _msg["content"]
                        _f1, _f2, _ = st.columns([1, 1, 6])
                        with _f1:
                            if st.button("Helpful", key=f"fb_up_{_i}"): _record_feedback(_mq, _ma, "thumbs_up"); st.toast("Thanks")
                        with _f2:
                            if st.button("Not helpful", key=f"fb_dn_{_i}"): _record_feedback(_mq, _ma, "thumbs_down"); st.toast("Noted")
        if prompt := st.chat_input("Ask about this submission..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            _persist_message(st.session_state.session_id, "user", prompt)
            with st.spinner("Analyzing..."):
                result = query_copilot(prompt)
            _answer = result["answer"]
            st.session_state.messages.append({"role": "assistant", "content": _answer})
            _persist_message(st.session_state.session_id, "assistant", _answer)
            st.rerun()

        # Similar Historical Risks
        st.markdown('<hr class="sec-div">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Similar Historical Risks</div>', unsafe_allow_html=True)
