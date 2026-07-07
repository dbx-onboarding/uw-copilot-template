import React, { useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import { Icon } from "./ui.jsx";

const SUGGESTIONS = [
  "Summarize the loss history",
  "What are the key risk drivers?",
  "Compare to similar accounts",
  "Any referral triggers here?",
];

export default function Chat({ submission, sessionId, toast }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [fb, setFb] = useState({});
  const scrollRef = useRef(null);

  // Reset the thread when the underwriter opens a different submission.
  useEffect(() => { setMessages([]); setFb({}); }, [submission?.id]);
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, busy]);

  const ask = async (text) => {
    const question = (text ?? input).trim();
    if (!question || busy) return;
    setInput("");
    const next = [...messages, { role: "user", content: question }];
    setMessages(next);
    setBusy(true);
    try {
      const res = await api.chat({
        question,
        session_id: sessionId,
        history: next,
      });
      setMessages([...next, { role: "assistant", content: res.answer }]);
    } catch {
      setMessages([...next, { role: "assistant", content: "Something went wrong reaching the CoPilot." }]);
    } finally {
      setBusy(false);
    }
  };

  const rate = async (i, rating) => {
    const a = messages[i]?.content || "";
    const qy = messages[i - 1]?.content || "";
    setFb((f) => ({ ...f, [i]: rating }));
    try {
      await api.feedback({ query: qy, response: a, rating, session_id: sessionId });
      toast(rating === "thumbs_up" ? "Thanks for the feedback" : "Noted — we'll use this to improve");
    } catch {}
  };

  return (
    <div className="panel chat-panel">
      <div className="panel-head">
        <div className="panel-title"><Icon.robot width={17} height={17} /> CoPilot Assistant</div>
        <button className="btn ghost" style={{ padding: "5px 10px" }} onClick={() => { setMessages([]); setFb({}); }}>
          + New chat
        </button>
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
