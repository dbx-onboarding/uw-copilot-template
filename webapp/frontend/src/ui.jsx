// Shared presentational helpers + a tiny inline-SVG icon set (no icon dependency).
import React from "react";

// Brand: the real logo.png if present, else the inline SVG fallback.
export function BrandLogo() {
  const [err, setErr] = React.useState(false);
  if (err) return <AtlasLogo />;
  return (
    <img className="rail-logo" src="/logo.png" alt="Atlas Commercial Insurance"
         onError={() => setErr(true)} />
  );
}

// Atlas Commercial Insurance brand mark (inline SVG — a globe/atlas emblem).
export function AtlasLogo() {
  return (
    <div className="atlas-logo">
      <svg width="34" height="34" viewBox="0 0 40 40" fill="none" aria-hidden>
        <rect width="40" height="40" rx="10" fill="var(--brand)" />
        <circle cx="20" cy="20" r="11" stroke="#fff" strokeWidth="1.6" />
        <ellipse cx="20" cy="20" rx="4.6" ry="11" stroke="#fff" strokeWidth="1.4" />
        <line x1="9" y1="20" x2="31" y2="20" stroke="#fff" strokeWidth="1.4" />
        <line x1="20" y1="9" x2="20" y2="31" stroke="#fff" strokeWidth="1.4" />
      </svg>
      <div className="atlas-word">
        <b>Atlas</b>
        <span>Commercial Insurance</span>
      </div>
    </div>
  );
}

export const RISK = {
  High: { cls: "high", label: "HIGH", color: "var(--danger)" },
  Medium: { cls: "med", label: "MED", color: "var(--warn)" },
  Med: { cls: "med", label: "MED", color: "var(--warn)" },
  Low: { cls: "low", label: "LOW", color: "var(--success)" },
};

export const scoreColor = (s) =>
  s >= 76 ? "var(--danger)" : s >= 55 ? "var(--warn)" : "var(--success)";

export function RiskBadge({ risk }) {
  const r = RISK[risk] || RISK.Low;
  return <span className={`badge ${r.cls}`}>{r.label}</span>;
}

export function ScoreBar({ score }) {
  const s = Math.max(0, Math.min(100, Number(score) || 0));
  const c = scoreColor(s);
  return (
    <div className="score-cell">
      <div className="score-track">
        <div className="score-fill" style={{ width: `${s}%`, background: c }} />
      </div>
      <span className="score-num" style={{ color: c }}>{s}</span>
    </div>
  );
}

export const pct = (v) =>
  v == null ? "—" : v <= 1 ? `${Math.floor(v * 100)}%` : `${Math.floor(Math.min(v, 100))}%`;

export function Spinner({ label }) {
  return (
    <div className="empty">
      <div className="spinner" />
      {label && <div className="dots" style={{ fontSize: 13 }}>{label}</div>}
    </div>
  );
}

// ── Icons ──────────────────────────────────────────────────────────────────
const I = (p) => ({ width: 16, height: 16, viewBox: "0 0 24 24", fill: "none",
  stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round", strokeLinejoin: "round", ...p });

export const Icon = {
  search: (p) => (<svg {...I(p)}><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></svg>),
  bell: (p) => (<svg {...I(p)}><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" /></svg>),
  help: (p) => (<svg {...I(p)}><circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" /><path d="M12 17h.01" /></svg>),
  back: (p) => (<svg {...I(p)}><path d="m15 18-6-6 6-6" /></svg>),
  chevron: (p) => (<svg {...I(p)}><path d="m9 18 6-6-6-6" /></svg>),
  send: (p) => (<svg {...I(p)}><path d="m22 2-7 20-4-9-9-4Z" /><path d="M22 2 11 13" /></svg>),
  spark: (p) => (<svg {...I(p)}><path d="M12 3v3m0 12v3M3 12h3m12 0h3M5.6 5.6l2.1 2.1m8.6 8.6 2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1" /></svg>),
  alert: (p) => (<svg {...I(p)}><path d="m21.7 18-9-16a1.5 1.5 0 0 0-2.6 0l-9 16A1.5 1.5 0 0 0 2.3 20h19.4a1.5 1.5 0 0 0 1.3-2Z" /><path d="M12 9v4" /><path d="M12 17h.01" /></svg>),
  inbox: (p) => (<svg {...I(p)}><path d="M22 12h-6l-2 3h-4l-2-3H2" /><path d="M5.5 5.5 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-6.5A2 2 0 0 0 16.8 4H7.2a2 2 0 0 0-1.7 1.5Z" /></svg>),
  mail: (p) => (<svg {...I(p)}><rect width="20" height="16" x="2" y="4" rx="2" /><path d="m2 7 10 6 10-6" /></svg>),
  refer: (p) => (<svg {...I(p)}><path d="M8 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-3" /><path d="M16 3h5v5" /><path d="M21 3 10 14" /></svg>),
  target: (p) => (<svg {...I(p)}><circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="6" /><circle cx="12" cy="12" r="2" /></svg>),
  robot: (p) => (<svg {...I(p)}><rect width="16" height="12" x="4" y="8" rx="2" /><path d="M12 8V4M8 2h8" /><circle cx="9" cy="14" r="1" /><circle cx="15" cy="14" r="1" /></svg>),
  grid: (p) => (<svg {...I(p)}><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /></svg>),
  docs: (p) => (<svg {...I(p)}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" /><path d="M14 2v6h6" /><path d="M8 13h8M8 17h8" /></svg>),
  shield: (p) => (<svg {...I(p)}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" /></svg>),
  chart: (p) => (<svg {...I(p)}><path d="M3 3v18h18" /><rect x="7" y="12" width="3" height="5" /><rect x="12" y="8" width="3" height="9" /><rect x="17" y="5" width="3" height="12" /></svg>),
  folder: (p) => (<svg {...I(p)}><path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.7-.9L9.6 3.9A2 2 0 0 0 7.9 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" /></svg>),
  gear: (p) => (<svg {...I(p)}><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z" /></svg>),
  check: (p) => (<svg {...I(p)}><path d="M20 6 9 17l-5-5" /></svg>),
  atlas: (p) => (<svg {...I(p)}><circle cx="12" cy="12" r="9" /><ellipse cx="12" cy="12" rx="4" ry="9" /><path d="M3.5 9h17M3.5 15h17" /></svg>),
  dollar: (p) => (<svg {...I(p)}><path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg>),
  clock: (p) => (<svg {...I(p)}><circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" /></svg>),
};

export const KPI_ICONS = {
  active_queue: { icon: Icon.inbox, tint: "var(--info)", bg: "var(--info-soft)" },
  new_submissions: { icon: Icon.mail, tint: "#a78bfa", bg: "rgba(167,139,250,0.14)" },
  high_risk: { icon: Icon.alert, tint: "var(--danger)", bg: "var(--danger-soft)" },
  pending_referral: { icon: Icon.refer, tint: "var(--warn)", bg: "var(--warn-soft)" },
  portfolio_score: { icon: Icon.target, tint: "var(--brand)", bg: "var(--brand-soft)" },
};
