// Section views for the Databricks-style workbench:
// Home (KPIs + CoPilot), Claims, Loss Control, Analytics, Documents, Settings.
import React, { useEffect, useMemo, useState } from "react";
import { api } from "./api.js";
import { Icon, KPI_ICONS, RiskBadge, Spinner } from "./ui.jsx";
import Chat from "./Chat.jsx";

export const KPI_META = [
  { key: "active_queue", label: "Active Queue", tag: "live" },
  { key: "new_submissions", label: "New Submissions", tag: "live" },
  { key: "high_risk", label: "High Risk Alerts", tag: "live" },
  { key: "pending_referral", label: "Pending Referral", tag: "live" },
  { key: "portfolio_score", label: "Portfolio Score", tag: "derived" },
];

const HOME_SUGGESTIONS = [
  "Which submissions need referral today?",
  "Summarize portfolio loss-ratio trends",
  "What's driving the high-risk alerts?",
  "Which accounts carry the most premium at risk?",
];

// ── small helpers ────────────────────────────────────────────────────────────
function useLoad(loader) {
  const [data, setData] = useState(null);
  useEffect(() => {
    let live = true;
    loader().then((r) => live && setData(r)).catch(() => live && setData({}));
    return () => { live = false; };
  }, []);
  return data;
}

function Table({ cols, rows, empty, onRow }) {
  if (!rows) return <Spinner label="Loading" />;
  if (rows.length === 0) return <div className="empty"><div className="big">🗂️</div>{empty}</div>;
  return (
    <table className="dtable">
      <thead><tr>{cols.map((c) => <th key={c.k} className={c.num ? "num" : ""}>{c.label}</th>)}</tr></thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i} className={onRow ? "clickable-row" : ""} onClick={onRow ? () => onRow(r) : undefined}>
            {cols.map((c) => <td key={c.k} className={c.num ? "num" : ""}>{c.render ? c.render(r) : (r[c.k] ?? "—")}</td>)}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Modal({ title, sub, onClose, children }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ width: 560, padding: 0 }} onClick={(e) => e.stopPropagation()}>
        <div style={{ padding: "20px 24px 16px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div style={{ fontWeight: 800, fontSize: 16 }}>{title}</div>
            {sub && <div style={{ fontSize: 12, color: "var(--subtle)", marginTop: 2 }}>{sub}</div>}
          </div>
          <button className="btn ghost" style={{ padding: "4px 10px", fontSize: 18, lineHeight: 1 }} onClick={onClose}>×</button>
        </div>
        <div style={{ padding: "16px 24px 20px" }}>{children}</div>
      </div>
    </div>
  );
}

function PageHead({ title, sub }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <h1 style={{ fontSize: 20, fontWeight: 800, margin: 0, letterSpacing: "-0.3px" }}>{title}</h1>
      {sub && <div style={{ fontSize: 12, color: "var(--subtle)", marginTop: 3 }}>{sub}</div>}
    </div>
  );
}

// ── HOME: KPIs + CoPilot only ─────────────────────────────────────────────────
export function HomeView({ kpis, sessionId, toast }) {
  const [showBreak, setShowBreak] = useState(false);
  const bd = kpis.portfolio_score_breakdown;
  return (
    <>
      <div className="kpi-grid">
        {KPI_META.map((k) => {
          const meta = KPI_ICONS[k.key];
          const IconC = meta.icon;
          const clickable = k.key === "portfolio_score" && bd;
          return (
            <div className={`kpi ${clickable ? "clickable-row" : ""}`} key={k.key}
                 onClick={clickable ? () => setShowBreak((v) => !v) : undefined}>
              <div className="ico" style={{ background: meta.bg, color: meta.tint }}><IconC width={18} height={18} /></div>
              <div className="val">{kpis[k.key] ?? "—"}</div>
              <div className="lbl">{k.label}{clickable && <span style={{ color: "var(--subtle)", fontWeight: 500 }}> · how?</span>}</div>
              <div className={`kpi-tag ${k.tag}`}>{k.tag === "derived" ? "live · derived" : "live · from queue"}</div>
            </div>
          );
        })}
      </div>
      {showBreak && bd && (
        <div className="panel card-pad" style={{ marginBottom: 20 }}>
          <div className="section-label">How the Portfolio Score is computed</div>
          <div className="score-line"><span>Base</span><span>{bd.base}</span></div>
          {bd.components.map((c, i) => (
            <div className="score-line" key={i}>
              <span>{c.label} ({c.value})</span><span className="pen">{c.penalty}</span>
            </div>
          ))}
          <div className="score-line" style={{ borderTop: "1px solid var(--border)", marginTop: 4, paddingTop: 6, fontWeight: 700, color: "var(--text)" }}>
            <span>Portfolio Score</span><span>{bd.score}</span>
          </div>
          <div className="score-formula">{bd.formula}</div>
        </div>
      )}
      <div className="home-copilot">
        <Chat submission={{ name: "the Atlas portfolio", id: "" }} sessionId={sessionId} toast={toast} suggestions={HOME_SUGGESTIONS} />
      </div>
    </>
  );
}

