import { useState, useEffect } from "react";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Cell, ReferenceLine, Legend
} from "recharts";
import "./ReportPage.css";

const RISK_COLORS = {
  CRITICAL: "#e94560", HIGH: "#f97316",
  MEDIUM: "#fbbf24", LOW: "#06d6a0",
  MINIMAL: "#06d6a0", PASS: "#06d6a0",
};

export default function ReportPage({ report, apiUrl }) {
  const [activeTab, setActiveTab] = useState("overview");
  const [mitigation, setMitigation] = useState(null);
  const [mitigationLoading, setMitigationLoading] = useState(false);
  const [tradeoffData, setTradeoffData] = useState(null);
  const [shapData, setShapData] = useState(null);
  const [adversarialData, setAdversarialData] = useState(null);
  const [counterfactualData, setCounterfactualData] = useState(null);
  const [rejectedApps, setRejectedApps] = useState([]);
  const [selectedApp, setSelectedApp] = useState(null);
  const [cfAttribute, setCfAttribute] = useState("gender");
  const [cfValue, setCfValue] = useState("Male");
  const [cfLoading, setCfLoading] = useState(false);
  const [reviewQueue, setReviewQueue] = useState([]);
  const [reviewLoading, setReviewLoading] = useState(false);

  const BASE = apiUrl || "http://localhost:8000";
  const AID = report.audit_id;

  useEffect(() => {
    if (activeTab === "mitigation" && !tradeoffData) {
      fetch(`${BASE}/api/tradeoff-curve/${AID}`)
        .then(r => r.json()).then(d => setTradeoffData(d.tradeoff_curve))
        .catch(() => {});
    }
    if (activeTab === "explain" && !shapData) {
      fetch(`${BASE}/api/shap/${AID}`)
        .then(r => r.json()).then(setShapData)
        .catch(() => {});
      fetch(`${BASE}/api/rejected-applications/${AID}?limit=20`)
        .then(r => r.json()).then(d => setRejectedApps(d.rejected_applications || []))
        .catch(() => {});
    }
    if (activeTab === "adversarial" && !adversarialData) {
      fetch(`${BASE}/api/adversarial/${AID}`)
        .then(r => r.json()).then(setAdversarialData)
        .catch(() => {});
    }
    if (activeTab === "review" && !reviewQueue.length) {
      setReviewLoading(true);
      fetch(`${BASE}/api/manual-review-queue/${AID}?limit=10`)
        .then(r => r.json()).then(d => { setReviewQueue(d.queue || []); setReviewLoading(false); })
        .catch(() => setReviewLoading(false));
    }
  }, [activeTab]);

  const runMitigation = async (attr) => {
    setMitigationLoading(true);
    try {
      const r = await fetch(`${BASE}/api/mitigation/${AID}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sensitive_attr: attr, constraint: "demographic_parity" }),
      });
      const d = await r.json();
      setMitigation(d);
    } catch (e) {}
    setMitigationLoading(false);
  };

  const runCounterfactual = async () => {
    if (!selectedApp) return;
    setCfLoading(true);
    try {
      const r = await fetch(`${BASE}/api/counterfactual`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          applicant_index: selectedApp.index,
          change_attribute: cfAttribute,
          change_to: cfValue,
          audit_id: AID,
        }),
      });
      const d = await r.json();
      setCounterfactualData(d);
    } catch (e) {}
    setCfLoading(false);
  };

  const handleExportPDF = () => {
    window.open(`${BASE}/api/export-pdf/${AID}`, "_blank");
  };
  const handleExportJSON = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url;
    a.download = `audit_${AID}.json`; a.click();
  };

  const riskColor = RISK_COLORS[report.risk_level] || "#64748b";

  const TABS = [
    { id: "overview", label: "Overview", icon: "⌂" },
    { id: "heatmap", label: "Bias Heatmap", icon: "🔥" },
    { id: "mitigation", label: "Mitigation Engine", icon: "🛠" },
    { id: "explain", label: "Counterfactual", icon: "🔮" },
    { id: "adversarial", label: "Adversarial", icon: "⚔" },
    { id: "integrity", label: "Model Integrity", icon: "🛡" },
    { id: "review", label: "Human Review", icon: "👤" },
  ];

  return (
    <div className="report-page">
      {/* Report Header */}
      <div className="report-header">
        <div className="report-meta">
          <div className="report-id-wrap">
            <span className="report-id-label">AUDIT</span>
            <span className="report-id">#{report.audit_id}</span>
          </div>
          <div className="report-info">
            <span>{report.timestamp?.slice(0, 10)}</span>
            <span className="dot">·</span>
            <span>{report.dataset?.total_samples?.toLocaleString()} samples</span>
            <span className="dot">·</span>
            <span>{report.model_type?.replace("_", " ").toUpperCase()}</span>
          </div>
        </div>
        <div className="report-risk">
          <div className="risk-score-wrap">
            <span className="risk-number" style={{ color: riskColor }}>{report.risk_score}</span>
            <span className="risk-denom">/100</span>
          </div>
          <div className="risk-label-col">
            <span className={`badge badge-${report.risk_level?.toLowerCase()}`}>{report.risk_level} RISK</span>
            <span className={`rbi-status ${report.rbi_compliant ? "pass" : "fail"}`}>
              {report.rbi_compliant ? "✓ RBI Compliant" : "✗ Non-Compliant"}
            </span>
          </div>
        </div>
        <div className="report-actions">
          <button className="btn-secondary" onClick={handleExportJSON}>↓ JSON</button>
          <button className="btn-primary" onClick={handleExportPDF}>📄 RBI PDF Report</button>
        </div>
      </div>

      {/* Risk Gauge Bar */}
      <div className="risk-gauge-bar">
        <div className="gauge-track">
          <div className="gauge-fill" style={{ width: `${report.risk_score}%`, background: riskColor }} />
        </div>
        <div className="gauge-labels">
          {["PASS", "LOW", "MEDIUM", "HIGH", "CRITICAL"].map((l, i) => (
            <span key={l} style={{ left: `${i * 25}%` }}>{l}</span>
          ))}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="report-tabs">
        <div className="tab-bar">
          {TABS.map(t => (
            <button key={t.id} className={`tab ${activeTab === t.id ? "active" : ""}`} onClick={() => setActiveTab(t.id)}>
              <span>{t.icon}</span> {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="report-body">

        {/* ── OVERVIEW TAB ── */}
        {activeTab === "overview" && (
          <div className="tab-content">
            {/* Model Performance */}
            <div className="section-block">
              <h3 className="section-h">Model Performance Metrics</h3>
              <div className="metrics-grid">
                {Object.entries(report.overall_metrics || {}).slice(0, 6).map(([k, v]) => (
                  <div key={k} className="metric-card">
                    <div className="mc-key">{k.replace(/_/g, " ").toUpperCase()}</div>
                    <div className="mc-val">
                      {typeof v === "number" && v <= 1 && !["total_samples","total_approved","total_rejected"].includes(k)
                        ? (v * 100).toFixed(1) + "%"
                        : v.toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Bias Summary Cards */}
            <div className="section-block">
              <h3 className="section-h">Bias Analysis Summary</h3>
              <div className="bias-summary-grid">
                {Object.entries(report.bias_analysis || {}).map(([attr, data]) => {
                  const sev = data.severity;
                  const di = data.disparate_impact || {};
                  const minDI = Math.min(...Object.values(di).map(v => v.di_ratio || 1));
                  return (
                    <div key={attr} className={`bias-attr-card sev-${sev.toLowerCase()}`}>
                      <div className="bac-header">
                        <span className="bac-attr">{attr.replace("_", " ").toUpperCase()}</span>
                        <span className={`badge badge-${sev.toLowerCase()}`}>{sev}</span>
                      </div>
                      <div className="bac-di">
                        Min DI Ratio: <strong style={{ color: minDI < 0.8 ? "#e94560" : "#06d6a0" }}>
                          {minDI.toFixed(3)}
                        </strong>
                        <span className="bac-threshold"> (threshold: 0.800)</span>
                      </div>
                      <div className="bac-summary">{data.summary}</div>
                      <div className="bac-groups">
                        {Object.entries(di).map(([g, v]) => (
                          <div key={g} className="bac-group-row">
                            <span className="bcg-name">{g}</span>
                            <div className="bcg-bar-wrap">
                              <div className="bcg-bar" style={{
                                width: `${v.approval_rate * 100}%`,
                                background: v.flagged ? "#e94560" : "#06d6a0"
                              }} />
                            </div>
                            <span className="bcg-val">{(v.approval_rate * 100).toFixed(1)}%</span>
                            {v.flagged && <span className="bcg-flag">⚠</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Intersectional */}
            <div className="section-block">
              <h3 className="section-h">Intersectional Analysis — Gender × City Tier</h3>
              <div className="intersect-grid">
                {(report.intersectional || []).map((row, i) => (
                  <div key={i} className="intersect-card">
                    <div className="ic-label">{row.gender} · Tier {row.city_tier}</div>
                    <div className="ic-bar-wrap">
                      <div className="ic-bar" style={{
                        width: `${row.approval_rate * 100}%`,
                        background: row.approval_rate < 0.45 ? "var(--accent-red)" : row.approval_rate < 0.55 ? "var(--accent-yellow)" : "var(--accent-green)"
                      }} />
                    </div>
                    <div className="ic-stats">
                      <span>{(row.approval_rate * 100).toFixed(1)}%</span>
                      <span className="ic-n">n={row.count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Regulatory Notes */}
            <div className="section-block">
              <h3 className="section-h">Regulatory Notes</h3>
              <div className="reg-notes">
                {(report.regulatory_notes || []).map((note, i) => (
                  <div key={i} className={`reg-note ${note.startsWith("CRITICAL") ? "reg-critical" : ""}`}>
                    <span className="reg-icon">{note.startsWith("CRITICAL") ? "⚠" : "ℹ"}</span>
                    {note}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── HEATMAP TAB ── */}
        {activeTab === "heatmap" && (
          <div className="tab-content">
            <div className="section-block">
              <div className="section-h-row">
                <h3 className="section-h">Disparate Impact Heatmap</h3>
                <span className="section-note">Red = DI &lt; 0.80 (violation) · Green = DI ≥ 0.80 (pass)</span>
              </div>
              <DisparateImpactHeatmap biasAnalysis={report.bias_analysis} />
            </div>

            {/* Radar chart */}
            <div className="section-block">
              <h3 className="section-h">Fairness Radar — Metric Comparison by Attribute</h3>
              <FairnessRadar biasAnalysis={report.bias_analysis} />
            </div>

            {/* Mitigation suggestions */}
            <div className="section-block">
              <h3 className="section-h">Mitigation Recommendations</h3>
              <div className="mitigations">
                {(report.mitigation_suggestions || []).map((m, i) => (
                  <div key={i} className={`mit-card mit-${m.priority.toLowerCase()}`}>
                    <div className="mit-top">
                      <span className={`badge badge-${m.priority === "HIGH" ? "critical" : m.priority.toLowerCase()}`}>{m.priority}</span>
                      <span className="mit-technique">{m.technique}</span>
                      <span className="mit-attr">{m.attribute.toUpperCase()}</span>
                    </div>
                    <p className="mit-desc">{m.description}</p>
                    {m.fairlearn_api && <code className="mit-api">{m.fairlearn_api}</code>}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── MITIGATION TAB ── */}
        {activeTab === "mitigation" && (
          <div className="tab-content">
            <div className="section-block">
              <div className="section-h-row">
                <h3 className="section-h">Mitigation Engine — ThresholdOptimizer</h3>
                <div className="mit-controls">
                  {["gender", "city_tier", "religion"].map(attr => (
                    <button key={attr} className="btn-secondary btn-sm"
                      onClick={() => runMitigation(attr)} disabled={mitigationLoading}>
                      Apply to {attr.replace("_", " ")}
                    </button>
                  ))}
                </div>
              </div>
              {mitigationLoading && <div className="loading-pulse">Running ThresholdOptimizer…</div>}
              {mitigation && <MitigationComparison data={mitigation} />}
              {!mitigation && !mitigationLoading && (
                <div className="empty-panel">
                  <div className="ep-icon">🛠</div>
                  <p>Select an attribute above to apply <strong>ThresholdOptimizer</strong> post-processing.</p>
                  <p className="ep-sub">Shows before/after comparison of disparate impact vs accuracy.</p>
                </div>
              )}
            </div>

            <div className="section-block">
              <h3 className="section-h">Accuracy vs Fairness — Pareto Frontier</h3>
              {tradeoffData ? (
                <TradeoffCurve data={tradeoffData} />
              ) : (
                <div className="loading-pulse">Loading Pareto curve…</div>
              )}
            </div>
          </div>
        )}

        {/* ── COUNTERFACTUAL TAB ── */}
        {activeTab === "explain" && (
          <div className="tab-content">
            <div className="section-block">
              <h3 className="section-h">SHAP Feature Attribution — What Drives Rejections?</h3>
              {shapData ? <ShapWaterfall data={shapData} /> : <div className="loading-pulse">Computing SHAP values…</div>}
            </div>

            <div className="section-block">
              <div className="section-h-row">
                <h3 className="section-h">Counterfactual What-If Analysis</h3>
                <span className="section-note">Individual Fairness Test</span>
              </div>
              <div className="cf-layout">
                <div className="cf-selector">
                  <div className="cf-label">1. Select a rejected application</div>
                  <div className="cf-app-list">
                    {rejectedApps.slice(0, 10).map(app => (
                      <button key={app.index} className={`cf-app-item ${selectedApp?.index === app.index ? "selected" : ""}`}
                        onClick={() => setSelectedApp(app)}>
                        <span className="cfa-id">{app.applicant_id}</span>
                        <span className="cfa-details">{app.gender} · Tier {app.city_tier} · CIBIL {app.cibil_score}</span>
                      </button>
                    ))}
                  </div>
                </div>
                <div className="cf-controls">
                  <div className="cf-label">2. Change one attribute</div>
                  <div className="cf-row">
                    <select className="cf-select" value={cfAttribute} onChange={e => { setCfAttribute(e.target.value); setCounterfactualData(null); }}>
                      <option value="gender">Gender</option>
                      <option value="religion">Religion</option>
                      <option value="city_tier">City Tier</option>
                    </select>
                    <span className="cf-arrow">→</span>
                    <select className="cf-select" value={cfValue} onChange={e => setCfValue(e.target.value)}>
                      {CF_OPTIONS[cfAttribute]?.map(v => (
                        <option key={v} value={v}>{String(v)}</option>
                      ))}
                    </select>
                  </div>
                  <button className="btn-primary" onClick={runCounterfactual}
                    disabled={!selectedApp || cfLoading}>
                    {cfLoading ? "Analyzing…" : "Run What-If Analysis"}
                  </button>
                </div>
              </div>
              {counterfactualData && <CounterfactualResult data={counterfactualData} />}
            </div>
          </div>
        )}

        {/* ── ADVERSARIAL TAB ── */}
        {activeTab === "adversarial" && (
          <div className="tab-content">
            <div className="section-block">
              <h3 className="section-h">Adversarial Robustness Assessment</h3>
              {adversarialData ? <AdversarialReport data={adversarialData} /> : <div className="loading-pulse">Running adversarial tests…</div>}
            </div>
          </div>
        )}

        {/* ── INTEGRITY TAB ── */}
        {activeTab === "integrity" && (
          <div className="tab-content">
            <div className="section-block">
              <h3 className="section-h">Model Integrity & Data Poisoning Check</h3>
              {report.model_integrity ? (
                <IntegrityReport data={report.model_integrity} />
              ) : (
                <div className="empty-panel">
                  <div className="ep-icon">🛡</div>
                  <p>Model integrity data not available. Run a fresh audit to compute integrity scores.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── HUMAN REVIEW TAB ── */}
        {activeTab === "review" && (
          <div className="tab-content">
            <div className="section-block">
              <div className="section-h-row">
                <h3 className="section-h">Human-in-the-Loop Review Queue</h3>
                <span className="section-note">Borderline bias cases flagged for officer review</span>
              </div>
              {reviewLoading && <div className="loading-pulse">Loading review queue…</div>}
              {!reviewLoading && <ReviewQueue queue={reviewQueue} />}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const CF_OPTIONS = {
  gender: ["Male", "Female", "Other"],
  religion: ["Hindu", "Muslim", "Christian", "Sikh", "Buddhist"],
  city_tier: [1, 2, 3],
};

// ══════════════════════════════════════════════════
// SUB-COMPONENTS
// ══════════════════════════════════════════════════

function DisparateImpactHeatmap({ biasAnalysis }) {
  if (!biasAnalysis) return null;
  const attrs = Object.keys(biasAnalysis);

  return (
    <div className="heatmap-container">
      <div className="heatmap-legend">
        <div className="hm-legend-bar" />
        <div className="hm-legend-labels">
          <span>DI = 0.0 (Critical)</span>
          <span>DI = 0.8 (Threshold)</span>
          <span>DI = 1.0+ (Ideal)</span>
        </div>
      </div>
      <div className="heatmap-grid">
        {attrs.map(attr => {
          const di = biasAnalysis[attr].disparate_impact || {};
          return (
            <div key={attr} className="hm-row">
              <div className="hm-attr-label">{attr.replace("_", " ").toUpperCase()}</div>
              <div className="hm-cells">
                {Object.entries(di).map(([group, val]) => {
                  const ratio = val.di_ratio;
                  const hue = Math.min(ratio / 1.0, 1);
                  const r = Math.round(233 * (1 - hue) + 6 * hue);
                  const g = Math.round(69 * (1 - hue) + 214 * hue);
                  const b = Math.round(96 * (1 - hue) + 0 * hue);
                  const bg = `rgb(${r},${g},${b})`;
                  return (
                    <div key={group} className="hm-cell" style={{ background: bg + "33", borderColor: bg + "88" }}>
                      <div className="hmc-group">{group}</div>
                      <div className="hmc-ratio" style={{ color: bg }}>{ratio.toFixed(3)}</div>
                      <div className="hmc-rate">{(val.approval_rate * 100).toFixed(1)}%</div>
                      {val.flagged && <div className="hmc-flag">⚠ FLAGGED</div>}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function FairnessRadar({ biasAnalysis }) {
  if (!biasAnalysis) return null;
  const attrs = Object.keys(biasAnalysis);
  const data = attrs.map(attr => {
    const di = biasAnalysis[attr].disparate_impact || {};
    const minDI = Math.min(...Object.values(di).map(v => v.di_ratio));
    const dp = biasAnalysis[attr].demographic_parity || {};
    const maxDPD = Math.max(...Object.values(dp).map(v => Math.abs(v.dpd || 0)));
    return {
      attr: attr.replace("_", " ").toUpperCase(),
      "DI Score": Math.round(Math.min(minDI / 0.8, 1) * 100),
      "DP Score": Math.round(Math.max(0, 1 - maxDPD * 10) * 100),
      "Pass Rate": biasAnalysis[attr].severity === "PASS" ? 100 : biasAnalysis[attr].severity === "LOW" ? 80 : 40,
    };
  });

  return (
    <ResponsiveContainer width="100%" height={300}>
      <RadarChart data={data}>
        <PolarGrid stroke="#1e3a5f" />
        <PolarAngleAxis dataKey="attr" tick={{ fill: "#94a3b8", fontSize: 12 }} />
        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: "#475569", fontSize: 10 }} />
        <Radar name="DI Score" dataKey="DI Score" stroke="#e94560" fill="#e94560" fillOpacity={0.2} strokeWidth={2} />
        <Radar name="DP Score" dataKey="DP Score" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} strokeWidth={2} />
        <Legend wrapperStyle={{ color: "#94a3b8", fontSize: 12 }} />
        <Tooltip contentStyle={{ background: "#0d1525", border: "1px solid #1e3a5f", borderRadius: 8, color: "#f1f5f9" }} />
      </RadarChart>
    </ResponsiveContainer>
  );
}

function MitigationComparison({ data }) {
  const { before, after, improvements, accuracy_cost, sensitive_attr, group_thresholds } = data;
  const beforeGroups = Object.entries(before.groups || {});
  const afterGroups = Object.entries(after.groups || {});

  const chartData = beforeGroups.map(([group, bv]) => ({
    group,
    before: Math.round(bv.approval_rate * 100),
    after: Math.round((after.groups[group]?.approval_rate || 0) * 100),
    di_before: bv.di_ratio,
    di_after: after.groups[group]?.di_ratio || 0,
  }));

  return (
    <div className="mitigation-result">
      <div className="mit-summary-cards">
        <div className="mit-sum-card">
          <div className="msc-label">Accuracy Cost</div>
          <div className="msc-val" style={{ color: Math.abs(accuracy_cost) > 0.02 ? "#fbbf24" : "#06d6a0" }}>
            {accuracy_cost > 0 ? "+" : ""}{(accuracy_cost * 100).toFixed(2)}%
          </div>
        </div>
        <div className="mit-sum-card">
          <div className="msc-label">Groups Fixed</div>
          <div className="msc-val" style={{ color: "#06d6a0" }}>{improvements.length}</div>
        </div>
        <div className="mit-sum-card">
          <div className="msc-label">Min DI Before</div>
          <div className="msc-val" style={{ color: before.min_di_ratio < 0.8 ? "#e94560" : "#06d6a0" }}>
            {before.min_di_ratio?.toFixed(3)}
          </div>
        </div>
        <div className="mit-sum-card">
          <div className="msc-label">Min DI After</div>
          <div className="msc-val" style={{ color: after.min_di_ratio >= 0.8 ? "#06d6a0" : "#fbbf24" }}>
            {after.min_di_ratio?.toFixed(3)}
          </div>
        </div>
      </div>

      <div className="mit-chart-label">Before vs After — Approval Rates by Group ({sensitive_attr})</div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={chartData} barGap={4} margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="group" tick={{ fill: "#94a3b8", fontSize: 12 }} />
          <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} tickFormatter={v => `${v}%`} />
          <Tooltip contentStyle={{ background: "#0d1525", border: "1px solid #1e3a5f", borderRadius: 8, color: "#f1f5f9" }} formatter={v => `${v}%`} />
          <ReferenceLine y={80} stroke="#e9456066" strokeDasharray="4 4" label={{ value: "80% threshold", fill: "#e94560", fontSize: 11 }} />
          <Bar dataKey="before" name="Before" fill="#e9456066" stroke="#e94560" strokeWidth={1} radius={[4,4,0,0]} />
          <Bar dataKey="after" name="After" fill="#06d6a066" stroke="#06d6a0" strokeWidth={1} radius={[4,4,0,0]} />
          <Legend wrapperStyle={{ color: "#94a3b8", fontSize: 12 }} />
        </BarChart>
      </ResponsiveContainer>

      <div className="mit-thresholds">
        <div className="mt-label">Applied Thresholds</div>
        <div className="mt-chips">
          {Object.entries(group_thresholds || {}).map(([g, t]) => (
            <div key={g} className="mt-chip">
              <span>{g}</span>
              <code>{typeof t === "number" ? t.toFixed(3) : t}</code>
            </div>
          ))}
        </div>
      </div>
      <div className="mit-api-note">
        API: <code>{data.fairlearn_api}</code>
      </div>
    </div>
  );
}

function TradeoffCurve({ data }) {
  const chartData = data.map(p => ({
    accuracy: Math.round(p.accuracy * 1000) / 10,
    fairness: Math.round(p.min_di_ratio * 1000) / 10,
    passes: p.passes_80_rule,
    fw: p.fairness_weight,
  }));

  return (
    <div className="tradeoff-container">
      <div className="tradeoff-note">
        Each point represents a different fairness constraint level. Points above the 80% fairness line pass the 4/5ths rule.
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart margin={{ top: 20, right: 30, bottom: 30, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="accuracy" name="Accuracy" unit="%" tick={{ fill: "#94a3b8", fontSize: 11 }}
            label={{ value: "Accuracy (%)", position: "insideBottom", fill: "#64748b", fontSize: 12, offset: -10 }} />
          <YAxis dataKey="fairness" name="Min DI Ratio" unit="%" tick={{ fill: "#94a3b8", fontSize: 11 }}
            label={{ value: "Min DI Ratio (%)", angle: -90, position: "insideLeft", fill: "#64748b", fontSize: 12 }} />
          <ReferenceLine y={80} stroke="#06d6a066" strokeDasharray="4 4"
            label={{ value: "80% Fairness Threshold", fill: "#06d6a0", fontSize: 11 }} />
          <Tooltip cursor={{ strokeDasharray: "3 3" }} contentStyle={{ background: "#0d1525", border: "1px solid #1e3a5f", borderRadius: 8, color: "#f1f5f9", fontSize: 12 }}
            formatter={(v, n) => [`${v}%`, n]} />
          <Scatter data={chartData.filter(d => !d.passes)} name="Fails 80% Rule" fill="#e94560" fillOpacity={0.8} />
          <Scatter data={chartData.filter(d => d.passes)} name="Passes 80% Rule" fill="#06d6a0" fillOpacity={0.8} />
          <Legend wrapperStyle={{ color: "#94a3b8", fontSize: 12 }} />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

function ShapWaterfall({ data }) {
  const global = data.global_importance || [];
  const sample = data.waterfall_samples?.[0];

  return (
    <div className="shap-container">
      <div className="shap-global">
        <div className="shap-col-title">Global Feature Importance</div>
        <div className="shap-bars">
          {global.map((f, i) => (
            <div key={f.feature} className="shap-row">
              <div className="shap-feat">{f.label}</div>
              <div className="shap-bar-wrap">
                <div className="shap-bar" style={{
                  width: `${f.importance * 100 * 3.5}%`,
                  background: f.direction > 0 ? "#06d6a066" : "#e9456066",
                  borderRight: `2px solid ${f.direction > 0 ? "#06d6a0" : "#e94560"}`,
                }} />
              </div>
              <span className="shap-imp">{(f.importance * 100).toFixed(1)}%</span>
              <span className="shap-rank">#{f.rank}</span>
            </div>
          ))}
        </div>
      </div>

      {sample && (
        <div className="shap-waterfall">
          <div className="shap-col-title">Rejection Explanation — {sample.applicant_id}</div>
          <div className="wf-bars">
            {sample.shap_values.slice(0, 7).map((sv, i) => (
              <div key={sv.feature} className="wf-row">
                <div className="wf-feat">{sv.label}</div>
                <div className="wf-val-raw">= {typeof sv.value === "number" ? sv.value.toLocaleString() : sv.value}</div>
                <div className="wf-bar-outer">
                  <div className="wf-bar" style={{
                    width: `${Math.min(Math.abs(sv.shap_value) * 400, 100)}%`,
                    background: sv.direction === "negative" ? "#e9456066" : "#06d6a066",
                    borderRight: `2px solid ${sv.direction === "negative" ? "#e94560" : "#06d6a0"}`,
                    marginLeft: sv.direction === "positive" ? 0 : "auto",
                  }} />
                </div>
                <span className="wf-shap" style={{ color: sv.direction === "negative" ? "#e94560" : "#06d6a0" }}>
                  {sv.shap_value > 0 ? "+" : ""}{sv.shap_value.toFixed(3)}
                </span>
              </div>
            ))}
          </div>
          <div className="wf-note">
            Top rejection driver: <strong>{sample.top_rejection_reason}</strong>
          </div>
        </div>
      )}

      <div className="shap-proxy-note">
        <span className="pn-icon">⚠</span>
        {data.interpretation}
      </div>
    </div>
  );
}

function CounterfactualResult({ data }) {
  const flipped = data.decision_flipped;
  return (
    <div className={`cf-result ${flipped ? "cf-flipped" : "cf-same"}`}>
      <div className="cfr-header">
        <div className="cfr-decisions">
          <div className="cfr-decision">
            <div className="cfrd-label">Original Decision</div>
            <div className={`cfrd-val ${data.original_decision === "REJECTED" ? "rejected" : "approved"}`}>
              {data.original_decision}
            </div>
            <div className="cfrd-score">Score: {data.original_score?.toFixed(1)}</div>
          </div>
          <div className="cfr-arrow">{flipped ? "🔄 FLIPPED" : "→ NO CHANGE"}</div>
          <div className="cfr-decision">
            <div className="cfrd-label">New Decision ({data.change_attribute} → {data.new_value})</div>
            <div className={`cfrd-val ${data.new_decision === "REJECTED" ? "rejected" : "approved"}`}>
              {data.new_decision}
            </div>
            <div className="cfrd-score">Score: {data.new_score?.toFixed(1)} ({data.score_delta > 0 ? "+" : ""}{data.score_delta})</div>
          </div>
        </div>
        {flipped && data.individual_fairness_violation && (
          <div className="cfr-violation">
            ⚠ INDIVIDUAL FAIRNESS VIOLATION — Decision depends on a protected attribute
          </div>
        )}
      </div>
      {data.proxy_warning && (
        <div className="cfr-proxy">{data.proxy_warning}</div>
      )}
      <div className="cfr-interpretation">{data.interpretation}</div>
    </div>
  );
}

function AdversarialReport({ data }) {
  const vulnColors = { CRITICAL: "#e94560", HIGH: "#f97316", MEDIUM: "#fbbf24", LOW: "#06d6a0" };
  const vc = vulnColors[data.vulnerability_level] || "#64748b";

  return (
    <div className="adv-report">
      <div className="adv-summary">
        <div className="adv-level" style={{ color: vc, borderColor: vc + "44", background: vc + "11" }}>
          {data.vulnerability_level}
        </div>
        <div className="adv-desc">{data.vulnerability_description}</div>
      </div>

      <div className="adv-scenarios">
        {(data.attack_scenarios || []).map((s, i) => (
          <div key={i} className="adv-card">
            <div className="advc-header">
              <span className="advc-name">{s.attack}</span>
              <span className="advc-desc">{s.description}</span>
            </div>
            <div className="advc-stats">
              <span>Original approvals: <strong>{s.original_approvals}</strong></span>
              <span>After attack: <strong style={{ color: s.additional_approvals > 0 ? "#e94560" : "#06d6a0" }}>
                {s.approvals_after_attack}
              </strong></span>
              <span>Flip rate: <strong style={{ color: s.flip_rate > 0.1 ? "#e94560" : "#06d6a0" }}>
                {(s.flip_rate * 100).toFixed(1)}%
              </strong></span>
            </div>
            <div className="advc-bar-wrap">
              <div className="advc-bar" style={{
                width: `${Math.min(s.flip_rate * 5 * 100, 100)}%`,
                background: s.flip_rate > 0.2 ? "#e9456066" : s.flip_rate > 0.1 ? "#fbbf2466" : "#06d6a066",
                borderRight: `2px solid ${s.flip_rate > 0.2 ? "#e94560" : s.flip_rate > 0.1 ? "#fbbf24" : "#06d6a0"}`,
              }} />
            </div>
          </div>
        ))}
      </div>

      <div className="adv-sensitivity">
        <div className="advs-title">Feature Sensitivity Analysis</div>
        {(data.feature_sensitivity || []).map(f => (
          <div key={f.feature} className="advs-row">
            <span className="advs-feat">{f.feature}</span>
            <span className="advs-perturb">{f.perturbation}</span>
            <div className="advs-bar-wrap">
              <div className="advs-bar" style={{
                width: `${Math.min(f.flip_rate * 500, 100)}%`,
                background: f.sensitivity === "HIGH" ? "#e9456066" : "#fbbf2466",
              }} />
            </div>
            <span className={`advs-sev sev-${f.sensitivity.toLowerCase()}`}>{f.sensitivity}</span>
          </div>
        ))}
      </div>

      <div className="adv-recs">
        <div className="advr-title">Recommendations</div>
        {(data.recommendations || []).map((r, i) => (
          <div key={i} className="advr-item">• {r}</div>
        ))}
      </div>
    </div>
  );
}

function IntegrityReport({ data }) {
  const levelColors = { TRUSTED: "#06d6a0", SUSPECT: "#fbbf24", COMPROMISED: "#f97316", POISONED: "#e94560" };
  const lc = levelColors[data.integrity_level] || "#64748b";

  return (
    <div className="integrity-report">
      <div className="ir-header">
        <div className="ir-score-wrap">
          <div className="ir-score" style={{ color: lc }}>{data.integrity_score}</div>
          <div className="ir-denom">/100</div>
        </div>
        <div className="ir-meta">
          <div className="ir-level" style={{ color: lc, background: lc + "22", border: `1px solid ${lc}44` }}>
            {data.integrity_level}
          </div>
          <div className="ir-summary">{data.summary}</div>
          <div className="ir-counts">
            <span className="irc-pass">✓ {data.checks_passed} passed</span>
            <span className="irc-fail">✗ {data.checks_failed} failed</span>
          </div>
        </div>
      </div>

      <div className="ir-checks">
        {(data.checks || []).map((c, i) => {
          const statusColor = { PASS: "#06d6a0", FAIL: "#e94560", WARNING: "#fbbf24", INFO: "#3b82f6", SKIPPED: "#64748b" };
          const sc = statusColor[c.status] || "#64748b";
          return (
            <div key={i} className="ir-check">
              <div className="irc-status" style={{ color: sc, background: sc + "22" }}>{c.status}</div>
              <div className="irc-body">
                <div className="irc-name">{c.check}</div>
                <div className="irc-detail">{c.detail}</div>
              </div>
              {c.penalty > 0 && <div className="irc-penalty">-{c.penalty}pts</div>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ReviewQueue({ queue }) {
  const [decisions, setDecisions] = useState({});

  const decide = (caseId, action) => {
    setDecisions(d => ({ ...d, [caseId]: action }));
  };

  if (!queue.length) {
    return (
      <div className="empty-panel">
        <div className="ep-icon">✓</div>
        <p>No borderline cases flagged for review at this time.</p>
      </div>
    );
  }

  return (
    <div className="review-queue">
      <div className="rq-header">
        <span className="rq-count">{queue.length} cases pending review</span>
        <span className="rq-note">These applications were rejected by the model but approved by the unbiased fair model.</span>
      </div>
      <div className="rq-cases">
        {queue.map(c => {
          const decision = decisions[c.case_id];
          const priorityColor = c.review_priority === "HIGH" ? "#e94560" : "#fbbf24";
          return (
            <div key={c.case_id} className={`rq-case ${decision ? `rq-decided-${decision.toLowerCase()}` : ""}`}>
              <div className="rqc-top">
                <div className="rqc-id-group">
                  <span className="rqc-case-id">{c.case_id}</span>
                  <span className="rqc-app-id">{c.applicant_id}</span>
                  <span className="rqc-priority" style={{ color: priorityColor, background: priorityColor + "22" }}>
                    {c.review_priority} PRIORITY
                  </span>
                </div>
                <div className="rqc-bias-score">
                  <span className="rqc-bs-label">Bias Score</span>
                  <div className="rqc-bs-bar">
                    <div style={{ width: `${c.bias_score}%`, background: c.bias_score > 60 ? "#e94560" : "#fbbf24" }} />
                  </div>
                  <span className="rqc-bs-val">{c.bias_score}%</span>
                </div>
              </div>

              <div className="rqc-profile">
                <span>{c.gender}</span><span>·</span>
                <span>{c.religion}</span><span>·</span>
                <span>Age {c.age}</span><span>·</span>
                <span>Tier {c.city_tier} ({c.city})</span><span>·</span>
                <span>CIBIL {c.cibil_score}</span><span>·</span>
                <span>₹{c.monthly_income?.toLocaleString()}/mo</span>
              </div>

              <div className="rqc-flags">
                {c.risk_flags?.map((f, i) => (
                  <div key={i} className="rqcf-item">⚠ {f}</div>
                ))}
              </div>

              <div className="rqc-decisions">
                <div className="rqcd-ai">
                  <span>AI Model:</span>
                  <span className="rqcd-rejected">REJECTED</span>
                </div>
                <div className="rqcd-ai">
                  <span>Fair Model:</span>
                  <span className="rqcd-approved">APPROVED</span>
                </div>
                {!decision ? (
                  <div className="rqcd-actions">
                    <button className="btn-approve" onClick={() => decide(c.case_id, "APPROVED")}>✓ Approve</button>
                    <button className="btn-reject" onClick={() => decide(c.case_id, "REJECTED")}>✗ Reject</button>
                    <button className="btn-escalate" onClick={() => decide(c.case_id, "ESCALATED")}>↑ Escalate</button>
                  </div>
                ) : (
                  <div className={`rqcd-decided rqcd-${decision.toLowerCase()}`}>
                    Officer Decision: <strong>{decision}</strong>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
