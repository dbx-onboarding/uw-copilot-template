import React, { useEffect, useMemo, useState } from "react";
import { api } from "./api.js";
import { Icon, KPI_ICONS, Spinner } from "./ui.jsx";
import Queue from "./Queue.jsx";
import Detail from "./Detail.jsx";

const KPI_META = [
  { key: "active_queue", label: "Active Queue" },
  { key: "new_submissions", label: "New Submissions" },
  { key: "high_risk", label: "High Risk Alerts" },
  { key: "pending_referral", label: "Pending Referral" },
  { key: "portfolio_score", label: "Portfolio Score" },
];

const sessionId = crypto.randomUUID ? crypto.randomUUID() : String(Math.random());

export default function App() {
  const [me, setMe] = useState(null);
  const [subs, setSubs] = useState(null);
  const [kpis, setKpis] = useState({});
  const [selected, setSelected] = useState(null);
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    api.me().then(setMe).catch(() => setMe({ name: "Underwriter", role: "underwriter", live_data: false, company: "Atlas Commercial Insurance" }));
    api.submissions()
      .then((r) => { setSubs(r.submissions); setKpis(r.kpis); })
      .catch(() => { setSubs([]); });
  }, []);

  const toast = (msg) => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, msg }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3200);
  };

  const initials = useMemo(() => {
    const n = me?.name || "U";
    return n.split(" ").filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join("");
  }, [me]);

  const live = me?.live_data;

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand-mark">🛡</div>
        <div className="brand-text">
          <div className="t1">UW CoPilot</div>
          <div className="t2">{me?.company || "Underwriting Intelligence"}</div>
        </div>
        <div className="topbar-spacer" />
        <span className={`status-pill ${live ? "status-live" : "status-demo"}`}>
          <span className="dot" />{live ? "LIVE DATA" : "DEMO DATA"}
        </span>
        <button className="iconbtn" title="Notifications"><Icon.bell width={16} height={16} /></button>
        <button className="iconbtn" title="Help"><Icon.help width={16} height={16} /></button>
        <div className="user-chip">
          <div className="avatar">{initials}</div>
          <div>
            <div className="name">{me?.name || "Underwriter"}</div>
            <div className="role">{(me?.role || "underwriter").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</div>
          </div>
        </div>
      </header>

      <main className="main">
        {subs === null ? (
          <Spinner label="Loading queue" />
        ) : selected ? (
          <Detail summary={selected} sessionId={sessionId} toast={toast} onBack={() => setSelected(null)} />
        ) : (
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
                  </div>
                );
              })}
            </div>
            <Queue subs={subs} onOpen={setSelected} />
          </>
        )}
      </main>

      <div className="toast-wrap">
        {toasts.map((t) => (<div className="toast" key={t.id}>{t.msg}</div>))}
      </div>
    </div>
  );
}