// ── CLAIMS ─────────────────────────────────────────────────────────────────────
export function ClaimsView() {
  const d = useLoad(api.allClaims);
  const rows = d?.claims;
  const [sel, setSel] = useState(null);
  const [filter, setFilter] = useState("all");
  const open = rows ? rows.filter((r) => r.status === "Open").length : 0;
  const lit = rows ? rows.filter((r) => r.litigation && r.litigation !== "None").length : 0;
  const shown = !rows
    ? rows
    : filter === "open"
    ? rows.filter((r) => r.status === "Open")
    : filter === "lit"
    ? rows.filter((r) => r.litigation && r.litigation !== "None")
    : rows;
  const toggle = (f) => setFilter((cur) => (cur === f ? "all" : f));
  return (
    <>
      <PageHead title="Claims" sub="Portfolio-wide claim inventory across all insureds. Click a claim for detail." />
      {rows && rows.length > 0 && (
        <div className="mini-stats">
          <span className={`mini-stat clickable ${filter === "all" ? "active" : ""}`} onClick={() => setFilter("all")}>{rows.length} claims</span>
          <span className={`mini-stat warn clickable ${filter === "open" ? "active" : ""}`} onClick={() => toggle("open")}>{open} open</span>
          <span className={`mini-stat danger clickable ${filter === "lit" ? "active" : ""}`} onClick={() => toggle("lit")}>{lit} in litigation</span>
        </div>
      )}
      <div className="panel card-pad">
        <Table rows={shown} onRow={setSel} empty="No claims available" cols={[
          { k: "claim_id", label: "Claim" },
          { k: "company", label: "Insured" },
          { k: "date", label: "Loss Date" },
          { k: "type", label: "Type" },
          { k: "status", label: "Status" },
          { k: "litigation", label: "Litigation" },
          { k: "incurred", label: "Incurred", num: true },
          { k: "paid", label: "Paid", num: true },
        ]} />
      </div>
      {sel && (
        <Modal title={sel.claim_id} sub={sel.company} onClose={() => setSel(null)}>
          <table className="snap"><tbody>
            <tr><td>Loss date</td><td>{sel.date}</td></tr>
            <tr><td>Type</td><td>{sel.type}</td></tr>
            <tr><td>Status</td><td>{sel.status}</td></tr>
            <tr><td>Litigation</td><td>{sel.litigation || "None"}</td></tr>
            <tr><td>Incurred</td><td>{sel.incurred}</td></tr>
            <tr><td>Paid</td><td>{sel.paid}</td></tr>
            <tr><td>Outstanding reserve</td><td>{sel.reserves || "—"}</td></tr>
          </tbody></table>
          {sel.description && (<>
            <div className="section-label" style={{ marginTop: 14 }}>Narrative</div>
            <div style={{ fontSize: 13, color: "var(--muted)", lineHeight: 1.6 }}>{sel.description}</div>
          </>)}
        </Modal>
      )}
    </>
  );
}

