// App.jsx - Root component with mobile responsive navigation

import { useState } from "react";
import { Menu, X } from "lucide-react";
import Sidebar from "./components/Sidebar";
import ChatArea from "./components/ChatArea";
import "./index.css";

export default function App() {
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [selectedUnit, setSelectedUnit]       = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen]   = useState(false);

  return (
    <div className="app-layout">
      {/* ── Top Bar ───────────────────────────────────── */}
      <header className="topbar">
        <div className="topbar-left">
          <button
            className="mobile-toggle-btn"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div className="topbar-brand">
            <div className="logo-icon">🎓</div>
            <h1>StudyBot</h1>
            <span className="badge-sem">Sem 7</span>
          </div>
        </div>

        <div className="topbar-actions">
          {/* Topbar right side kept clean per request */}
        </div>
      </header>

      {/* ── Mobile Backdrop Overlay ──────────────────── */}
      {mobileMenuOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* ── Body ──────────────────────────────────────── */}
      <div className="main-content">
        <Sidebar
          selectedSubject={selectedSubject}
          selectedUnit={selectedUnit}
          onSubjectChange={setSelectedSubject}
          onUnitChange={setSelectedUnit}
          isOpen={mobileMenuOpen}
          onClose={() => setMobileMenuOpen(false)}
        />
        <ChatArea
          selectedSubject={selectedSubject}
          selectedUnit={selectedUnit}
          onOpenSidebar={() => setMobileMenuOpen(true)}
        />
      </div>

      {/* ── Floating Watermark Badge ────────────────── */}
      <div className="floating-dev-badge" title="Developed by Kanishgar">
        <span className="dev-badge-pulse"></span>
        <span className="dev-badge-text">
          ⚡ Developed by <span className="dev-badge-name">Kanishgar</span>
        </span>
      </div>
    </div>
  );
}
