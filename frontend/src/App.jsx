import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import UploadPage from "./pages/UploadPage";
import ReportPage from "./pages/ReportPage";
import Navbar from "./components/Navbar";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [auditReport, setAuditReport] = useState(null);
  const [loading, setLoading] = useState(false);

  const runDemoAudit = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/demo-audit`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setAuditReport(data);
      setPage("report");
    } catch (e) {
      alert("Backend unreachable. Check your VITE_API_URL environment variable.\n\n" + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <Navbar page={page} setPage={setPage} hasReport={!!auditReport} />
      {page === "dashboard" && (
        <Dashboard onRunDemo={runDemoAudit} loading={loading} />
      )}
      {page === "upload" && (
        <UploadPage setAuditReport={setAuditReport} setPage={setPage} apiUrl={API_URL} />
      )}
      {page === "report" && auditReport && (
        <ReportPage report={auditReport} apiUrl={API_URL} />
      )}
      {page === "report" && !auditReport && (
        <div className="empty-state">
          <div className="empty-icon">📊</div>
          <h2>No Audit Report Yet</h2>
          <p>Run a demo audit or upload a model to see results</p>
          <div className="empty-actions">
            <button className="btn-primary" onClick={runDemoAudit} disabled={loading}>
              {loading ? "Running…" : "▶ Run Demo Audit"}
            </button>
            <button className="btn-secondary" onClick={() => setPage("upload")}>
              ↑ Upload Model
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