// ── LOSS CONTROL ────────────────────────────────────────────────────────────────
export function LossControlView() {
  const d = useLoad(api.lossControl);
  const rows = d?.insureds;
  const [sel, setSel] = useState(null);
  return (
    <>
      <PageHead title="Loss Control" sub="Fleet safety and FMCSA CSA posture by insured. Higher CSA percentiles = elevated risk. Click an insured for detail." />
      <div className="panel card-pad">
        <Table rows={rows} onRow={setSel} empty="No loss-control data available" cols={[
          { k: "company", label: "Insured" },
          { k: "state", label: "State" },
          { k: "fleet_size", label: "Fleet", num: true },
          { k: "safety_rating", label: "Safety Rating", render: (r) => (
            <span className={`badge ${r.safety_rating === "Satisfactory" ? "low" : r.safety_rating === "Conditional" ? "med" : "high"}`}>{r.safety_rating || "—"}</span>
          ) },
          { k: "csa_unsafe", label: "CSA Unsafe", num: true, render: (r) => (
            <span style={{ color: r.csa_unsafe >= 65 ? "var(--danger)" : r.csa_unsafe >= 50 ? "var(--warn)" : "var(--text)", fontWeight: r.csa_unsafe >= 50 ? 700 : 400 }}>{r.csa_unsafe ?? "—"}</span>
          ) },
          { k: "csa_maint", label: "CSA Maint.", num: true },
          { k: "dashcam_pct", label: "Dashcam %", num: true, render: (r) => (r.dashcam_pct != null ? `${Math.round(r.dashcam_pct)}%` : "—") },
          { k: "telematics", label: "Telematics" },
          { k: "risk_tier", label: "Risk Tier" },
        ]} />
      </div>
      {sel && (
        <Modal title={sel.company} sub={`${sel.state || ""} · ${sel.risk_tier || ""} risk tier`} onClose={() => setSel(null)}>
          <table className="snap"><tbody>
            <tr><td>Fleet size</td><td>{sel.fleet_size ?? "—"} power units</td></tr>
            <tr><td>Drivers</td><td>{sel.driver_count ?? "—"}</td></tr>
            <tr><td>DOT safety rating</td><td>{sel.safety_rating || "—"}</td></tr>
            <tr><td>CSA Unsafe Driving</td><td>{sel.csa_unsafe ?? "—"}</td></tr>
            <tr><td>CSA Vehicle Maintenance</td><td>{sel.csa_maint ?? "—"}</td></tr>
            <tr><td>Dashcam coverage</td><td>{sel.dashcam_pct != null ? `${Math.round(sel.dashcam_pct)}%` : "—"}</td></tr>
            <tr><td>Telematics provider</td><td>{sel.telematics || "—"}</td></tr>
          </tbody></table>
          <div className="section-label" style={{ marginTop: 14 }}>Loss-control assessment</div>
          <div style={{ fontSize: 13, color: "var(--muted)", lineHeight: 1.6 }}>
            {sel.csa_unsafe >= 65
              ? "Elevated CSA Unsafe Driving — recommend loss-control survey and driver-coaching program before renewal."
              : sel.safety_rating === "Conditional"
              ? "Conditional DOT rating — remediation plan required; monitor CSA trend closely."
              : (sel.dashcam_pct != null && sel.dashcam_pct < 80)
              ? "Dashcam adoption below 80% — recommend increasing coverage to qualify for the camera credit."
              : "Within acceptable loss-control posture; maintain telematics participation and safety program."}
          </div>
        </Modal>
      )}
    </>
  );
}

// ── ANALYTICS (computed client-side from the submission queue) ───────────────────
const parseMoney = (s) => {
  if (!s) return 0;
  const m = String(s).replace(/[$,]/g, "");
  if (m.endsWith("M")) return parseFloat(m) * 1e6;
  if (m.endsWith("K")) return parseFloat(m) * 1e3;
  return parseFloat(m) || 0;
};

