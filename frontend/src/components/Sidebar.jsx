// Sidebar.jsx - Subject & Unit selector ONLY (read-only for users)
// PDFs are pre-ingested by admin via: python ingest.py

import { BookOpen } from "lucide-react";
import { SUBJECTS } from "../subjects";

export default function Sidebar({ selectedSubject, selectedUnit, onSubjectChange, onUnitChange }) {
  return (
    <aside className="sidebar">
      {/* Subject Selection */}
      <div className="sidebar-section">
        <h3>📚 Subject</h3>
        <div className="subject-grid">
          {SUBJECTS.map((subj) => (
            <button
              key={subj.id}
              className={`subject-card ${selectedSubject === subj.id ? "active" : ""}`}
              onClick={() => {
                onSubjectChange(subj.id);
                onUnitChange(null);
              }}
            >
              <div
                className="subj-icon"
                style={{ background: subj.bg, color: subj.color }}
              >
                {subj.icon}
              </div>
              <div className="subj-info">
                <div className="subj-name">{subj.shortName}</div>
                <div className="subj-sub">5 Units</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Unit Selection */}
      {selectedSubject && (
        <div className="sidebar-section">
          <h3>📖 Unit</h3>
          <div className="unit-pills">
            {[1, 2, 3, 4, 5].map((u) => (
              <button
                key={u}
                className={`unit-pill ${selectedUnit === u ? "active" : ""}`}
                onClick={() => onUnitChange(selectedUnit === u ? null : u)}
              >
                Unit {u}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Footer info */}
      <div className="sidebar-section" style={{ marginTop: "auto" }}>
        <div style={{ fontSize: 11, color: "var(--text-muted)", lineHeight: 1.8 }}>
          <BookOpen size={12} style={{ display: "inline", marginRight: 4 }} />
          <strong>Sem 7 Study Assistant</strong>
          <br />
          Powered by Gemini + RAG
          <br />
          <span style={{ opacity: 0.7 }}>Trained on your question papers</span>
        </div>
      </div>
    </aside>
  );
}
