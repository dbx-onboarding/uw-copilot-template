import React, { useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import { Icon } from "./ui.jsx";

const DEFAULT_SUGGESTIONS = [
  "Summarize the loss history",
  "What are the key risk drivers?",
  "Compare to similar accounts",
  "Any referral triggers here?",
];

const uid = () =>
  typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : String(Math.random());
const freshChat = () => ({ id: uid(), title: "New chat", messages: [], fb: {} });

export default function Chat({ submission, sessionId, toast, suggestions }) {
  const SUGGESTIONS = suggestions && suggestions.length ? suggestions : DEFAULT_SUGGESTIONS;
  const [chats, setChats] = useState(() => [freshChat()]);
  const [activeId, setActiveId] = useState(() => null);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef(null);

  // Reset the tabs when the underwriter opens a different submission.
  useEffect(() => {
    const c = freshChat();
    setChats([c]);
    setActiveId(c.id);
    setInput("");
  }, [submission?.id]);

  // Keep an active tab valid even if the active one is closed.
  useEffect(() => {
    if (!chats.find((c) => c.id === activeId)) setActiveId(chats[0]?.id ?? null);
  }, [chats, activeId]);

  const active = chats.find((c) => c.id === activeId) || chats[0];

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [active?.messages, busy]);

  const patchActive = (fn) =>
    setChats((prev) => prev.map((c) => (c.id === active.id ? fn(c) : c)));

  const addChat = () => {
    const c = freshChat();
    setChats((prev) => [...prev, c]);
    setActiveId(c.id);
    setInput("");
  };

  const closeChat = (id, e) => {
    e.stopPropagation();
    setChats((prev) => {
      const rest = prev.filter((c) => c.id !== id);
      return rest.length ? rest : [freshChat()];
    });
  };

  const ask = async (text) => {
    const question = (text ?? input).trim();
    if (!question || busy) return;
    setInput("");
    const next = [...active.messages, { role: "user", content: question }];
    patchActive((c) => ({
      ...c,
      messages: next,
      title: c.title === "New chat" ? question.slice(0, 32) : c.title,
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

  const messages = active?.messages || [];
  const fb = active?.fb || {};

  return (
    <div className="panel chat-panel">
      <div className="panel-head">
        <div className="panel-title"><Icon.robot width={17} height={17} /> CoPilot Assistant</div>
        <button className="btn ghost" style={{ padding: "5px 10px" }} onClick={addChat}>
          + New chat
        </button>
      </div>

      <div className="chat-tabs">
        {chats.map((c) => (
          <div
            key={c.id}
            className={`chat-tab ${c.id === active.id ? "active" : ""}`}
            onClick={() => setActiveId(c.id)}
            title={c.title}
          >
            <span className="tab-label">{c.title}</span>
            {chats.length > 1 && (
              <span className="tab-x" onClick={(e) => closeChat(c.id, e)}>×</span>
            )}
          </div>
        ))}
      </div>

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
    </div>
  );
}