function Bars({ title, data }) {
  const max = Math.max(1, ...data.map((d) => d.n));
  return (
    <div className="panel card-pad" style={{ flex: 1, minWidth: 260 }}>
      <div className="section-label">{title}</div>
      {data.map((d) => (
        <div key={d.label} className="bar-row">
          <div className="bar-label">{d.label}</div>
          <div className="bar-track"><div className="bar-fill" style={{ width: `${(d.n / max) * 100}%`, background: d.color || "var(--brand)" }} /></div>
          <div className="bar-n">{d.n}</div>
        </div>
      ))}
    </div>
  );
}

export function AnalyticsView({ subs, kpis }) {
  const stats = useMemo(() => {
    const byRisk = { High: 0, Medium: 0, Low: 0 };
    const byOp = {};
    const byStatus = {};
    let premium = 0, lrSum = 0, lrN = 0;
    (subs || []).forEach((s) => {
      byRisk[s.risk] = (byRisk[s.risk] || 0) + 1;
      const op = s.operation || s.lob || "Other"; byOp[op] = (byOp[op] || 0) + 1;
      const st = s.status || "—"; byStatus[st] = (byStatus[st] || 0) + 1;
      premium += parseMoney(s.premium);
      if (s.loss_ratio != null) { lrSum += (s.loss_ratio <= 1 ? s.loss_ratio * 100 : s.loss_ratio); lrN += 1; }
    });
    return { byRisk, byOp, byStatus, premium, avgLr: lrN ? Math.round(lrSum / lrN) : 0 };
  }, [subs]);

  const money = (n) => n >= 1e6 ? `$${(n / 1e6).toFixed(1)}M` : n >= 1e3 ? `$${Math.round(n / 1e3)}K` : `$${n}`;

  return (
    <>
      <PageHead title="Analytics" sub="Portfolio analytics computed live from the current submission queue." />
      <div className="kpi-grid" style={{ gridTemplateColumns: "repeat(4,1fr)" }}>
        <div className="kpi"><div className="val">{(subs || []).length}</div><div className="lbl">Submissions</div><div className="kpi-tag live">live</div></div>
        <div className="kpi"><div className="val">{money(stats.premium)}</div><div className="lbl">Quoted/Expiring Premium</div><div className="kpi-tag live">live</div></div>
        <div className="kpi"><div className="val">{stats.avgLr}%</div><div className="lbl">Avg 3-yr Loss Ratio</div><div className="kpi-tag live">live</div></div>
        <div className="kpi"><div className="val">{kpis?.portfolio_score ?? "—"}</div><div className="lbl">Portfolio Score</div><div className="kpi-tag derived">live · derived</div></div>
      </div>
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 4 }}>
        <Bars title="By Risk Level" data={[
          { label: "High", n: stats.byRisk.High || 0, color: "var(--danger)" },
          { label: "Medium", n: stats.byRisk.Medium || 0, color: "var(--warn)" },
          { label: "Low", n: stats.byRisk.Low || 0, color: "var(--success)" },
        ]} />
        <Bars title="By Operation" data={Object.entries(stats.byOp).map(([label, n]) => ({ label, n }))} />
        <Bars title="By Status" data={Object.entries(stats.byStatus).map(([label, n]) => ({ label, n, color: "var(--info)" }))} />
      </div>
    </>
  );
}

