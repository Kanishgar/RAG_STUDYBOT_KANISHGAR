// ChatArea.jsx — Button-driven question viewer
// Flow: Subject (sidebar) → Unit (sidebar) → click mark button → see all questions

import { useState, useRef, useEffect } from "react";
import { Bot, Database, ChevronRight, RotateCcw, Copy, Check } from "lucide-react";
import { fetchQuestions } from "../api";
import { getSubject } from "../subjects";

// ── Mark buttons config ───────────────────────────────────────────────────────
const MARK_BUTTONS = [
  {
    marks: 2,
    label: "2 Mark Questions",
    sublabel: "Part A — Short answers",
    emoji: "⚡",
    color: "#10B981",
    bg: "#D1FAE5",
    border: "#6EE7B7",
  },
  {
    marks: 6,
    label: "6 Mark Questions",
    sublabel: "Part B — Medium answers",
    emoji: "📝",
    color: "#F59E0B",
    bg: "#FEF3C7",
    border: "#FCD34D",
  },
  {
    marks: 10,
    label: "10 Mark Questions",
    sublabel: "Part C — Long answers",
    emoji: "📖",
    color: "#8B5CF6",
    bg: "#EDE9FE",
    border: "#C4B5FD",
  },
];

const PART_LABEL = {
  a_i:    "Part A(i)",
  a_ii:   "Part A(ii)",
  a:      "Part A",
  b:      "Part B",
  b_i:    "Part B",
  c_i:    "Part C — Either",
  c_ii:   "Part C — Or",
  generic:"General",
};

// ── Sub-components ────────────────────────────────────────────────────────────

function WelcomeScreen({ subject, unit, onOpenSidebar }) {
  if (!subject) {
    return (
      <div className="welcome-screen">
        <div className="welcome-icon">🎓</div>
        <h2>Sem 7 Study Assistant</h2>
        <p>Browse past exam questions for PSG College of Technology.</p>
        <div className="steps">
          <div className="step"><div className="step-num">1</div>Select a subject</div>
          <div className="step"><div className="step-num">2</div>Pick a unit (1–5)</div>
          <div className="step"><div className="step-num">3</div>Click 2M, 6M, or 10M button!</div>
        </div>
        <button className="mobile-cta-btn" onClick={onOpenSidebar}>
          📚 Choose Subject & Unit
        </button>
      </div>
    );
  }
  if (!unit) {
    return (
      <div className="welcome-screen">
        <div className="welcome-icon">{subject.icon}</div>
        <h2>{subject.shortName}</h2>
        <p>Now select a unit from 1 to 5 to view past exam questions.</p>
        <button className="mobile-cta-btn" onClick={onOpenSidebar}>
          📖 Choose Unit (1–5)
        </button>
      </div>
    );
  }
  return null;
}

