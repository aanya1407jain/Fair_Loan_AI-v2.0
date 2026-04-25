import "./BiasHeatmap.css";

const SEVERITY_COLORS = {
  CRITICAL: "#ff6b6b",
  HIGH: "#ffd166",
  MEDIUM: "#f4a261",
  LOW: "#06d6a0",
  PASS: "#06d6a0",
  MINIMAL: "#06d6a0",
};

export default function BiasHeatmap({ biasAnalysis }) {
  if (!biasAnalysis) return null;

  const attrs = Object.entries(biasAnalysis);

  return (
    <div className="heatmap-container">
      <div className="heatmap-title">
        <span>Bias Heatmap</span>
        <span className="heatmap-subtitle">Group × Metric Grid</span>
      </div>

      {attrs.map(([attr, data]) => {
        const di = data.disparate_impact || {};
        const eod = data.equal_opportunity || {};

        return (
          <div key={attr} className="attr-section">
            <div className="attr-header">
              <span className="attr-name">{attr.replace("_", " ").toUpperCase()}</span>
              <span
                className="severity-badge"
                style={{ background: SEVERITY_COLORS[data.severity] + "22", color: SEVERITY_COLORS[data.severity], border: `1px solid ${SEVERITY_COLORS[data.severity]}` }}
              >
                {data.severity}
              </span>
            </div>

            <div className="heat-grid">
              <div className="heat-col-header"></div>
              <div className="heat-col-header">Approval Rate</div>
              <div className="heat-col-header">DI Ratio</div>
              <div className="heat-col-header">EOD</div>
              <div className="heat-col-header">Status</div>

              {Object.entries(di).map(([group, val]) => {
                const eodVal = eod[group] || {};
                const di_ratio = val.di_ratio;
                const heatColor = di_ratio >= 0.9 ? "#06d6a0" : di_ratio >= 0.8 ? "#ffd166" : di_ratio >= 0.7 ? "#f4a261" : "#ff6b6b";
                const isPivileged = group == data.privileged_group;

                return (
                  <>
                    <div className="heat-row-label" key={group + "-label"}>
                      {group}
                      {isPivileged && <span className="priv-tag">ref</span>}
                    </div>
                    <div className="heat-cell">
                      <div className="cell-bar-wrap">
                        <div className="cell-bar" style={{ width: `${val.approval_rate * 100}%`, background: heatColor }}></div>
                        <span>{(val.approval_rate * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                    <div className="heat-cell" style={{ color: heatColor, fontFamily: "Space Mono, monospace" }} key={group + "-di"}>
                      {di_ratio.toFixed(3)}
                    </div>
                    <div className="heat-cell" key={group + "-eod"} style={{ fontFamily: "Space Mono, monospace", color: eodVal.eod < -0.1 ? "#ff6b6b" : "var(--text)" }}>
                      {eodVal.eod !== undefined ? eodVal.eod.toFixed(3) : "—"}
                    </div>
                    <div className="heat-cell" key={group + "-status"}>
                      {val.flagged
                        ? <span className="flag-badge">⚠ Flagged</span>
                        : <span className="ok-badge">✓ OK</span>
                      }
                    </div>
                  </>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