// ── DOCUMENTS ────────────────────────────────────────────────────────────────────
export function DocumentsView() {
  const [q, setQ] = useState("");
  const [cat, setCat] = useState("All");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const run = (query, category) => {
    setLoading(true);
    api.allDocuments(query, category === "All" ? "" : category)
      .then((r) => setData(r)).catch(() => setData({ documents: [], total: 0, categories: [] }))
      .finally(() => setLoading(false));
  };
  useEffect(() => { run("", "All"); }, []);

  const cats = ["All", ...((data?.categories) || [])];
  const rows = data?.documents;

  return (
    <>
      <PageHead title="Documents"
        sub={data?.total != null
          ? `Search the ${data.total.toLocaleString()} documents indexed in the Vector Search corpus — by name, category, or content.`
          : "Search the RAG document corpus by name, category, or content."} />

      <div className="toolbar" style={{ marginBottom: 14 }}>
        <div className="search" style={{ flex: 1 }}>
          <Icon.search width={16} height={16} />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") run(q, cat); }}
            placeholder="Search documents — e.g. “Ironhorse loss run”, “MCS-90”, “fatigue policy”…"
          />
        </div>
        <select className="doc-filter" value={cat} onChange={(e) => { setCat(e.target.value); run(q, e.target.value); }}>
          {cats.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <button className="btn primary" onClick={() => run(q, cat)}>Search</button>
      </div>

      <div className="panel card-pad">
        {loading ? <Spinner label="Searching corpus" /> : (
          <>
            <div style={{ fontSize: 12, color: "var(--subtle)", marginBottom: 10 }}>
              {rows ? `${rows.length} match${rows.length === 1 ? "" : "es"}${q ? ` for “${q}”` : ""}` : ""}
            </div>
            <Table rows={rows} empty={q ? `No documents match “${q}” — it may not be in the corpus yet.` : "No parsed documents available"} cols={[
              { k: "name", label: "Document", render: (r) => (
                <div><div style={{ fontWeight: 600 }}>{r.name}</div>
                  {r.preview && <div style={{ fontSize: 11.5, color: "var(--subtle)", marginTop: 2, maxWidth: 520, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.preview}</div>}
                </div>
              ) },
              { k: "type", label: "Category" },
              { k: "pages", label: "Pages", num: true },
              { k: "status", label: "Status", render: (r) => <span className={`badge ${r.status === "Indexed" ? "low" : "neutral"}`}>{r.status}</span> },
              { k: "date", label: "Indexed" },
            ]} />
          </>
        )}
      </div>
    </>
  );
}

// ── SETTINGS ────────────────────────────────────────────────────────────────────
export function SettingsView() {
  const d = useLoad(api.settings);
  const yn = (b) => <span className={`badge ${b ? "low" : "neutral"}`}>{b ? "Connected" : "Not configured"}</span>;
  return (
    <>
      <PageHead title="Settings" sub="Read-only configuration for this Databricks App deployment." />
      <div className="panel card-pad" style={{ maxWidth: 640 }}>
        {!d ? <Spinner label="Loading" /> : (
          <table className="snap">
            <tbody>
              <tr><td>Company</td><td>{d.company}</td></tr>
              <tr><td>Unity Catalog</td><td>{d.catalog}</td></tr>
              <tr><td>Schema</td><td>{d.schema}</td></tr>
              <tr><td>Your role</td><td>{(d.role || "underwriter").replace(/_/g, " ")}</td></tr>
              <tr><td>SQL Warehouse</td><td>{yn(d.warehouse_ready)}</td></tr>
              <tr><td>Model Serving (CoPilot)</td><td>{yn(d.serving_endpoint_configured)}</td></tr>
              <tr><td>Vector Search index</td><td>{yn(d.vector_index_configured)}</td></tr>
            </tbody>
          </table>
        )}
        <div style={{ marginTop: 14, fontSize: 12, color: "var(--subtle)" }}>
          Settings are managed in the Databricks App configuration and Unity Catalog. This screen is read-only.
        </div>
      </div>
    </>
  );
}

// ── ABOUT ───────────────────────────────────────────────────────────────────────
function RagDiagram() {
  const nodes = [
    { x: 8, t: "Question", s: "underwriter asks", tone: "muted" },
    { x: 196, t: "1 · Retrieve", s: "Vector Search", tone: "brand" },
    { x: 384, t: "2 · Augment", s: "Atlas documents", tone: "brand" },
    { x: 572, t: "3 · Generate", s: "Model Serving", tone: "brand" },
    { x: 760, t: "Cited answer", s: "with sources", tone: "success" },
  ];
  const fill = { muted: "var(--elevated)", brand: "var(--brand-soft, rgba(255,54,33,0.12))", success: "var(--success-soft)" };
  const stroke = { muted: "var(--border)", brand: "var(--brand)", success: "var(--success)" };
  const txt = { muted: "var(--text)", brand: "var(--brand)", success: "var(--success)" };
  return (
    <svg viewBox="0 0 920 150" className="diagram" role="img" aria-label="RAG pipeline">
      {nodes.slice(0, -1).map((n, i) => (
        <g key={`a${i}`}>
          <line x1={n.x + 152} y1={62} x2={nodes[i + 1].x - 6} y2={62} stroke="var(--muted)" strokeWidth="2" />
          <path d={`M ${nodes[i + 1].x - 6} 62 l -9 -5 l 0 10 z`} fill="var(--muted)" />
        </g>
      ))}
      {nodes.map((n, i) => (
        <g key={i}>
          <rect x={n.x} y={30} width="152" height="64" rx="12" fill={fill[n.tone]} stroke={stroke[n.tone]} strokeWidth="1.5" />
          <text x={n.x + 76} y={60} textAnchor="middle" fontSize="15" fontWeight="800" fill={txt[n.tone]}>{n.t}</text>
          <text x={n.x + 76} y={79} textAnchor="middle" fontSize="11.5" fill="var(--muted)">{n.s}</text>
        </g>
      ))}
      <text x={460} y={128} textAnchor="middle" fontSize="12" fill="var(--subtle)">Grounded in Atlas's own documents — never the open internet. If the docs don't answer it, the CoPilot says so.</text>
    </svg>
  );
}

function ArchDiagram() {
  const svc = [
    { x: 40, t: "SQL Warehouse", s: "Delta tables — submissions, claims, drivers, units, loss runs" },
    { x: 350, t: "Vector Search", s: "1,500 documents indexed for retrieval" },
    { x: 660, t: "Model Serving", s: "RAG agent — grounded, cited answers" },
  ];
  return (
    <svg viewBox="0 0 940 336" className="diagram" role="img" aria-label="Architecture">
      {/* Unity Catalog governance container */}
      <rect x="6" y="150" width="928" height="180" rx="16" fill="none" stroke="var(--brand)" strokeWidth="1.5" strokeDasharray="6 5" opacity="0.7" />
      <text x="24" y="174" fontSize="12.5" fontWeight="800" fill="var(--brand)">UNITY CATALOG · governance · lineage · access control</text>

      {/* User */}
      <rect x="360" y="14" width="220" height="46" rx="12" fill="var(--elevated)" stroke="var(--border)" strokeWidth="1.5" />
      <text x="470" y="36" textAnchor="middle" fontSize="14" fontWeight="800" fill="var(--text)">Underwriter</text>
      <text x="470" y="52" textAnchor="middle" fontSize="11" fill="var(--muted)">Databricks SSO · role from Unity Catalog</text>

      {/* App */}
      <line x1="470" y1="60" x2="470" y2="78" stroke="var(--muted)" strokeWidth="2" />
      <path d="M 470 84 l -5 -9 l 10 0 z" fill="var(--muted)" />
      <rect x="300" y="84" width="340" height="50" rx="12" fill="var(--brand-soft, rgba(255,54,33,0.12))" stroke="var(--brand)" strokeWidth="1.6" />
      <text x="470" y="106" textAnchor="middle" fontSize="14" fontWeight="800" fill="var(--brand)">UW CoPilot — Databricks App</text>
      <text x="470" y="123" textAnchor="middle" fontSize="11" fill="var(--muted)">React workbench + FastAPI</text>

      {/* Services */}
      {svc.map((n, i) => (
        <g key={i}>
          <line x1="470" y1="134" x2={n.x + 120} y2="196" stroke="var(--muted)" strokeWidth="1.6" opacity="0.7" />
          <rect x={n.x} y="196" width="240" height="66" rx="12" fill="var(--surface)" stroke="var(--border)" strokeWidth="1.5" />
          <text x={n.x + 120} y="223" textAnchor="middle" fontSize="13.5" fontWeight="800" fill="var(--text)">{n.t}</text>
          <text x={n.x + 120} y="242" textAnchor="middle" fontSize="10.8" fill="var(--muted)">{n.s.length > 42 ? n.s.slice(0, 42) : n.s}</text>
        </g>
      ))}

      {/* Audit strip */}
      <rect x="40" y="284" width="860" height="34" rx="9" fill="var(--elevated)" stroke="var(--border)" strokeWidth="1.2" />
      <text x="470" y="305" textAnchor="middle" fontSize="12" fontWeight="700" fill="var(--muted)">Audit log — every underwriting decision &amp; AI override recorded</text>
    </svg>
  );
}

export function AboutView() {
  const stats = [
    ["1,500+", "documents indexed"],
    ["16", "Delta tables"],
    ["9", "workbench sections"],
    ["100%", "on the Lakehouse"],
  ];
  const rag = [
    { n: "1 · Retrieve", d: "Search Atlas's own library for the passages most relevant to the question — by meaning, not just keywords (Vector Search)." },
    { n: "2 · Augment", d: "Hand those exact passages to the AI as its source material for this question." },
    { n: "3 · Generate", d: "The AI answers grounded in those passages and cites the document and page — or says it doesn't know." },
  ];
  const features = [
    ["Home", "Portfolio KPIs and a decision-support CoPilot, plus a Portfolio Score that decomposes into its drivers."],
    ["Submissions", "The working queue — AI score, risk, loss ratio, owner, New/Renewal, and SLA aging."],
    ["Submission workbench", "Explainable AI recommendation with rule citations, Pricing & rate adequacy, Authority & FMCSA safety, Claims, Loss Development, Drivers, Units, Subjectivity clearing, and a grounded CoPilot."],
    ["Claims / Loss Control", "Portfolio-wide claim inventory and fleet-safety / CSA posture, each with drill-in detail."],
    ["Analytics", "Live book breakdowns by risk, operation, and premium at risk."],
    ["Documents", "Full-text search across the 1,500-document RAG corpus — confirm whether a document is indexed."],
    ["Quote letter", "One-click broker-ready PDF built from the recommended terms and subjectivities."],
    ["Governance", "Every decision and override written to an audit table; identity & access from Databricks SSO + Unity Catalog."],
  ];
  return (
    <>
      {/* Hero */}
      <div className="about-banner">
        <div className="ab-eyebrow">DATABRICKS APP · COMMERCIAL AUTO UNDERWRITING</div>
        <div className="ab-title">Atlas Underwriting CoPilot</div>
        <div className="ab-sub">A governed underwriting workbench on the Databricks Lakehouse — every submission, claim, driver, unit and 1,500+ documents in one place, with an AI assistant that explains its reasoning and cites its sources.</div>
        <div className="ab-stats">
          {stats.map(([n, l]) => (<div className="ab-stat" key={l}><div className="abs-n">{n}</div><div className="abs-l">{l}</div></div>))}
        </div>
      </div>

      {/* RAG */}
      <div className="section-label" style={{ marginTop: 26 }}>What is RAG — in plain language</div>
      <div className="panel card-pad">
        <p style={{ marginTop: 0 }}>A normal chatbot (a raw ChatGPT) was trained on the public internet — it knows nothing about Atlas. Ask it <em>"what is Atlas's risk appetite?"</em> and it guesses. <strong>RAG — Retrieval-Augmented Generation</strong> fixes that: instead of answering from memory, we first pull the relevant pages from <em>our own</em> documents, hand them to the AI, and say <em>"answer using only these, and cite them"</em> — like handing a colleague the manual open to the right page.</p>
        <RagDiagram />
        <div className="about-steps">
          {rag.map((s) => (<div className="about-step" key={s.n}><div className="as-n">{s.n}</div><div className="as-d">{s.d}</div></div>))}
        </div>
      </div>

      {/* Architecture */}
      <div className="section-label" style={{ marginTop: 24 }}>Architecture — all on the Lakehouse</div>
      <div className="panel card-pad">
        <ArchDiagram />
        <p className="about-note">The <strong>numbers</strong> (loss ratios, reserves, driver &amp; unit schedules) live in Delta tables and show in the workbench tabs. The <strong>knowledge</strong> (appetite, rules, procedures) lives in the documents and is what the CoPilot answers from — with citations. No data leaves the platform.</p>
      </div>

      {/* Features */}
      <div className="section-label" style={{ marginTop: 24 }}>What's inside</div>
      <div className="about-grid">
        {features.map(([t, d]) => (<div className="about-card" key={t}><div className="ac-dot" /><div><div className="ac-t">{t}</div><div className="ac-d">{d}</div></div></div>))}
      </div>

      {/* Governance */}
      <div className="panel card-pad about-trust" style={{ marginTop: 20 }}>
        <div className="section-label" style={{ marginTop: 0 }}>Trust &amp; governance</div>
        <p style={{ margin: 0 }}>Answers are grounded and cited; the AI recommendation shows the Atlas rule behind every factor and never hides behind a fabricated confidence score; every underwriting decision — and every time a human overrides the AI — is written to an audit table. Nothing leaves the Lakehouse, and access is controlled by Unity Catalog.</p>
      </div>
    </>
  );
}

// ── FEEDBACK ────────────────────────────────────────────────────────────────────
export function FeedbackView({ me, toast }) {
  const [name, setName] = useState(me?.name || "");
  const [role, setRole] = useState(me?.role ? me.role.replace(/_/g, " ") : "");
  const [company, setCompany] = useState(me?.company || "");
  const [feedback, setFeedback] = useState("");
  const [anon, setAnon] = useState(false);
  const [busy, setBusy] = useState(false);
  const [list, setList] = useState(null);

  const load = () => api.appFeedbackList().then((r) => setList(r.feedback || [])).catch(() => setList([]));
  useEffect(() => { load(); }, []);

  const submit = async () => {
    if (!feedback.trim() || busy) return;
    setBusy(true);
    try {
      const r = await api.appFeedback({ name: anon ? "" : name, role, company: anon ? "" : company, feedback, anonymous: anon });
      toast(r.ok ? "Thanks — your feedback was recorded" : "Feedback captured (demo — connect a warehouse to persist)");
      setFeedback("");
      load();
    } catch { toast("Couldn't submit — please retry"); }
    finally { setBusy(false); }
  };

  return (
    <>
      <PageHead title="Feedback" sub="Tell us what's working and what to improve. You can submit anonymously." />
      <div className="panel card-pad" style={{ maxWidth: 680 }}>
        <div className="ff-grid">
          <label className="ff"><span>Name</span>
            <input value={anon ? "" : name} disabled={anon} onChange={(e) => setName(e.target.value)} placeholder={anon ? "Hidden (anonymous)" : "Your name"} /></label>
          <label className="ff"><span>Role</span>
            <input value={role} onChange={(e) => setRole(e.target.value)} placeholder="e.g. Underwriter" /></label>
          <label className="ff"><span>Company</span>
            <input value={anon ? "" : company} disabled={anon} onChange={(e) => setCompany(e.target.value)} placeholder={anon ? "Hidden (anonymous)" : "Company"} /></label>
        </div>
        <label className="ff ff-full"><span>Feedback</span>
          <textarea rows={5} value={feedback} onChange={(e) => setFeedback(e.target.value)} placeholder="What did you like? What would make this better?" /></label>
        <label className="ff-check">
          <input type="checkbox" checked={anon} onChange={(e) => setAnon(e.target.checked)} />
          Submit anonymously — your name &amp; company won't be stored
        </label>
        <div style={{ marginTop: 14 }}>
          <button className="btn primary" disabled={busy || !feedback.trim()} onClick={submit}>
            {busy ? "Submitting…" : "Submit feedback"}
          </button>
        </div>
      </div>

      <div className="section-label" style={{ marginTop: 26 }}>Recent feedback</div>
      {list === null ? <Spinner label="Loading" /> : list.length === 0 ? (
        <div className="panel card-pad"><div className="empty">No feedback yet — be the first.</div></div>
      ) : (
        <div className="fb-feed">
          {list.map((f, i) => (
            <div className="fb-card" key={i}>
              <div className="fb-top">
                <span className="fb-who">{f.name}{f.role ? ` · ${f.role}` : ""}{f.company ? ` · ${f.company}` : ""}</span>
                <span className="fb-when">{f.when}</span>
              </div>
              <div className="fb-body">{f.feedback}</div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
