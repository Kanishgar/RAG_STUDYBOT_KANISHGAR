// App.jsx - Root component

import { useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatArea from "./components/ChatArea";
import "./index.css";

export default function App() {
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [selectedUnit, setSelectedUnit]       = useState(null);

  return (
    <div className="app-layout">
      {/* ── Top Bar ───────────────────────────────────── */}
      <header className="topbar">
        <div className="topbar-brand">
          <div className="logo-icon">🎓</div>
          <h1>StudyBot</h1>
          <span>Semester 7</span>
        </div>
        <div className="topbar-actions">
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Powered by Gemini + RAG
          </span>
        </div>
      </header>

      {/* ── Body ──────────────────────────────────────── */}
      <div className="main-content">
        <Sidebar
          selectedSubject={selectedSubject}
          selectedUnit={selectedUnit}
          onSubjectChange={setSelectedSubject}
          onUnitChange={setSelectedUnit}
        />
        <ChatArea
          selectedSubject={selectedSubject}
          selectedUnit={selectedUnit}
        />
      </div>
    </div>
  );
}
