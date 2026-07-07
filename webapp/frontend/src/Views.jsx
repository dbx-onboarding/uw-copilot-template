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
  return (
    <>
      <div className="kpi-grid">
        {KPI_META.map((k) => {
          const meta = KPI_ICONS[k.key];
          const IconC = meta.icon;
          return (
            <div className="kpi" key={k.key}>
              <div className="ico" style={{ background: meta.bg, color: meta.tint }}><IconC width={18} height={18} /></div>
              <div className="val">{kpis[k.key] ?? "—"}</div>
              <div className="lbl">{k.label}</div>
              <div className={`kpi-tag ${k.tag}`}>{k.tag === "derived" ? "live · derived" : "live · from queue"}</div>
            </div>
          );
        })}
      </div>
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
  const open = rows ? rows.filter((r) => r.status === "Open").length : 0;
  const lit = rows ? rows.filter((r) => r.litigation && r.litigation !== "None").length : 0;
  return (
    <>
      <PageHead title="Claims" sub="Portfolio-wide claim inventory across all insureds. Click a claim for detail." />
      {rows && rows.length > 0 && (
        <div className="mini-stats">
          <span className="mini-stat">{rows.length} claims</span>
          <span className="mini-stat warn">{open} open</span>
          <span className="mini-stat danger">{lit} in litigation</span>
        </div>
      )}
      <div className="panel card-pad">
        <Table rows={rows} onRow={setSel} empty="No claims available" cols={[
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
  const d = useLoad(api.allDocuments);
  return (
    <>
      <PageHead title="Documents" sub="Parsed submission documents indexed for retrieval (Vector Search)." />
      <div className="panel card-pad">
        <Table rows={d?.documents} empty="No parsed documents available" cols={[
          { k: "name", label: "Document" },
          { k: "type", label: "Category" },
          { k: "pages", label: "Pages", num: true },
          { k: "status", label: "Status", render: (r) => <span className={`badge ${r.status === "Indexed" ? "low" : "neutral"}`}>{r.status}</span> },
          { k: "date", label: "Date" },
        ]} />
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
