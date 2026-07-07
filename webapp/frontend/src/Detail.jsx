import React, { useEffect, useState } from "react";
import { api } from "./api.js";
import { Icon, RiskBadge, pct, Spinner } from "./ui.jsx";
import Chat from "./Chat.jsx";

const TABS = ["Overview", "Claims", "Loss Runs", "Drivers", "Documents", "Notes"];

const ACTION_CFG = {
  Approved: {
    label: "Approve Submission",
    color: "var(--success)",
    btnClass: "success",
    icon: "✓",
    message: "Approve this submission and move it to the quoting pipeline.",
    placeholder: "Optional: Add approval conditions or coverage notes...",
    required: false,
    newStatus: "Quoted",
  },
  Referred: {
    label: "Refer to Senior UW",
    color: "var(--warn)",
    btnClass: "warn",
    icon: "↗",
    message: "Escalate this submission to senior underwriting for review.",
    placeholder: "Required: Describe the reason for referral and any specific concerns...",
    required: true,
    newStatus: "In Review",
  },
  Declined: {
    label: "Decline Submission",
    color: "var(--danger)",
    btnClass: "danger",
    icon: "✕",
    message: "Decline this submission. This action will be recorded in the audit log.",
    placeholder: "Required: Provide the reason for declining (e.g. loss ratio, commodity exclusion)...",
    required: true,
    newStatus: "Declined",
  },
  "Info Requested": {
    label: "Request Additional Info",
    color: "var(--info)",
    btnClass: "",
    icon: "?",
    message: "Request additional information from the broker before proceeding.",
    placeholder: "Required: Specify what information is needed from the broker...",
    required: true,
    newStatus: "In Review",
  },
};

export default function Detail({ summary, sessionId, onBack, toast }) {
  const [detail, setDetail] = useState(summary);
  const [tab, setTab] = useState("Overview");
  const [similar, setSimilar] = useState(null);
  const [notes, setNotes] = useState("");
  const [decided, setDecided] = useState(null);
  const [modal, setModal] = useState(null);
  const [modalReason, setModalReason] = useState("");

  useEffect(() => {
    let live = true;
    api.submission(summary.id).then((d) => live && setDetail(d)).catch(() => {});
    api.similar(summary.id).then((r) => live && setSimilar(r.similar)).catch(() => setSimilar([]));
    return () => { live = false; };
  }, [summary.id]);

  const a = detail.assessment || {};
  const verdict = a.verdict || "REVIEW";
  const conf = Math.round((a.confidence || 0.85) * 100);

  const decide = async (action, reason) => {
    setDecided(action);
    setModal(null);
    let ok = false;
    try {
      const r = await api.decision({ submission_id: detail.id, decision: action, reason: reason || null });
      ok = !!r?.ok;
      if (ok) {
        const cfg = ACTION_CFG[action];
        if (cfg?.newStatus) setDetail(d => ({ ...d, status: cfg.newStatus }));
      }
    } catch {}
    toast(ok
      ? `✓ ${action} — recorded to the audit log`
      : `${action} — demo action (not persisted; connect a warehouse to save)`);
  };

  const openModal = (action) => { setModalReason(""); setModal({ action }); };

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
                      decided={decided} decide={openModal} />
          )}
          {tab === "Claims" && <ClaimsTab id={detail.id} />}
          {tab === "Loss Runs" && <LossRunsTab id={detail.id} />}
          {tab === "Drivers" && <DriversTab id={detail.id} scheduled={detail.driver_count} />}
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
      {modal && (
        <ActionModal
          action={modal.action}
          reason={modalReason}
          setReason={setModalReason}
          onConfirm={() => decide(modal.action, modalReason)}
          onCancel={() => setModal(null)}
        />
      )}
    </>
  );
}

function Overview({ detail, a, verdict, conf, decided, decide }) {
  const snap = [
    ["Insured", detail.name],
    ["Status", detail.status],
    ["Operation", detail.operation || "Commercial Auto"],
    ["Commodity", detail.commodity],
    ["Fleet Size", detail.fleet_size],
    ["Drivers (scheduled)", detail.driver_count],
    ["Loss Ratio (3yr)", pct(detail.loss_ratio)],
    ["Annual Revenue", detail.annual_revenue],
    ["Years in Business", detail.years_in_business],
    ["State", detail.state],
    [detail.premium_label || "Premium", detail.premium],
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

function DriversTab({ id, scheduled }) {
  const d = useTabData(api.drivers, id);
  const onFile = d?.drivers?.length;
  return (
   <>
    {scheduled != null && (
      <div className="section-label" style={{ marginBottom: 8 }}>
        {(onFile ?? 0)} driver record{onFile === 1 ? "" : "s"} on file · {scheduled} scheduled per application
      </div>
    )}
    <DataTable rows={d?.drivers} empty="No driver records linked to this submission (schedule pending upload / insured not yet linked)" cols={[
    { k: "name", label: "Driver" },
    { k: "cdl_class", label: "CDL" },
    { k: "experience", label: "Yrs Exp", num: true },
    { k: "mvr_points", label: "MVR Pts", num: true, render: (r) => (
      <span style={{ color: r.mvr_points >= 5 ? "var(--danger)" : "var(--text)", fontWeight: r.mvr_points >= 5 ? 700 : 400 }}>{r.mvr_points ?? "—"}</span>
    ) },
    { k: "accidents", label: "Acc 3yr", num: true },
    { k: "status", label: "Status" },
    { k: "hazmat", label: "HazMat", render: (r) => (r.hazmat ? "Yes" : "No") },
  ]} />
   </>
  );
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

// ── Action confirmation modal ─────────────────────────────────────────────
function ActionModal({ action, reason, setReason, onConfirm, onCancel }) {
  const cfg = ACTION_CFG[action] || {};
  const blocked = cfg.required && !reason.trim();
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head" style={{ color: cfg.color }}>
          <span style={{ fontSize: 18 }}>{cfg.icon}</span> {cfg.label}
        </div>
        <p className="modal-msg">{cfg.message}</p>
        <textarea
          className="modal-textarea"
          placeholder={cfg.placeholder}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          autoFocus
        />
        {cfg.required && !reason.trim() && (
          <div style={{ fontSize: 12, color: "var(--danger)", marginTop: 4 }}>
            A reason is required for this action.
          </div>
        )}
        <div className="modal-actions">
          <button className="btn ghost" onClick={onCancel}>Cancel</button>
          <button
            className={`btn ${cfg.btnClass}`}
            disabled={blocked}
            style={{ opacity: blocked ? 0.45 : 1 }}
            onClick={onConfirm}
          >
            Confirm — {cfg.label}
          </button>
        </div>
      </div>
    </div>
  );
}
