import React, { useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import { Icon } from "./ui.jsx";

const DEFAULT_SUGGESTIONS = [
  "Summarize the loss history",
  "What are the key risk drivers?",
  "Compare to similar accounts",
  "Any referral triggers here?",
];

const HISTORY_ID = "__history__";
const STORE_PREFIX = "uwcopilot.chat.";
const keyFor = (submission) => STORE_PREFIX + (submission?.id || "portfolio");

const uid = () =>
  typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : String(Math.random());
const freshChat = () => ({ id: uid(), title: "New chat", messages: [], fb: {}, renamed: false });

function loadChats(submission) {
  try {
    const raw = localStorage.getItem(keyFor(submission));
    const arr = raw ? JSON.parse(raw) : null;
    if (Array.isArray(arr) && arr.length) return arr;
  } catch {}
  return [freshChat()];
}

export default function Chat({ submission, sessionId, toast, suggestions }) {
  const SUGGESTIONS = suggestions && suggestions.length ? suggestions : DEFAULT_SUGGESTIONS;
  const [chats, setChats] = useState(() => loadChats(submission));
  const [activeId, setActiveId] = useState(() => chats[0]?.id);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editVal, setEditVal] = useState("");
  const [serverHist, setServerHist] = useState(null);
  const [openHist, setOpenHist] = useState({});
  const scrollRef = useRef(null);

  const persist = (arr) => {
    try { localStorage.setItem(keyFor(submission), JSON.stringify(arr)); } catch {}
  };
  // All mutations go through commit() so state + localStorage stay in lock-step.
  const commit = (updater) =>
    setChats((prev) => {
      const next = typeof updater === "function" ? updater(prev) : updater;
      persist(next);
      return next;
    });

  // Load this submission's saved tabs when the account changes (or on mount).
  useEffect(() => {
    const loaded = loadChats(submission);
    setChats(loaded);
    setActiveId(loaded[0]?.id);
    setInput("");
    setEditingId(null);
  }, [submission?.id]);

  // Keep a valid active tab.
  useEffect(() => {
    if (activeId !== HISTORY_ID && !chats.find((c) => c.id === activeId)) {
      setActiveId(chats[0]?.id ?? null);
    }
  }, [chats, activeId]);

  const isHistory = activeId === HISTORY_ID;
  const active = chats.find((c) => c.id === activeId) || chats[0];

  // Pull server-persisted history each time the History tab is opened.
  useEffect(() => {
    if (isHistory) {
      api.history().then((r) => setServerHist(r.items || [])).catch(() => setServerHist([]));
    }
  }, [isHistory]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [active?.messages, busy, isHistory]);

  const patchActive = (fn) => commit((prev) => prev.map((c) => (c.id === active.id ? fn(c) : c)));

  const addChat = () => {
    const c = freshChat();
    commit((prev) => [...prev, c]);
    setActiveId(c.id);
    setInput("");
  };

  const closeChat = (id, e) => {
    e.stopPropagation();
    commit((prev) => {
      const rest = prev.filter((c) => c.id !== id);
      return rest.length ? rest : [freshChat()];
    });
  };

  const startRename = (c, e) => {
    e.stopPropagation();
    setEditingId(c.id);
    setEditVal(c.title);
  };
  const commitRename = () => {
    const v = (editVal || "").trim() || "New chat";
    commit((prev) => prev.map((c) => (c.id === editingId ? { ...c, title: v, renamed: true } : c)));
    setEditingId(null);
  };

  const ask = async (text) => {
    const question = (text ?? input).trim();
    if (!question || busy || isHistory) return;
    setInput("");
    const next = [...active.messages, { role: "user", content: question }];
    patchActive((c) => ({
      ...c,
      messages: next,
      title: (!c.renamed && c.title === "New chat") ? question.slice(0, 32) : c.title,
    }));
    setBusy(true);
    try {
      const res = await api.chat({
        question,
        session_id: sessionId,
        submission_id: submission?.id || "",
        submission_context: submission
          ? {
              "Company": submission.name,
              "Submission ID": submission.id,
              "Status": submission.status,
              "Operation": submission.operation,
              "Commodity": submission.commodity,
              "Fleet Size": submission.fleet_size,
              "Drivers": submission.driver_count,
              "Loss Ratio (3yr)": submission.loss_ratio
                ? `${Math.floor(submission.loss_ratio * 100)}%`
                : null,
              "Premium": submission.premium,
              "Underwriter": submission.underwriter,
              "Risk Level": submission.risk,
              "Referral Required": submission.referral ? "Yes" : "No",
            }
          : {},
        history: next,
      });
      patchActive((c) => ({ ...c, messages: [...next, { role: "assistant", content: res.answer, sources: res.sources }] }));
    } catch {
      patchActive((c) => ({
        ...c,
        messages: [...next, { role: "assistant", content: "Something went wrong reaching the CoPilot." }],
      }));
    } finally {
      setBusy(false);
    }
  };

  const rate = async (i, rating) => {
    const a = active.messages[i]?.content || "";
    const qy = active.messages[i - 1]?.content || "";
    patchActive((c) => ({ ...c, fb: { ...c.fb, [i]: rating } }));
    try {
      await api.feedback({ query: qy, response: a, rating, session_id: sessionId });
      toast(rating === "thumbs_up" ? "Thanks for the feedback" : "Noted — we'll use this to improve");
    } catch {}
  };

  // Flatten every Q&A pair across tabs for the History view (newest first).
  const historyItems = [];
  chats.forEach((c) => {
    for (let i = 0; i < c.messages.length; i++) {
      if (c.messages[i].role === "user") {
        const a = c.messages[i + 1] && c.messages[i + 1].role === "assistant" ? c.messages[i + 1] : null;
        historyItems.push({ chatId: c.id, chatTitle: c.title, q: c.messages[i].content, a: a ? a.content : null });
      }
    }
  });
  historyItems.reverse();

  const messages = active?.messages || [];
  const fb = active?.fb || {};

  return (
    <div className="panel chat-panel">
      <div className="panel-head">
        <div className="panel-title"><Icon.robot width={17} height={17} /> CoPilot Assistant</div>
        <button className="btn ghost" style={{ padding: "5px 10px" }} onClick={addChat}>+ New chat</button>
      </div>

      <div className="chat-tabs">
        {chats.map((c) => (
          <div
            key={c.id}
            className={`chat-tab ${c.id === activeId ? "active" : ""}`}
            onClick={() => setActiveId(c.id)}
            title="Double-click to rename"
          >
            {editingId === c.id ? (
              <input
                className="tab-edit"
                value={editVal}
                autoFocus
                onChange={(e) => setEditVal(e.target.value)}
                onBlur={commitRename}
                onClick={(e) => e.stopPropagation()}
                onKeyDown={(e) => {
                  if (e.key === "Enter") { e.preventDefault(); commitRename(); }
                  if (e.key === "Escape") setEditingId(null);
                }}
              />
            ) : (
              <span className="tab-label" onDoubleClick={(e) => startRename(c, e)}>{c.title}</span>
            )}
            {chats.length > 1 && editingId !== c.id && (
              <span className="tab-x" onClick={(e) => closeChat(c.id, e)}>×</span>
            )}
          </div>
        ))}
        <div
          className={`chat-tab history ${isHistory ? "active" : ""}`}
          onClick={() => setActiveId(HISTORY_ID)}
          title="All previous questions & answers"
        >
          <span className="tab-label">🕘 History</span>
        </div>
      </div>

      {isHistory ? (
        (() => {
          // Prefer server-persisted history (survives tab close / device); else local.
          const useServer = serverHist && serverHist.length > 0;
          const list = useServer
            ? serverHist.map((h) => ({ q: h.q, a: h.a, meta: h.when, chatId: null }))
            : historyItems.map((h) => ({ q: h.q, a: h.a, meta: h.chatTitle, chatId: h.chatId }));
          return (
            <div className="chat-scroll">
              {serverHist === null && historyItems.length === 0 ? (
                <div className="empty" style={{ margin: "auto 0" }}><span className="dots">Loading history</span></div>
              ) : list.length === 0 ? (
                <div className="empty" style={{ margin: "auto 0" }}>
                  <div style={{ fontWeight: 600, color: "var(--muted)" }}>No questions yet</div>
                  <div style={{ fontSize: 12, color: "var(--subtle)" }}>Ask the CoPilot and your Q&amp;A history will collect here.</div>
                </div>
              ) : (<>
                <div className="hist-head">{useServer ? "Your saved history" : "This session"} · tap an item to expand</div>
                {list.map((h, i) => (
                  <div className={`hist-item ${openHist[i] ? "expanded" : ""}`} key={i}
                       onClick={() => setOpenHist((o) => ({ ...o, [i]: !o[i] }))}>
                    <div className="hist-meta">{h.meta}<span className="hist-toggle">{openHist[i] ? "▾ collapse" : "▸ expand"}</span></div>
                    <div className="hist-q">Q: {h.q}</div>
                    {h.a && <div className="hist-a">{h.a}</div>}
                  </div>
                ))}
              </>)}
            </div>
          );
        })()
      ) : (
        <div className="chat-scroll" ref={scrollRef}>
          {messages.length === 0 && !busy ? (
            <div className="empty" style={{ margin: "auto 0" }}>
              <Icon.spark width={26} height={26} />
              <div style={{ fontWeight: 600, color: "var(--muted)" }}>
                Ask about {submission?.name || "this submission"}
              </div>
              <div className="suggest">
                {SUGGESTIONS.map((s) => (
                  <span key={s} className="chip" onClick={() => ask(s)}>{s}</span>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m, i) => (
              <div key={i} className={`msg ${m.role}`}>
                <div className="who">{m.role === "user" ? "You" : "CoPilot"}</div>
                <div className="bubble">{m.content}</div>
                {m.role === "assistant" && m.sources && m.sources.length > 0 && (
                  <div className="cite-row">
                    {m.sources.map((s, k) => (
                      <span className="cite" key={k}>📄 {s.title}{s.page ? ` · p.${s.page}` : ""}</span>
                    ))}
                  </div>
                )}
                {m.role === "assistant" && (
                  <div className="fb-row">
                    <button className={`fb-btn ${fb[i] === "thumbs_up" ? "done" : ""}`} onClick={() => rate(i, "thumbs_up")}>👍 Helpful</button>
                    <button className={`fb-btn ${fb[i] === "thumbs_down" ? "done" : ""}`} onClick={() => rate(i, "thumbs_down")}>👎 Not helpful</button>
                  </div>
                )}
              </div>
            ))
          )}
          {busy && (
            <div className="msg assistant">
              <div className="who">CoPilot</div>
              <div className="bubble"><span className="dots">Analyzing</span></div>
            </div>
          )}
        </div>
      )}

      {!isHistory && (
        <div className="chat-input">
          <textarea
            rows={1}
            value={input}
            placeholder="Ask about this submission..."
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(); }
            }}
          />
          <button className="btn primary" disabled={busy || !input.trim()} onClick={() => ask()}>
            <Icon.send width={15} height={15} />
          </button>
        </div>
      )}
    </div>
  );
}
