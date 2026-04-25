import "./Navbar.css";

export default function Navbar({ page, setPage, hasReport }) {
  return (
    <nav className="navbar">
      <div className="nav-brand" onClick={() => setPage("dashboard")}>
        <span className="nav-logo">⚖</span>
        <div>
          <span className="nav-title">Fair Loan AI</span>
          <span className="nav-version">v2.0 RegTech</span>
        </div>
      </div>

      <div className="nav-links">
        <button
          className={`nav-link ${page === "dashboard" ? "active" : ""}`}
          onClick={() => setPage("dashboard")}
        >
          <span className="nav-link-icon">⌂</span> Dashboard
        </button>
        <button
          className={`nav-link ${page === "upload" ? "active" : ""}`}
          onClick={() => setPage("upload")}
        >
          <span className="nav-link-icon">↑</span> Upload Model
        </button>
        {hasReport && (
          <button
            className={`nav-link ${page === "report" ? "active" : ""}`}
            onClick={() => setPage("report")}
          >
            <span className="nav-link-icon">📊</span> Audit Report
            <span className="nav-dot" />
          </button>
        )}
      </div>

      <div className="nav-right">
        <a
          href="#"
          className="nav-api-badge"
          onClick={(e) => {
            e.preventDefault();
            window.open((import.meta.env.VITE_API_URL || "http://localhost:8000") + "/docs", "_blank");
          }}
        >
          <span>API Docs</span>
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
            <path d="M2 8L8 2M8 2H4M8 2V6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        </a>
        <div className="nav-rbi-badge">RBI Aligned</div>
      </div>
    </nav>
  );
}
