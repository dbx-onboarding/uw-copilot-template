import React, { useEffect, useState } from "react";
import { api } from "./api.js";
import { Icon, RiskBadge, pct, Spinner } from "./ui.jsx";
import Chat from "./Chat.jsx";

const TABS = ["Overview", "Claims", "Loss Runs", "Drivers", "Documents", "Notes"];

export default function Detail({ summary, sessionId, onBack, toast }) {
  const [detail, setDetail] = useState(summary);
  const [tab, setTab] = useState("Overview");
  const [similar, setSimilar] = useState(null);
  const [notes, setNotes] = useState("");
  const [decided, setDecided] = useState(null);

  useEffect(() => {
    let live = true;
    api.submission(summary.id).then((d) => live && setDetail(d)).catch(() => {});
    api.similar(summary.id).then((r) => live && setSimilar(r.similar)).catch(() => setSimilar([]));
    return () => { live = false; };
  }, [summary.id]);

  const a = detail.assessment || {};
  const verdict = a.verdict || "REVIEW";
  const conf = Math.round((a.confidence || 0.85) * 100);

  const decide = async (decision) => {
    setDecided(decision);
    try { await api.decision({ submission_id: detail.id, decision, reason: notes || null }); } catch {}
    toast(`${decision} recorded for ${detail.name}`);
  };

  return (
    <>
      <div className="breadcrumb">
        <button className="btn ghost" style={{ padding: "6px 10px" }} onClick={onBack}>
          <Icon.back width={15} height={15} /> Queue
        </button>
        <Icon.chevron width={14} height={14} />
        <span className="cur">{detail.name}</span>
      </div>

      <div className="detail-grid">
        {/* ── LEFT: workbench ─────────────────────────────────────────── */}
        <div className="panel card-pad">
          <div className="detail-head">
            <div>
              <h1>{detail.name}</h1>
              <div className="meta">{detail.operation || detail.lob} · {detail.id} · Received {detail.received}</div>
            </div>
            <div style={{ display: "flex", gap: 6 }}>
              <RiskBadge risk={detail.risk} />
              {detail.referral && <span className="badge ref">REFER</span>}
            </div>
          </div>

          <div className="tabs" style={{ marginBottom: 16, flexWrap: "wrap", display: "flex" }}>
            {TABS.map((t) => (
              <button key={t} className={`tab ${tab === t ? "active" : ""}`} onClick={() => setTab(t)}>{t}</button>
            ))}
          </div>

          {tab === "Overview" && (
            <Overview detail={detail} a={a} verdict={verdict} conf={conf}
                      decided={decided} decide={decide} />
          )}
          {tab === "Claims" && <ClaimsTab id={detail.id} />}
          {tab === "Loss Runs" && <LossRunsTab id={detail.id} />}
          {tab === "Drivers" && <DriversTab id={detail.id} />}
          {tab === "Documents" && <DocumentsTab id={detail.id} />}
          {tab === "Notes" && (
            <textarea
              className="chat-input" style={{ width: "100%", minHeight: 180, border: "1px solid var(--border)",
                borderRadius: "var(--radius-sm)", background: "var(--surface)", color: "var(--text)",
                padding: 12, fontFamily: "var(--sans)", fontSize: 13 }}
              placeholder="Add underwriter notes..." value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          )}
        </div>

        {/* ── RIGHT: chat + similar risks ─────────────────────────────── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <Chat submission={detail} sessionId={sessionId} toast={toast} />
          <div className="panel card-pad">
            <div className="section-label">Similar Historical Risks</div>
            {similar === null ? (
              <Spinner />
            ) : similar.length === 0 ? (
              <div style={{ color: "var(--subtle)", fontSize: 13 }}>No comparable accounts found.</div>
            ) : (
              similar.map((s, i) => (
                <div className="sim-item" key={i}>
                  <div>
                    <div className="sim-name">{s.company}</div>
                    <div className="sim-cat">{s.category}{s.live ? "" : " · sample"}</div>
                  </div>
                  <span className="sim-score">{s.similarity}%</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </>
  );
}

function Overview({ detail, a, verdict, conf, decided, decide }) {
  const snap = [
    ["Insured", detail.name],
    ["Operation", detail.operation || "Commercial Auto"],
    ["Commodity", detail.commodity],
    ["Fleet Size", detail.fleet_size],
    ["Drivers", detail.driver_count],
    ["Loss Ratio (3yr)", pct(detail.loss_ratio)],
    ["Annual Revenue", detail.annual_revenue],
    ["Years in Business", detail.years_in_business],
    ["State", detail.state],
    ["Premium", detail.premium],
    ["Underwriter", detail.underwriter],
  ].filter(([, v]) => v != null && v !== "");

  return (
    <>
      <div className="ai-card">
        <div className="head"><Icon.spark width={14} height={14} /> AI Recommendation</div>
        <div className="ai-body">
          <div className={`verdict ${verdict}`}>{verdict}</div>
          <div className="conf-ring">
            <div className="num">{conf}%</div>
            <div className="cap">Confidence</div>
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 22 }}>
        <div>
          <div className="section-label">Submission Snapshot</div>
          <table className="snap">
            <tbody>
              {snap.map(([k, v]) => (<tr key={k}><td>{k}</td><td>{v}</td></tr>))}
            </tbody>
          </table>
        </div>
        <div>
          <div className="section-label">Key Risk Indicators</div>
          {(a.risk_indicators || []).map((r, i) => (
            <div className="risk-line" key={i}><Icon.alert width={15} height={15} className="mk" /><span>{r}</span></div>
          ))}
          <div className="section-label" style={{ marginTop: 18 }}>Recommended Next Steps</div>
          {(a.next_steps || []).map((s, i) => (
            <div className="step-line" key={i}><span className="n">{i + 1}</span><span>{s}</span></div>
          ))}
        </div>
      </div>

      <div className="actions-row">
        <button className="btn success" disabled={!!decided} onClick={() => decide("Approved")}>Approve</button>
        <button className="btn warn" disabled={!!decided} onClick={() => decide("Referred")}>Refer to Senior UW</button>
        <button className="btn danger" disabled={!!decided} onClick={() => decide("Declined")}>Decline</button>
        <button className="btn" onClick={() => decide("Info Requested")}>Request Info</button>
        {decided && <span style={{ marginLeft: "auto", alignSelf: "center", fontSize: 13, color: "var(--success)", fontWeight: 600 }}>✓ {decided}</span>}
      </div>
    </>
  );
}

// ── Tab data loaders ──────────────────────────────────────────────────────
function useTabData(loader, id) {
  const [data, setData] = useState(null);
  useEffect(() => {
    let live = true;
    loader(id).then((r) => live && setData(r)).catch(() => live && setData({}));
    return () => { live = false; };
  }, [id]);
  return data;
}

function DataTable({ cols, rows, empty }) {
  if (!rows) return <Spinner />;
  if (rows.length === 0) return <div className="empty"><div className="big">🗂️</div>{empty}</div>;
  return (
    <table className="dtable">
      <thead><tr>{cols.map((c) => (<th key={c.k} className={c.num ? "num" : ""}>{c.label}</th>))}</tr></thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>{cols.map((c) => (<td key={c.k} className={c.num ? "num" : ""}>{c.render ? c.render(r) : (r[c.k] ?? "—")}</td>))}</tr>
        ))}
      </tbody>
    </table>
  );
}

function ClaimsTab({ id }) {
  const d = useTabData(api.claims, id);
  return <DataTable rows={d?.claims} empty="No claims on record" cols={[
    { k: "claim_id", label: "Claim" },
    { k: "date", label: "Loss Date" },
    { k: "type", label: "Type" },
    { k: "status", label: "Status" },
    { k: "litigation", label: "Litigation" },
    { k: "incurred", label: "Incurred", num: true },
    { k: "paid", label: "Paid", num: true },
  ]} />;
}

function LossRunsTab({ id }) {
  const d = useTabData(api.lossRuns, id);
  return <DataTable rows={d?.loss_runs} empty="No loss runs on record" cols={[
    { k: "period", label: "Period" },
    { k: "claims", label: "Claims", num: true },
    { k: "large_losses", label: "Large Losses", num: true },
    { k: "incurred", label: "Incurred", num: true },
    { k: "earned_premium", label: "Earned Prem.", num: true },
    { k: "loss_ratio", label: "Loss Ratio", num: true },
  ]} />;
}

function DriversTab({ id }) {
  const d = useTabData(api.drivers, id);
  return <DataTable rows={d?.drivers} empty="No drivers on record" cols={[
    { k: "name", label: "Driver" },
    { k: "cdl_class", label: "CDL" },
    { k: "experience", label: "Yrs Exp", num: true },
    { k: "mvr_points", label: "MVR Pts", num: true, render: (r) => (
      <span style={{ color: r.mvr_points >= 5 ? "var(--danger)" : "var(--text)", fontWeight: r.mvr_points >= 5 ? 700 : 400 }}>{r.mvr_points ?? "—"}</span>
    ) },
    { k: "accidents", label: "Acc 3yr", num: true },
    { k: "status", label: "Status" },
    { k: "hazmat", label: "HazMat", render: (r) => (r.hazmat ? "Yes" : "No") },
  ]} />;
}

function DocumentsTab({ id }) {
  const d = useTabData(api.documents, id);
  return <DataTable rows={d?.documents} empty="No documents indexed" cols={[
    { k: "name", label: "Document" },
    { k: "type", label: "Category" },
    { k: "pages", label: "Pages", num: true },
    { k: "status", label: "Status", render: (r) => (
      <span className={`badge ${r.status === "Indexed" ? "low" : "neutral"}`}>{r.status}</span>
    ) },
    { k: "date", label: "Date" },
  ]} />;
}
