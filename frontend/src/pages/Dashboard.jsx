import "./Dashboard.css";

export default function Dashboard({ onRunDemo, loading }) {
  return (
    <div className="dashboard">
      {/* Hero */}
      <section className="hero">
        <div className="hero-glow" />
        <div className="hero-content">
          <div className="hero-eyebrow">
            <span className="eyebrow-dot" />
            India's RegTech Credit Fairness Layer
          </div>
          <h1 className="hero-title">
            Detect & Fix Bias in<br />
            <span className="hero-accent">Loan Scoring Models</span>
          </h1>
          <p className="hero-desc">
            Banks and NBFCs use ML models that encode historical discrimination against
            gender, religion, and geography. Fair Loan AI audits any model for
            disparate impact, provides AI-powered mitigation, and generates
            RBI-ready compliance reports — in seconds.
          </p>
          <div className="hero-actions">
            <button className="btn-primary btn-lg" onClick={onRunDemo} disabled={loading}>
              {loading ? (
                <><span className="spin">◌</span> Running Audit…</>
              ) : (
                <>▶ Run Demo Audit</>
              )}
            </button>
            <div className="hero-action-note">
              5,000 synthetic Indian applicants · 3 protected attributes · Full PDF export
            </div>
          </div>
        </div>

        {/* Floating stats */}
        <div className="hero-stats">
          {STATS.map(s => (
            <div key={s.label} className="hero-stat">
              <div className="stat-val">{s.val}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="features-section">
        <div className="section-header">
          <h2>Advanced Audit Capabilities</h2>
          <p>From bias detection to regulatory compliance — in one platform</p>
        </div>
        <div className="features-grid">
          {FEATURES.map(f => (
            <div key={f.title} className="feature-card">
              <div className="feature-icon-wrap" style={{ background: f.color + "22", border: `1px solid ${f.color}44` }}>
                <span className="feature-icon">{f.icon}</span>
              </div>
              <div className="feature-body">
                <div className="feature-title">{f.title}</div>
                <div className="feature-desc">{f.desc}</div>
                {f.tag && <div className="feature-tag" style={{ color: f.color, background: f.color + "11" }}>{f.tag}</div>}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="pipeline-section">
        <div className="section-header">
          <h2>Audit Pipeline</h2>
          <p>Five-stage automated fairness assessment</p>
        </div>
        <div className="pipeline">
          {STEPS.map((s, i) => (
            <div key={i} className="pipeline-step">
              <div className="step-connector" />
              <div className="step-bubble" style={{ background: s.color + "22", borderColor: s.color + "66" }}>
                <span style={{ color: s.color }}>{s.icon}</span>
              </div>
              <div className="step-content">
                <div className="step-num" style={{ color: s.color }}>STEP {i + 1}</div>
                <div className="step-title">{s.title}</div>
                <div className="step-desc">{s.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Terminology */}
      <section className="terms-section">
        <div className="section-header">
          <h2>Industry-Standard Terminology</h2>
          <p>Fair Loan AI uses regulatory-grade fairness metrics</p>
        </div>
        <div className="terms-grid">
          {TERMS.map(t => (
            <div key={t.term} className="term-card">
              <div className="term-header">
                <span className="term-abbr">{t.abbr}</span>
                <span className="term-name">{t.term}</span>
              </div>
              <div className="term-def">{t.def}</div>
              <div className="term-threshold">Threshold: {t.threshold}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

const STATS = [
  { val: "80%", label: "4/5 Rule Threshold" },
  { val: "3", label: "Protected Attributes" },
  { val: "5K+", label: "Synthetic Samples" },
  { val: "RBI", label: "2023 Aligned" },
  { val: "PDF", label: "Compliance Export" },
  { val: "AI", label: "Auto-Mitigation" },
];

const FEATURES = [
  { icon: "🔍", title: "Disparate Impact Heatmap", desc: "Red-to-Green grid showing DI ratios across Gender × Religion × City Tier × Loan Type.", color: "#e94560", tag: "4/5ths Rule" },
  { icon: "🛠", title: "Mitigation Engine", desc: "ThresholdOptimizer post-processing. Before/after accuracy vs fairness comparison.", color: "#06d6a0", tag: "Fairlearn API" },
  { icon: "🔮", title: "Counterfactual What-If", desc: "Change one attribute on a rejected application to test if the decision flips.", color: "#a78bfa", tag: "Individual Fairness" },
  { icon: "⚔", title: "Adversarial Robustness", desc: "Tests if the model can be exploited by slightly inflating non-sensitive features.", color: "#f97316", tag: "Security" },
  { icon: "📊", title: "SHAP Waterfall Charts", desc: "Feature attribution for rejection decisions. Reveals proxy variable discrimination.", color: "#3b82f6", tag: "Explainability" },
  { icon: "📈", title: "Accuracy-Fairness Trade-off", desc: "Pareto frontier scatter plot. Shows the cost of fairness to help pick optimal operating point.", color: "#fbbf24", tag: "Pareto Frontier" },
  { icon: "🧠", title: "Model Integrity Score", desc: "Detects data poisoning, proxy variables, and systematic bias injection in training data.", color: "#ec4899", tag: "Cybersecurity" },
  { icon: "👤", title: "Human-in-the-Loop Review", desc: "Dashboard queue for borderline bias cases requiring human officer decision.", color: "#06d6a0", tag: "Manual Review" },
  { icon: "📄", title: "RBI Compliance PDF", desc: "One-click regulatory report: Model Card, Bias Analysis, Mitigation Plan, Integrity Check.", color: "#e94560", tag: "RegTech" },
];

const STEPS = [
  { icon: "⚙", title: "Load Data", desc: "5,000 synthetic Indian applicants — Tier-1/2/3 cities, realistic demographics.", color: "#3b82f6" },
  { icon: "🧮", title: "Run Model", desc: "Built-in biased demo model or upload your own .pkl with predict() / predict_proba().", color: "#a78bfa" },
  { icon: "📐", title: "Compute Metrics", desc: "Disparate Impact, Equal Opportunity, Demographic Parity across all protected attributes.", color: "#fbbf24" },
  { icon: "🛠", title: "Apply Mitigation", desc: "ThresholdOptimizer adjusts group-specific decision boundaries to satisfy fairness constraints.", color: "#06d6a0" },
  { icon: "📄", title: "Export Report", desc: "Professional PDF with Model Card, Audit Trail, Mitigation Plan — ready for RBI submission.", color: "#e94560" },
];

const TERMS = [
  { abbr: "DI", term: "Disparate Impact", def: "Ratio of approval rates between disadvantaged and privileged groups. Tests if protected attributes cause significantly lower outcomes.", threshold: "≥ 0.80 (4/5ths rule)" },
  { abbr: "EO", term: "Equalized Odds", def: "Equal true positive AND false positive rates across demographic groups. Stricter than Equal Opportunity.", threshold: "|diff| ≤ 0.10" },
  { abbr: "DP", term: "Demographic Parity", def: "Overall approval rates should be similar across all demographic groups, regardless of actual creditworthiness.", threshold: "|diff| ≤ 0.05" },
  { abbr: "PV", term: "Proxy Variable Detection", def: "Identifies when seemingly neutral features (Zip Code, Monthly Income) act as stand-ins for protected attributes like caste or religion.", threshold: "SHAP correlation < 0.15" },
];
