import React, { useEffect, useMemo, useState } from "react";
import { api } from "./api.js";
import { Icon, KPI_ICONS, Spinner } from "./ui.jsx";
import Queue from "./Queue.jsx";
import Detail from "./Detail.jsx";

const KPI_META = [
  { key: "active_queue", label: "Active Queue", tag: "live" },
  { key: "new_submissions", label: "New Submissions", tag: "live" },
  { key: "high_risk", label: "High Risk Alerts", tag: "live" },
  { key: "pending_referral", label: "Pending Referral", tag: "live" },
  { key: "portfolio_score", label: "Portfolio Score", tag: "static" },
];

// Databricks-style left-rail navigation. "Dashboard" / "Submissions" show the
// queue; the rest are workbench sections available in the full deployment.
const NAV = [
  { key: "dashboard", label: "Dashboard", icon: Icon.grid },
  { key: "submissions", label: "Submissions", icon: Icon.inbox },
  { key: "claims", label: "Claims", icon: Icon.folder },
  { key: "loss_control", label: "Loss Control", icon: Icon.shield },
  { key: "analytics", label: "Analytics", icon: Icon.chart },
  { key: "documents", label: "Documents", icon: Icon.docs },
  { key: "settings", label: "Settings", icon: Icon.gear },
];
const QUEUE_NAV = new Set(["dashboard", "submissions"]);

const sessionId = crypto.randomUUID ? crypto.randomUUID() : String(Math.random());

export default function App() {
  const [me, setMe] = useState(null);
  const [subs, setSubs] = useState(null);
  const [kpis, setKpis] = useState({});
  const [selected, setSelected] = useState(null);
  const [nav, setNav] = useState("dashboard");
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    api.me().then(setMe).catch(() =>
      setMe({ name: "Underwriter", email: "", role: "underwriter", live_data: false, company: "Atlas Commercial Insurance" }));
    api.submissions()
      .then((r) => { setSubs(r.submissions); setKpis(r.kpis); })
      .catch(() => { setSubs([]); });
  }, []);

  const toast = (msg) => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, msg }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3600);
  };

  const initials = useMemo(() => {
    const n = me?.name || "U";
    return n.split(" ").filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join("");
  }, [me]);

  const live = me?.live_data;
  const navLabel = NAV.find((x) => x.key === nav)?.label || "Dashboard";
  const roleText = (me?.role || "underwriter").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  const goNav = (k) => { setNav(k); setSelected(null); };

  return (
    <div className="app">
      {/* ── Databricks-style left navigation rail ─────────────────────────── */}
      <aside className="rail">
        <div className="rail-brand">
          <span className="db-mark" aria-hidden />
          <span className="db-word">databricks</span>
        </div>
        <div className="rail-ws">
          <div className="ws-name">{me?.company || "Atlas Commercial Insurance"}</div>
          <div className="ws-sub">Apps workspace</div>
        </div>
        <nav className="rail-nav">
          <div className="rail-group">UW COPILOT</div>
          {NAV.map((item) => {
            const IconC = item.icon;
            return (
              <button
                key={item.key}
                className={`rail-item ${nav === item.key ? "active" : ""}`}
                onClick={() => goNav(item.key)}
              >
                <IconC width={17} height={17} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
        <div className="rail-foot">
          <span className="db-dot" /> Databricks Apps · UW CoPilot v1.0
        </div>
      </aside>

      {/* ── Content column ────────────────────────────────────────────────── */}
      <div className="content">
        <header className="topbar">
          <img className="app-logo" src="/logo.png" alt="Atlas Commercial Insurance"
               onError={(e) => { e.currentTarget.style.display = "none"; }} />
          <div className="brand-text">
            <div className="t1">UW CoPilot</div>
            <div className="t2">{me?.company || "Atlas Commercial Insurance"}</div>
          </div>
          <div className="crumbs">
            <span className="crumb-mut">Apps</span><span className="crumb-sep">/</span>
            <span className="crumb-mut">UW CoPilot</span><span className="crumb-sep">/</span>
            <span className="crumb-cur">{navLabel}</span>
          </div>
          <div className="topbar-spacer" />
          <span className={`status-pill ${live ? "status-live" : "status-demo"}`}>
            <span className="dot" />{live ? "LIVE DATA" : "DEMO DATA"}
          </span>
          <button className="iconbtn" title="Help"><Icon.help width={16} height={16} /></button>
          <div className="user-chip">
            <div className="avatar">{initials}</div>
            <div className="uinfo">
              <div className="name">{me?.name || "Underwriter"}</div>
              <div className="email">{me?.email || ""}</div>
              <div className="role">{roleText}</div>
            </div>
          </div>
        </header>

        <main className="main">
          {subs === null ? (
            <Spinner label="Loading queue" />
          ) : selected ? (
            <Detail summary={selected} sessionId={sessionId} toast={toast} onBack={() => setSelected(null)} />
          ) : QUEUE_NAV.has(nav) ? (
            <>
              <div className="kpi-grid">
                {KPI_META.map((k) => {
                  const meta = KPI_ICONS[k.key];
                  const IconC = meta.icon;
                  return (
                    <div className="kpi" key={k.key}>
                      <div className="ico" style={{ background: meta.bg, color: meta.tint }}>
                        <IconC width={18} height={18} />
                      </div>
                      <div className="val">{kpis[k.key] ?? "—"}</div>
                      <div className="lbl">{k.label}</div>
                      <div className={`kpi-tag ${k.tag}`}>
                        {k.tag === "static" ? "static value for now" : "live · from queue"}
                      </div>
                    </div>
                  );
                })}
              </div>
              <Queue subs={subs} onOpen={setSelected} />
            </>
          ) : (
            <Placeholder label={navLabel} onBack={() => goNav("dashboard")} />
          )}
        </main>
      </div>

      <div className="toast-wrap">
        {toasts.map((t) => (<div className="toast" key={t.id}>{t.msg}</div>))}
      </div>
    </div>
  );
}

function Placeholder({ label, onBack }) {
  return (
    <div className="panel card-pad">
      <div className="empty">
        <div className="big">🧭</div>
        <div style={{ fontWeight: 700, fontSize: 15 }}>{label}</div>
        <div style={{ maxWidth: 460 }}>
          This workbench section is part of the full Atlas deployment. In this demo,
          open <b>Dashboard</b> to work the live submission queue.
        </div>
        <button className="btn primary" style={{ marginTop: 8 }} onClick={onBack}>Go to Dashboard</button>
      </div>
    </div>
  );
}
