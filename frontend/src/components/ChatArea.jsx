// ChatArea.jsx - Main chat window with marks selector

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Database, Zap } from "lucide-react";
import { sendQuestion } from "../api";
import { getSubject } from "../subjects";

// ── Mark pill labels ──────────────────────────────────────────────────────────
const MARKS_OPTIONS = [
  { value: null, label: "Auto",   emoji: "🤖", title: "Let AI decide answer depth" },
  { value: 3,    label: "3 Marks", emoji: "⚡", title: "Short answer (Part A)" },
  { value: 6,    label: "6 Marks", emoji: "📝", title: "Medium answer (Part B)" },
  { value: 10,   label: "10 Marks",emoji: "📖", title: "Long answer (Part C)" },
];

const PART_LABELS = {
  a_i:    { label: "Part A(i)", marks: 3,  color: "#10B981" },
  a_ii:   { label: "Part A(ii)", marks: 3, color: "#10B981" },
  a:      { label: "Part A", marks: 3,     color: "#10B981" },
  b:      { label: "Part B", marks: 6,     color: "#F59E0B" },
  b_i:    { label: "Part B", marks: 6,     color: "#F59E0B" },
  c_i:    { label: "Part C(i) — Either", marks: 10, color: "#8B5CF6" },
  c_ii:   { label: "Part C(ii) — Or",   marks: 10, color: "#8B5CF6" },
  generic:{ label: "General", marks: 0, color: "#6B7280" },
};

// ── Sub-components ────────────────────────────────────────────────────────────

function TypingIndicator() {
  return (
    <div className="message bot">
      <div className="msg-avatar"><Bot size={16} /></div>
      <div className="msg-bubble">
        <div className="typing-indicator">
          <span /><span /><span />
        </div>
      </div>
    </div>
  );
}

function WelcomeScreen() {
  return (
    <div className="welcome-screen">
      <div className="welcome-icon">🎓</div>
      <h2>Sem 7 Study Assistant</h2>
      <p>Trained on Anna University question papers. Pick your subject, unit, and mark type — then ask!</p>
      <div className="steps">
        <div className="step"><div className="step-num">1</div>Select subject</div>
        <div className="step"><div className="step-num">2</div>Pick unit</div>
        <div className="step"><div className="step-num">3</div>Choose mark type</div>
        <div className="step"><div className="step-num">4</div>Ask your question!</div>
      </div>
    </div>
  );
}

function MarksBadge({ marks, part }) {
  if (!marks && !part) return null;
  const info = PART_LABELS[part] || {};
  return (
    <div style={{ display: "flex", gap: 5, flexWrap: "wrap", marginTop: 8 }}>
      {marks > 0 && (
        <span className="chunks-badge" style={{ background: `${info.color}22`, color: info.color }}>
          <Zap size={10} /> {marks} marks
        </span>
      )}
      {part && part !== "generic" && (
        <span className="chunks-badge" style={{ background: `${info.color}15`, color: info.color }}>
          {info.label}
        </span>
      )}
    </div>
  );
}

function MessageBubble({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={`message ${isUser ? "user" : "bot"}`}>
      <div className="msg-avatar">
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>
      <div>
        <div className="msg-bubble">
          {/* User mark badge */}
          {isUser && msg.marks && (
            <div style={{
              fontSize: 11, fontWeight: 700, opacity: 0.8,
              marginBottom: 4, color: "rgba(255,255,255,0.85)"
            }}>
              {msg.marks}-mark question
            </div>
          )}
          <span style={{ whiteSpace: "pre-wrap" }}>{msg.content}</span>

          {/* Bot metadata badges */}
          {!isUser && (
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 10 }}>
              {msg.detectedMarks && (
                <MarksBadge marks={msg.detectedMarks} part={msg.topParts?.[0]} />
              )}
              {msg.chunksUsed > 0 && (
                <span className="chunks-badge">
                  <Database size={10} /> {msg.chunksUsed} past questions used
                </span>
              )}
            </div>
          )}
        </div>
        <div className="msg-meta">{msg.time}</div>
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function ChatArea({ selectedSubject, selectedUnit }) {
  const [messages, setMessages]   = useState([]);
  const [input, setInput]         = useState("");
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);
  const [selectedMarks, setMarks] = useState(null); // null = auto
  const bottomRef = useRef(null);

  const subject  = getSubject(selectedSubject);
  const canChat  = !!selectedSubject && !!selectedUnit;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async () => {
    const q = input.trim();
    if (!q || loading || !canChat) return;

    const userMsg = {
      id:    Date.now(),
      role:  "user",
      content: q,
      marks: selectedMarks,
      time:  new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const res = await sendQuestion({
        question: q,
        subject:  selectedSubject,
        unit:     selectedUnit,
        marks:    selectedMarks,
      });

      const botMsg = {
        id:            Date.now() + 1,
        role:          "bot",
        content:       res.answer,
        chunksUsed:    res.chunks_used,
        detectedMarks: res.detected_marks,
        topParts:      res.top_parts,
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error("API error:", err);
      setError(
        err?.response?.data?.detail || err?.message || "Something went wrong. Is the backend running?"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-area">
      {/* Context bar */}
      <div className="context-bar">
        {subject ? (
          <span className="context-tag subject">{subject.icon} {subject.shortName}</span>
        ) : (
          <span className="context-tag empty">No subject</span>
        )}
        {selectedUnit ? (
          <span className="context-tag unit">📖 Unit {selectedUnit}</span>
        ) : (
          <span className="context-tag empty">No unit</span>
        )}
      </div>

      {/* Messages */}
      <div className="messages-container">
        {messages.length === 0 && !loading ? (
          <WelcomeScreen />
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} msg={msg} />)
        )}
        {loading && <TypingIndicator />}
        {error && (
          <div style={{
            background: "#FEE2E2", color: "#DC2626",
            padding: "10px 14px", borderRadius: 10,
            fontSize: 13, alignSelf: "center"
          }}>
            ⚠️ {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Marks selector + Input bar */}
      <div className="input-bar">
        {/* Mark type selector */}
        <div className="marks-selector">
          <span className="marks-label">Answer depth:</span>
          <div className="marks-pills">
            {MARKS_OPTIONS.map((opt) => (
              <button
                key={opt.value ?? "auto"}
                className={`marks-pill ${selectedMarks === opt.value ? "active" : ""}`}
                onClick={() => setMarks(opt.value)}
                title={opt.title}
              >
                {opt.emoji} {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="input-row">
          <textarea
            className="chat-input"
            placeholder={
              canChat
                ? `Ask a ${selectedMarks ? `${selectedMarks}-mark ` : ""}question about ${subject?.shortName} — Unit ${selectedUnit}...`
                : "Select a subject and unit first..."
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!canChat || loading}
            rows={1}
          />
          <button
            className="send-btn"
            onClick={handleSend}
            disabled={!canChat || !input.trim() || loading}
            title="Send (Enter)"
          >
            <Send size={18} />
          </button>
        </div>
        <p className="input-hint">
          <strong>Enter</strong> to send · <strong>Shift+Enter</strong> for new line
        </p>
      </div>
    </div>
  );
}
