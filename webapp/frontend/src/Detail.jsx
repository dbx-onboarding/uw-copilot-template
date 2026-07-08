import React, { useEffect, useState } from "react";
import { api } from "./api.js";
import { Icon, RiskBadge, pct, Spinner } from "./ui.jsx";
import Chat from "./Chat.jsx";

const TABS = ["Overview", "Pricing", "Authority & Safety", "Claims", "Loss Development", "Drivers", "Documents", "Notes"];

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
              {detail.account_type && (
                <span className={`badge ${detail.account_type === "Renewal" ? "renewal" : "newbiz"}`}>
                  {detail.account_type === "Renewal" ? "RENEWAL" : "NEW BUSINESS"}
                </span>
              )}
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
          {tab === "Pricing" && <PricingTab id={detail.id} />}
          {tab === "Authority & Safety" && <AuthoritySafetyTab id={detail.id} newBiz={detail.account_type === "New Business"} />}
          {tab === "Claims" && <ClaimsTab id={detail.id} newBiz={detail.account_type === "New Business"} />}
          {tab === "Loss Development" && <LossDevTab id={detail.id} newBiz={detail.account_type === "New Business"} />}
          {tab === "Drivers" && <DriversTab id={detail.id} scheduled={detail.driver_count} newBiz={detail.account_type === "New Business"} />}
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
    ["Account", detail.account_type],
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

  const evidence = a.evidence || [];
  return (
    <>
      <div className="ai-card">
        <div className="head">
          <Icon.spark width={14} height={14} /> AI Recommendation
          <span className="ai-sub">Decision support · underwriter decides</span>
        </div>
        <div className="ai-body2">
          <div className={`verdict ${verdict}`}>{verdict}</div>
          <div className="conf-chip">Confidence <b>{a.confidence_label || "—"}</b></div>
        </div>
        {a.rationale && <div className="ai-rationale">{a.rationale}</div>}
        {evidence.length > 0 && (
          <div className="evidence">
            {evidence.map((e, i) => (
              <div className={`ev-row ${e.severity}`} key={i}>
                <span className="ev-dot" />
                <span className="ev-factor">{e.factor}</span>
                <span className="ev-val">{e.value}</span>
                <span className="ev-detail">{e.detail}</span>
                <span className="ev-rule">{e.rule}</span>
              </div>
            ))}
          </div>
        )}
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
          <div className="section-label">Recommended Next Steps</div>
          {(a.next_steps || []).map((s, i) => (
            <div className="step-line" key={i}><span className="n">{i + 1}</span><span>{s}</span></div>
          ))}
          {(a.subjectivities || []).length > 0 && (<>
            <div className="section-label" style={{ marginTop: 18 }}>Recommended Subjectivities</div>
            {a.subjectivities.map((s, i) => (
              <div className="risk-line" key={i}><Icon.check width={14} height={14} className="mk" /><span>{s}</span></div>
            ))}
          </>)}
        </div>
      </div>

      <div className="actions-row">
        <button className="btn success" disabled={!!decided} onClick={() => decide("Approved")}>Approve</button>
        <button className="btn warn" disabled={!!decided} onClick={() => decide("Referred")}>Refer to Senior UW</button>
        <button className="btn danger" disabled={!!decided} onClick={() => decide("Declined")}>Decline</button>
        <button className="btn" onClick={() => decide("Info Requested")}>Request Info</button>
        <button className="btn ghost" style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
          onClick={() => window.open(`/api/submissions/${encodeURIComponent(detail.id)}/quote-letter`, "_blank")}>
          <Icon.docs width={14} height={14} /> Quote Letter
        </button>
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

const NEWBIZ_NOTE = "New business submission — no prior Atlas policy history. Underwrite from the prior-carrier loss runs, MVRs, and application under Documents.";

function ClaimsTab({ id, newBiz }) {
  const d = useTabData(api.claims, id);
  return <DataTable rows={d?.claims} empty={newBiz ? NEWBIZ_NOTE : "No claims on record"} cols={[
    { k: "claim_id", label: "Claim" },
    { k: "date", label: "Loss Date" },
    { k: "type", label: "Type" },
    { k: "status", label: "Status" },
    { k: "litigation", label: "Litigation" },
    { k: "incurred", label: "Incurred", num: true },
    { k: "paid", label: "Paid", num: true },
  ]} />;
}

function LossDevTab({ id, newBiz }) {
  const d = useTabData(api.lossDev, id);
  if (d === null) return <Spinner />;
  const periods = d?.periods || [];
  const s = d?.summary;
  if (periods.length === 0) {
    return <div className="empty" style={{ padding: 30 }}>{newBiz ? NEWBIZ_NOTE : "No loss runs on record"}</div>;
  }
  return (
    <>
      {s && (
        <div className="mini-stats" style={{ marginBottom: 14 }}>
          <span className={`mini-stat ${s.trend === "Deteriorating" ? "danger" : s.trend === "Improving" ? "" : ""}`}>Trend: {s.trend}</span>
          <span className="mini-stat">{s.trend_detail}</span>
          {s.total_large_losses > 0 && <span className="mini-stat warn">{s.total_large_losses} large loss{s.total_large_losses === 1 ? "" : "es"} (&ge;$100K)</span>}
          <span className="mini-stat">Open reserves {s.open_reserves}</span>
          <span className="mini-stat">Valued {s.valued_as_of}</span>
        </div>
      )}
      <DataTable rows={periods} empty="No loss runs on record" cols={[
        { k: "period", label: "Period" },
        { k: "valued", label: "Valued" },
        { k: "claims", label: "Claims", num: true },
        { k: "large_losses", label: "Large", num: true },
        { k: "incurred", label: "Incurred", num: true },
        { k: "paid", label: "Paid", num: true },
        { k: "open_reserves", label: "Open Res.", num: true },
        { k: "loss_ratio", label: "Loss Ratio", num: true },
        { k: "severity", label: "Severity", num: true },
      ]} />
      <div style={{ fontSize: 11.5, color: "var(--subtle)", marginTop: 8 }}>
        Loss ratio = incurred ÷ earned premium. Severity = avg cost per claim. Figures as valued above — confirm current valuation before binding.
      </div>
    </>
  );
}

function PricingTab({ id }) {
  const d = useTabData(api.pricing, id);
  if (d === null) return <Spinner />;
  if (!d || Object.keys(d).length === 0) return <div className="empty" style={{ padding: 30 }}>Pricing indication unavailable.</div>;
  const adqClass = d.adequacy === "Adequate" ? "low" : d.adequacy === "Marginal" ? "med" : d.adequacy === "Inadequate" ? "high" : "neutral";
  const cards = [
    ["Expiring premium", d.expiring_premium || "—"],
    ["Indicated premium", d.indicated_premium || "—"],
    ["Quoted premium", d.quoted_premium || "—"],
    ["Rate need vs. expiring", d.rate_need_pct || "—"],
    ["Rate taken (quoted)", d.rate_taken_pct || "—"],
    ["Target loss ratio", d.target_loss_ratio || "—"],
    ["Premium / unit (quoted)", d.premium_per_unit_quoted || "—"],
    ["Indicated / unit", d.premium_per_unit_indicated || "—"],
    ["Loss cost / unit (annual)", d.loss_cost_per_unit || "—"],
  ];
  return (
    <>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
        <div className="section-label" style={{ margin: 0 }}>Rate Adequacy</div>
        <span className={`badge ${adqClass}`}>{d.adequacy}</span>
      </div>
      <div className="pricing-grid">
        {cards.map(([k, v]) => (
          <div className="price-card" key={k}><div className="pc-val">{v}</div><div className="pc-lbl">{k}</div></div>
        ))}
      </div>
      <div style={{ fontSize: 12, color: "var(--subtle)", marginTop: 12, lineHeight: 1.6 }}>
        <b>Basis:</b> {d.basis}<br />{d.trend_note} Indicated premium brings expected losses to the {d.target_loss_ratio} target loss ratio. This is a working indication — confirm class rates and schedule mods in the rating workbook before quoting.
      </div>
    </>
  );
}

function IntelRow({ label, value, alert }) {
  return (
    <tr><td>{label}</td><td className={alert ? "intel-alert" : ""}>{value}{alert ? "  ⚠" : ""}</td></tr>
  );
}

function AuthoritySafetyTab({ id, newBiz }) {
  const d = useTabData(api.accountIntel, id);
  if (d === null) return <Spinner />;
  if (!d || Object.keys(d).length === 0) {
    return <div className="empty" style={{ padding: 30 }}>{newBiz ? "New business — authority & FMCSA intel not yet loaded. Pull the SAFER/SMS snapshot and prior-carrier detail." : "No authority/FMCSA record on file."}</div>;
  }
  const yn = (b) => (b ? "On file" : "Missing");
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 22 }}>
      <div>
        <div className="section-label">Authority & Market</div>
        <table className="snap"><tbody>
          <IntelRow label="Operating authority since" value={d.authority_granted || "—"} />
          <IntelRow label="Authority age" value={d.authority_age_years != null ? `${d.authority_age_years} yrs` : "—"} alert={d.new_authority} />
          <IntelRow label="Prior / incumbent carrier" value={d.prior_carrier || "—"} />
          <IntelRow label="Years with prior carrier" value={d.years_with_prior != null ? d.years_with_prior : "—"} />
          <IntelRow label="Reason in market" value={d.reason_in_market || "—"} />
          <IntelRow label="Operating radius" value={d.operating_radius || "—"} />
        </tbody></table>
        <div className="section-label" style={{ marginTop: 16 }}>Filings</div>
        <table className="snap"><tbody>
          <IntelRow label="MCS-150 current" value={d.mcs150_current ? "Current" : "Not current"} alert={!d.mcs150_current} />
          <IntelRow label="MCS-90 endorsement" value={yn(d.mcs90_on_file)} alert={!d.mcs90_on_file} />
          <IntelRow label="BMC-91 filing" value={yn(d.bmc91_on_file)} alert={!d.bmc91_on_file} />
        </tbody></table>
      </div>
      <div>
        <div className="section-label">FMCSA SMS Posture</div>
        <table className="snap"><tbody>
          <IntelRow label="Vehicle OOS rate" value={d.oos_vehicle_pct != null ? `${d.oos_vehicle_pct}% (nat'l ${d.national_oos_vehicle_avg}%)` : "—"} alert={d.vehicle_oos_alert} />
          <IntelRow label="Driver OOS rate" value={d.oos_driver_pct != null ? `${d.oos_driver_pct}% (nat'l ${d.national_oos_driver_avg}%)` : "—"} alert={d.driver_oos_alert} />
          <IntelRow label="Crash rate / 100 units" value={d.crash_rate_per_100 != null ? d.crash_rate_per_100 : "—"} />
        </tbody></table>
        <div style={{ fontSize: 12, color: "var(--subtle)", marginTop: 12, lineHeight: 1.6 }}>
          <b>Data provenance</b><br />
          FMCSA SMS snapshot: {d.csa_as_of || "—"}<br />
          Loss runs valued: {d.loss_runs_valued || "—"}<br />
          <span style={{ color: "var(--muted)" }}>⚠ marks metrics above the national average or a missing filing — verify before quoting.</span>
        </div>
      </div>
    </div>
  );
}

function DriversTab({ id, scheduled, newBiz }) {
  const d = useTabData(api.drivers, id);
  const onFile = d?.drivers?.length;
  return (
   <>
    {scheduled != null && (
      <div className="section-label" style={{ marginBottom: 8 }}>
        {(onFile ?? 0)} driver record{onFile === 1 ? "" : "s"} on file · {scheduled} scheduled per application
      </div>
    )}
    <DataTable rows={d?.drivers} empty={newBiz
      ? "New business submission — driver MVRs not yet loaded into Atlas. Review the application driver schedule and ordered MVRs under Documents."
      : "No driver records linked to this submission (schedule pending upload)"} cols={[
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
