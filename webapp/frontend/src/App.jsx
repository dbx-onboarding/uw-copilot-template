import React, { useEffect, useMemo, useState } from "react";
import { api } from "./api.js";
import { Icon, Spinner } from "./ui.jsx";
import Queue from "./Queue.jsx";
import Detail from "./Detail.jsx";
import { HomeView, ClaimsView, LossControlView, AnalyticsView, DocumentsView, SettingsView } from "./Views.jsx";

// Databricks-style left-rail navigation.
const NAV = [
  { key: "home", label: "Home", icon: Icon.grid },
  { key: "submissions", label: "Submissions", icon: Icon.inbox },
  { key: "claims", label: "Claims", icon: Icon.folder },
  { key: "loss_control", label: "Loss Control", icon: Icon.shield },
  { key: "analytics", label: "Analytics", icon: Icon.chart },
  { key: "documents", label: "Documents", icon: Icon.docs },
  { key: "settings", label: "Settings", icon: Icon.gear },
];

const sessionId = crypto.randomUUID ? crypto.randomUUID() : String(Math.random());

export default function App() {
  const [me, setMe] = useState(null);
  const [subs, setSubs] = useState(null);
  const [kpis, setKpis] = useState({});
  const [selected, setSelected] = useState(null);
  const [nav, setNav] = useState("home");
  const [toasts, setToasts] = useState([]);
  const [helpOpen, setHelpOpen] = useState(false);

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
  const navLabel = NAV.find((x) => x.key === nav)?.label || "Home";
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
          <button className="iconbtn" title="How it works" onClick={() => setHelpOpen(true)}><Icon.help width={16} height={16} /></button>
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
            <Spinner label="Loading" />
          ) : selected ? (
            <Detail summary={selected} sessionId={sessionId} toast={toast} onBack={() => setSelected(null)} />
          ) : nav === "home" ? (
            <HomeView kpis={kpis} sessionId={sessionId} toast={toast} />
          ) : nav === "submissions" ? (
            <Queue subs={subs} onOpen={setSelected} />
          ) : nav === "claims" ? (
            <ClaimsView />
          ) : nav === "loss_control" ? (
            <LossControlView />
          ) : nav === "analytics" ? (
            <AnalyticsView subs={subs} kpis={kpis} />
          ) : nav === "documents" ? (
            <DocumentsView />
          ) : nav === "settings" ? (
            <SettingsView />
          ) : (
            <Placeholder label={navLabel} onBack={() => goNav("home")} />
          )}
        </main>
      </div>

      <div className="toast-wrap">
        {toasts.map((t) => (<div className="toast" key={t.id}>{t.msg}</div>))}
      </div>
      {helpOpen && <HelpModal onClose={() => setHelpOpen(false)} />}
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

// ── Help / How It Works modal ──────────────────────────────────────────
const HELP_STAGES = [
  {
    icon: "📥",
    title: "1 — Submission Intake",
    color: "var(--info)",
    desc: "Broker uploads ACORD 125, loss runs, MVR reports, and DOT certificates to S3. Auto Loader detects new files every 15 minutes and triggers the pipeline automatically — no manual steps required.",
    details: ["Supports PDF, CSV, and image attachments", "Files land in S3 → parsed page-by-page into text", "Written to document_chunks (Delta) within 5–20 min of upload"],
  },
  {
    icon: "🔍",
    title: "2 — Chunking & Vector Indexing",
    color: "var(--info)",
    desc: "Each document is split into overlapping text chunks (~500 tokens). Chunks are embedded using Databricks' embedding model and indexed in the Vector Search endpoint for hybrid (semantic + keyword) retrieval.",
    details: ["2,268 chunks indexed across 1,500 PDF documents", "Hybrid search: dense embeddings + BM25 keyword", "New submissions are searchable within 20 min"],
  },
  {
    icon: "🗄️",
    title: "3 — Structured Data Layer",
    color: "var(--success)",
    desc: "Structured fields extracted from submission forms are written to 8 live Delta tables in Unity Catalog. Every tab in the workbench (Claims, Loss Runs, Drivers, Documents) pulls directly from these tables via the SQL Warehouse.",
    details: ["Tables: submissions · insureds · drivers · policies · claims · loss_runs · loss_ratios · referrals", "All data is live — no nightly refreshes", "Secured by Unity Catalog fine-grained access controls"],
  },
  {
    icon: "🧠",
    title: "4 — AI Risk Scoring",
    color: "var(--warn)",
    desc: "Every submission is scored server-side using Atlas underwriting rules: loss ratio vs 75% threshold, CSA Unsafe Driving scores, FMCSA safety rating, large loss count, and fleet size. The result is a verdict — APPROVE, REFER, or DECLINE — with a confidence percentage.",
    details: ["Loss ratio > 75% → automatic REFER", "CSA score > 65 or safety rating CONDITIONAL → REFER", "Risk indicators + recommended next steps generated per submission"],
  },
  {
    icon: "💬",
    title: "5 — CoPilot Chat (RAG)",
    color: "var(--brand)",
    desc: "Every chat message is enriched with the current submission's context (ID, loss ratio, fleet size, commodity, status) before being sent to the AI. The RAG agent queries the vector index for the 5 most relevant document chunks, then Claude Sonnet 4 synthesizes a grounded answer with source citations.",
    details: ["Submission context injected automatically — no copy-pasting", "Retrieves from actual submission PDFs (loss runs, ACORD forms, UW guidelines)", "Powered by Databricks Model Serving + Claude Sonnet 4"],
  },
  {
    icon: "✅",
    title: "6 — Decisions & Audit Trail",
    color: "var(--success)",
    desc: "Clicking Approve, Refer to Senior UW, Decline, or Request Info opens a confirmation modal. The decision and reason are written to the feedback_overrides audit table, and the submission status is updated live in the Delta table — no page reload needed.",
    details: ["Approved → status: Quoted", "Referred / Info Requested → status: In Review", "Declined → status: Declined", "Full audit: decision, reason, AI recommendation, timestamp, user — all persisted"],
  },
  {
    icon: "🔄",
    title: "7 — Feedback Loop",
    color: "var(--muted)",
    desc: "Thumbs up or down on any CoPilot response is written to the copilot_feedback table (rating stored as +1 / -1). This data feeds periodic RAG quality evaluation and signals which answers need model or prompt improvement.",
    details: ["Every chat response is rateable", "Ratings stored with session ID, user, question, and answer", "Used in evaluate notebook for RAG quality scoring"],
  },
];

