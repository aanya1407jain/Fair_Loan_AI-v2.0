import { useState, useRef } from "react";
import "./UploadPage.css";

export default function UploadPage({ setAuditReport, setPage, apiUrl }) {
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const inputRef = useRef();

  const handleFile = (f) => {
    if (!f) return;
    if (!f.name.endsWith(".pkl")) { setError("Only .pkl files are supported"); return; }
    setFile(f); setError(null);
  };

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true); setError(null); setProgress(10);

    const form = new FormData();
    form.append("file", file);

    try {
      setProgress(30);
      const res = await fetch(`${apiUrl}/api/upload-model`, { method: "POST", body: form });
      setProgress(80);
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setProgress(100);
      setAuditReport(data);
      setPage("report");
    } catch (e) {
      setError(e.message);
      setProgress(0);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-page">
      <div className="upload-header">
        <h1>Upload Your Model</h1>
        <p>Upload any scikit-learn compatible <code>.pkl</code> model to audit it for bias against 5,000 synthetic Indian loan applicants.</p>
      </div>

      <div className="upload-layout">
        {/* Drop Zone */}
        <div className="upload-panel">
          <div
            className={`drop-zone ${dragOver ? "drag-over" : ""} ${file ? "has-file" : ""}`}
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={e => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files[0]); }}
            onClick={() => inputRef.current.click()}
          >
            <input ref={inputRef} type="file" accept=".pkl" style={{ display: "none" }}
              onChange={e => handleFile(e.target.files[0])} />
            {file ? (
              <div className="file-selected">
                <div className="file-icon">📦</div>
                <div className="file-name">{file.name}</div>
                <div className="file-size">{(file.size / 1024).toFixed(1)} KB</div>
                <div className="file-ready">Ready to audit</div>
              </div>
            ) : (
              <div className="drop-hint">
                <div className="dh-icon">↑</div>
                <div className="dh-title">Drop your .pkl model here</div>
                <div className="dh-sub">or click to browse</div>
                <div className="dh-note">scikit-learn compatible · predict() or predict_proba()</div>
              </div>
            )}
          </div>

          {error && <div className="upload-error">⚠ {error}</div>}

          {loading && (
            <div className="upload-progress">
              <div className="up-bar">
                <div className="up-fill" style={{ width: `${progress}%` }} />
              </div>
              <div className="up-label">
                {progress < 30 ? "Uploading model…" : progress < 80 ? "Running bias audit…" : "Generating report…"}
              </div>
            </div>
          )}

          <div className="upload-actions">
            <button className="btn-primary" onClick={handleSubmit}
              disabled={!file || loading}>
              {loading ? "Auditing…" : "▶ Run Bias Audit"}
            </button>
            <button className="btn-secondary" onClick={() => { setFile(null); setError(null); }}>Clear</button>
          </div>
        </div>

        {/* Info panel */}
        <div className="upload-info">
          <h3>Model Requirements</h3>
          <div className="req-list">
            {REQUIREMENTS.map((r, i) => (
              <div key={i} className="req-item">
                <span className="req-icon">{r.icon}</span>
                <div><div className="req-title">{r.title}</div><div className="req-desc">{r.desc}</div></div>
              </div>
            ))}
          </div>

          <div className="upload-divider" />

          <h3>What Gets Audited</h3>
          <div className="audit-list">
            {AUDITS.map((a, i) => (
              <div key={i} className="audit-item">
                <span className="ai-check">✓</span>
                <span>{a}</span>
              </div>
            ))}
          </div>

          <div className="upload-divider" />

          <h3>No Real Data? Use Demo</h3>
          <p className="demo-note">Our built-in biased demo model is pre-trained on synthetic Indian banking data with intentional gender and city-tier discrimination — perfect for demonstrating audit capabilities.</p>
          <button className="btn-secondary" style={{ width: "100%", marginTop: "12px" }}
            onClick={async () => {
              setLoading(true);
              try {
                const res = await fetch(`${apiUrl}/api/demo-audit`);
                const data = await res.json();
                setAuditReport(data);
                setPage("report");
              } catch (e) { setError(e.message); }
              setLoading(false);
            }} disabled={loading}>
            ▶ Use Demo Model Instead
          </button>
        </div>
      </div>
    </div>
  );
}

const REQUIREMENTS = [
  { icon: "📦", title: "Format: .pkl", desc: "Pickle-serialized scikit-learn compatible model" },
  { icon: "🔧", title: "Interface", desc: "Must implement predict() or predict_proba()" },
  { icon: "📥", title: "Input Shape", desc: "Expects 7 numeric features (CIBIL, income, DTI, etc.)" },
  { icon: "📤", title: "Output", desc: "Binary classification (0 = reject, 1 = approve)" },
];

const AUDITS = [
  "Disparate Impact across Gender, Religion, City Tier",
  "Equal Opportunity & Equalized Odds",
  "Demographic Parity violation detection",
  "Proxy Variable identification via SHAP",
  "Model Integrity & data poisoning check",
  "Counterfactual individual fairness test",
  "Adversarial robustness scenarios",
  "RBI-ready PDF compliance report",
];
