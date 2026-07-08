import React, { useMemo, useState } from "react";
import { Icon, RiskBadge, ScoreBar, pct } from "./ui.jsx";

const TABS = [
  { key: "all", label: "All" },
  { key: "ref", label: "Referrals" },
  { key: "high", label: "High Risk" },
  { key: "renewals", label: "Renewals" },
  { key: "overdue", label: "Overdue" },
];

function AgingPill({ s }) {
  const cls = s.aging === "Overdue" ? "overdue" : s.aging === "Due soon" ? "due" : "ontrack";
  const label = s.aging || "—";
  const days = s.days_in_queue != null ? `${s.days_in_queue}d` : "";
  return <span className={`aging-pill ${cls}`}>{days} {label}</span>;
}

export default function Queue({ subs, onOpen }) {
  const [q, setQ] = useState("");
  const [tab, setTab] = useState("all");

  const filtered = useMemo(() => {
    const t = q.trim().toLowerCase();
    let list = subs;
    if (t) {
      list = list.filter((s) =>
        [s.name, s.id, s.broker, s.state, s.underwriter, s.operation]
          .filter(Boolean)
          .some((v) => String(v).toLowerCase().includes(t))
      );
    }
    if (tab === "ref") list = list.filter((s) => s.referral);
    if (tab === "high") list = list.filter((s) => s.risk === "High");
    if (tab === "renewals") list = list.filter((s) => s.account_type === "Renewal");
    if (tab === "overdue") list = list.filter((s) => s.aging === "Overdue" || s.aging === "Due soon");
    return list;
  }, [subs, q, tab]);

  const counts = {
    all: subs.length,
    ref: subs.filter((s) => s.referral).length,
    high: subs.filter((s) => s.risk === "High").length,
    renewals: subs.filter((s) => s.account_type === "Renewal").length,
    overdue: subs.filter((s) => s.aging === "Overdue" || s.aging === "Due soon").length,
  };

  return (
    <>
      <div className="toolbar">
        <div className="search">
          <Icon.search width={16} height={16} />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search submissions, insureds, brokers, underwriters..."
          />
        </div>
        <div className="tabs">
          {TABS.map((t) => (
            <button
              key={t.key}
              className={`tab ${tab === t.key ? "active" : ""}`}
              onClick={() => setTab(t.key)}
            >
              {t.label}<span className="n">{counts[t.key]}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="panel">
        {filtered.length === 0 ? (
          <div className="empty">
            <div className="big">📭</div>
            <div style={{ fontWeight: 600 }}>No submissions match</div>
          </div>
        ) : (
          <table className="qtable">
            <thead>
              <tr>
                <th>Company</th>
                <th>Type</th>
                <th>Risk</th>
                <th>AI Score</th>
                <th>Loss Ratio</th>
                <th>Premium</th>
                <th>Owner</th>
                <th>Aging</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s) => (
                <tr key={s.id} onClick={() => onOpen(s)}>
                  <td>
                    <div className="q-company">
                      {s.name}
                      {s.referral && <span className="badge ref" style={{ marginLeft: 8 }}>REF</span>}
                    </div>
                    <div className="q-sub">{s.id} · {s.broker || "—"}</div>
                  </td>
                  <td>{s.account_type ? <span className={`badge ${s.account_type === "Renewal" ? "renewal" : "newbiz"}`}>{s.account_type === "Renewal" ? "RENEWAL" : "NEW"}</span> : <span style={{ color: "var(--muted)" }}>{s.operation || s.lob}</span>}</td>
                  <td><RiskBadge risk={s.risk} /></td>
                  <td><ScoreBar score={s.score} /></td>
                  <td>{pct(s.loss_ratio)}</td>
                  <td style={{ fontWeight: 600 }}>{s.premium || "—"}</td>
                  <td style={{ color: "var(--muted)" }}>{s.owner || s.underwriter || "—"}</td>
                  <td>{s.aging ? <AgingPill s={s} /> : "—"}</td>
                  <td style={{ color: "var(--muted)" }}>{s.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