function HelpModal({ onClose }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-card"
        style={{ width: 640, maxHeight: "80vh", overflowY: "auto", padding: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{
          padding: "22px 28px 18px",
          borderBottom: "1px solid var(--border)",
          position: "sticky", top: 0, background: "var(--card)", zIndex: 1,
          display: "flex", alignItems: "center", justifyContent: "space-between",
        }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: 16, color: "var(--text)" }}>How UW CoPilot Works</div>
            <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 3 }}>
              End-to-end flow from submission intake to final underwriting decision
            </div>
          </div>
          <button className="btn ghost" style={{ padding: "4px 10px", fontSize: 18, lineHeight: 1 }} onClick={onClose}>×</button>
        </div>

        {/* Intro */}
        <div style={{ padding: "18px 28px 4px" }}>
          <div style={{
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: "var(--radius-sm)", padding: "12px 16px",
            fontSize: 13, color: "var(--muted)", lineHeight: 1.6,
          }}>
            UW CoPilot connects your <strong style={{ color: "var(--text)" }}>live Delta Lake data</strong>,
            a <strong style={{ color: "var(--text)" }}>Vector Search index</strong> over 1,500 submission PDFs,
            and <strong style={{ color: "var(--text)" }}>Claude Sonnet 4</strong> into a single underwriting
            workbench — all running on Databricks Apps.
          </div>
        </div>

        {/* Pipeline stages */}
        <div style={{ padding: "12px 28px 28px", display: "flex", flexDirection: "column", gap: 4 }}>
          {HELP_STAGES.map((s, i) => (
            <HelpStage key={i} stage={s} />
          ))}
        </div>

        {/* Footer */}
        <div style={{
          borderTop: "1px solid var(--border)",
          padding: "14px 28px",
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}>
          <span style={{ fontSize: 12, color: "var(--subtle)" }}>
            Atlas Commercial Insurance · Databricks Apps · UW CoPilot v1.0
          </span>
          <button className="btn" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}

function HelpStage({ stage }) {
  const [open, setOpen] = React.useState(false);
  return (
    <div style={{
      border: "1px solid var(--border)",
      borderRadius: "var(--radius-sm)",
      overflow: "hidden",
      marginBottom: 6,
    }}>
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          width: "100%", display: "flex", alignItems: "flex-start", gap: 12,
          padding: "13px 16px", background: "var(--surface)",
          border: "none", cursor: "pointer", textAlign: "left",
        }}
      >
        <span style={{ fontSize: 20, lineHeight: 1, flexShrink: 0, marginTop: 1 }}>{stage.icon}</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, fontSize: 13, color: stage.color }}>{stage.title}</div>
          <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 3, lineHeight: 1.5 }}>{stage.desc}</div>
        </div>
        <span style={{ color: "var(--subtle)", fontSize: 14, flexShrink: 0, marginTop: 2 }}>{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div style={{ padding: "0 16px 14px 48px", background: "var(--card)" }}>
          <ul style={{ margin: 0, paddingLeft: 16 }}>
            {stage.details.map((d, i) => (
              <li key={i} style={{ fontSize: 12, color: "var(--muted)", marginBottom: 4, lineHeight: 1.5 }}>{d}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
