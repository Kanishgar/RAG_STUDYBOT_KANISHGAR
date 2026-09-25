// Sidebar.jsx - Subject & Unit selector with mobile drawer support

import { BookOpen, X } from "lucide-react";
import { SUBJECTS } from "../subjects";

export default function Sidebar({
  selectedSubject,
  selectedUnit,
  onSubjectChange,
  onUnitChange,
  isOpen = false,
  onClose,
}) {
  return (
    <aside className={`sidebar ${isOpen ? "open" : ""}`}>
      {/* Mobile Drawer Header */}
      <div className="sidebar-mobile-header">
        <div className="smh-title">
          <span>📚 Choose Subject & Unit</span>
        </div>
        {onClose && (
          <button
            className="sidebar-close-btn"
            onClick={onClose}
            aria-label="Close sidebar"
          >
            <X size={18} />
          </button>
        )}
      </div>

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
                onClick={() => {
                  const nextUnit = selectedUnit === u ? null : u;
                  onUnitChange(nextUnit);
                  if (nextUnit && onClose) {
                    onClose();
                  }
                }}
              >
                Unit {u}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Footer info */}
      <div className="sidebar-section sidebar-footer">
        <div style={{ fontSize: 11, color: "var(--text-muted)", lineHeight: 1.8 }}>
          <BookOpen size={12} style={{ display: "inline", marginRight: 4 }} />
          <strong>Sem 7 Study Assistant</strong>
          <br />
          PSG College of Technology
          <br />
          <span style={{ opacity: 0.7 }}>2M, 6M & 10M Past Exam Qns</span>
        </div>
      </div>
    </aside>
  );
}