function QuestionCard({ q, index, markColor }) {
  const [copied, setCopied] = useState(false);
  const partLabel = PART_LABEL[q.part] || q.part;

  const handleCopy = () => {
    navigator.clipboard?.writeText(q.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="question-card" style={{ borderLeftColor: markColor }}>
      <div className="question-num" style={{ color: markColor }}>Q{index + 1}</div>
      <div className="question-body">
        <div className="question-text">{q.text}</div>
        <div className="question-meta">
          <span className="q-badge" style={{ background: `${markColor}20`, color: markColor }}>
            {partLabel}
          </span>
          {q.is_either_or && (
            <span className="q-badge" style={{ background: "#F3F4F6", color: "#6B7280" }}>
              Either / Or
            </span>
          )}
          <button
            className="copy-card-btn"
            onClick={handleCopy}
            title="Copy question text"
            aria-label="Copy question text"
          >
            {copied ? <Check size={12} color="#059669" /> : <Copy size={12} />}
            <span>{copied ? "Copied" : "Copy"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}

function ResultsPanel({ result, onBack }) {
  const btnCfg = MARK_BUTTONS.find((b) => b.marks === result.marks);
  const markColor = btnCfg?.color || "#6B7280";

  return (
    <div className="results-panel">
      {/* Results header */}
      <div className="results-header" style={{ borderBottomColor: `${markColor}33` }}>
        <div>
          <div className="results-title" style={{ color: markColor }}>
            {btnCfg?.emoji} {btnCfg?.label}
          </div>
          <div className="results-sub">
            Unit {result.unit} · {result.count} question{result.count !== 1 ? "s" : ""} found
          </div>
        </div>
        <button className="back-btn" onClick={onBack} title="Back to mark selection">
          <RotateCcw size={14} /> Back
        </button>
      </div>

      {/* Questions list */}
      <div className="questions-list">
        {result.questions.length === 0 ? (
          <div className="empty-result">
            <Database size={32} style={{ opacity: 0.3, marginBottom: 12 }} />
            <p>No questions found for this unit.</p>
          </div>
        ) : (
          result.questions.map((q, i) => (
            <QuestionCard key={i} q={q} index={i} markColor={markColor} />
          ))
        )}
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function ChatArea({ selectedSubject, selectedUnit, onOpenSidebar }) {
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);
  const [result, setResult]     = useState(null); // null = show buttons
  const [activeMarks, setActiveMarks] = useState(null);
  const topRef = useRef(null);

  const subject = getSubject(selectedSubject);
  const canFetch = !!selectedSubject && !!selectedUnit;

  // Reset results when subject or unit changes
  useEffect(() => {
    setResult(null);
    setError(null);
    setActiveMarks(null);
  }, [selectedSubject, selectedUnit]);

  // Scroll to top when new results arrive
  useEffect(() => {
    if (result) topRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [result]);

  const handleMarkClick = async (marks) => {
    if (!canFetch || loading) return;

    setLoading(true);
    setError(null);
    setActiveMarks(marks);
    setResult(null);

    try {
      const data = await fetchQuestions({
        subject: selectedSubject,
        unit: selectedUnit,
        marks,
      });
      setResult(data);
    } catch (err) {
      setError(
        err?.response?.data?.detail || err?.message || "Backend not reachable. Is it running?"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-area">
      {/* Context bar */}
      <div className="context-bar">
        <div
          className="context-tags"
          onClick={onOpenSidebar}
          role="button"
          tabIndex={0}
          title="Tap to change subject or unit"
        >
          {subject ? (
            <span className="context-tag subject">{subject.icon} {subject.shortName}</span>
          ) : (
            <span className="context-tag empty">Select subject</span>
          )}
          {selectedUnit ? (
            <>
              <ChevronRight size={14} style={{ opacity: 0.4 }} />
              <span className="context-tag unit">📖 Unit {selectedUnit}</span>
            </>
          ) : (
            <span className="context-tag empty">Select unit</span>
          )}
        </div>
        <button
          className="context-change-btn"
          onClick={onOpenSidebar}
          title="Change subject or unit"
        >
          Change
        </button>
      </div>

      {/* Main content */}
      <div className="messages-container" ref={topRef}>

        {/* Show welcome if not ready */}
        {!canFetch && (
          <WelcomeScreen
            subject={subject}
            unit={selectedUnit}
            onOpenSidebar={onOpenSidebar}
          />
        )}

        {/* Show mark buttons when ready and no result yet */}
        {canFetch && !result && !loading && (
          <div className="mark-buttons-panel">
            <div className="mark-panel-title">
              <Bot size={18} style={{ marginRight: 8, opacity: 0.7 }} />
              Choose question type for <strong>{subject?.shortName} — Unit {selectedUnit}</strong>
            </div>

            <div className="mark-buttons-grid">
              {MARK_BUTTONS.map((btn) => (
                <button
                  key={btn.marks}
                  className="mark-big-btn"
                  style={{
                    background: btn.bg,
                    borderColor: btn.border,
                    color: btn.color,
                  }}
                  onClick={() => handleMarkClick(btn.marks)}
                  disabled={loading}
                >
                  <span className="mbtn-emoji">{btn.emoji}</span>
                  <span className="mbtn-label">{btn.label}</span>
                  <span className="mbtn-sub">{btn.sublabel}</span>
                </button>
              ))}
            </div>

            <div className="mark-hint">
              <Database size={12} /> All questions fetched directly from past papers
            </div>
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div className="mark-buttons-panel">
            <div className="mark-panel-title">Fetching questions…</div>
            <div className="mark-buttons-grid">
              {MARK_BUTTONS.map((btn) => {
                const active = btn.marks === activeMarks;
                return (
                  <button
                    key={btn.marks}
                    className="mark-big-btn"
                    style={{
                      background: active ? btn.bg : "#F9FAFB",
                      borderColor: active ? btn.border : "#E5E7EB",
                      color: active ? btn.color : "#9CA3AF",
                      opacity: active ? 1 : 0.5,
                    }}
                    disabled
                  >
                    <span className="mbtn-emoji">{active ? "⏳" : btn.emoji}</span>
                    <span className="mbtn-label">{btn.label}</span>
                    <span className="mbtn-sub">{active ? "Loading…" : btn.sublabel}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div style={{
            background: "#FEE2E2", color: "#DC2626",
            padding: "14px 18px", borderRadius: 12,
            fontSize: 13, margin: "20px auto", maxWidth: 480,
            textAlign: "center",
          }}>
            ⚠️ {error}
            <br />
            <button
              style={{
                marginTop: 10, fontSize: 12, color: "#DC2626",
                background: "transparent", border: "1px solid #DC2626",
                borderRadius: 8, padding: "4px 12px", cursor: "pointer",
              }}
              onClick={() => { setError(null); setActiveMarks(null); }}
            >
              Try again
            </button>
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <ResultsPanel
            result={result}
            onBack={() => { setResult(null); setActiveMarks(null); }}
          />
        )}
      </div>
    </div>
  );
}
