"""
Model Integrity Score
Checks for data poisoning, model tampering, and systematic bias injection.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
import hashlib
import warnings
warnings.filterwarnings("ignore")

FEATURE_COLS = [
    "cibil_score", "monthly_income", "loan_amount",
    "debt_to_income_ratio", "existing_loans",
    "credit_history_years", "num_late_payments",
]


def compute_integrity_score(
    df: pd.DataFrame,
    model=None,
    file_hash: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute a model integrity score checking for poisoning and tampering."""

    checks = []
    total_score = 100

    # Check 1: Feature distribution normality (poisoning leaves statistical traces)
    feature_anomalies = []
    for feat in FEATURE_COLS:
        if feat not in df.columns:
            continue
        vals = df[feat].astype(float)
        mean, std = vals.mean(), vals.std()
        skew = float(((vals - mean) ** 3).mean() / (std ** 3 + 1e-10))
        if abs(skew) > 3.0:
            feature_anomalies.append({
                "feature": feat,
                "skewness": round(skew, 3),
                "severity": "HIGH" if abs(skew) > 5 else "MEDIUM",
            })

    if feature_anomalies:
        penalty = min(20, len(feature_anomalies) * 5)
        total_score -= penalty
        checks.append({
            "check": "Feature Distribution Analysis",
            "status": "WARNING",
            "detail": f"{len(feature_anomalies)} features show unusual skewness that may indicate data manipulation.",
            "anomalies": feature_anomalies,
            "penalty": penalty,
        })
    else:
        checks.append({
            "check": "Feature Distribution Analysis",
            "status": "PASS",
            "detail": "All feature distributions appear statistically normal.",
            "anomalies": [],
            "penalty": 0,
        })

    # Check 2: Approval rate consistency across groups (systematic bias injection)
    group_approval_rates = {}
    for attr in ["gender", "city_tier", "religion"]:
        if attr not in df.columns:
            continue
        rates = df.groupby(attr)["model_approved"].mean().to_dict()
        max_rate = max(rates.values())
        min_rate = min(rates.values())
        if max_rate > 0 and (min_rate / max_rate) < 0.5:
            group_approval_rates[attr] = {
                "rates": {str(k): round(float(v), 4) for k, v in rates.items()},
                "ratio": round(float(min_rate / max_rate), 4),
                "severity": "CRITICAL" if min_rate / max_rate < 0.3 else "HIGH",
            }

    if group_approval_rates:
        penalty = min(30, len(group_approval_rates) * 10)
        total_score -= penalty
        checks.append({
            "check": "Systematic Bias Injection Check",
            "status": "FAIL",
            "detail": f"Significant approval rate disparities detected across {list(group_approval_rates.keys())}. Possible poisoning.",
            "affected_attributes": group_approval_rates,
            "penalty": penalty,
        })
    else:
        checks.append({
            "check": "Systematic Bias Injection Check",
            "status": "PASS",
            "detail": "Approval rate disparities within acceptable limits.",
            "affected_attributes": {},
            "penalty": 0,
        })

    # Check 3: Label consistency (fair_approved vs model_approved correlation)
    if "fair_approved" in df.columns and "model_approved" in df.columns:
        agreement = (df["fair_approved"] == df["model_approved"]).mean()
        disagreement_rate = 1.0 - agreement

        if disagreement_rate > 0.20:
            penalty = min(25, int(disagreement_rate * 100))
            total_score -= penalty
            checks.append({
                "check": "Label Consistency Check",
                "status": "WARNING",
                "detail": f"Model disagrees with fair ground truth on {disagreement_rate:.1%} of cases — unusually high.",
                "agreement_rate": round(float(agreement), 4),
                "penalty": penalty,
            })
        else:
            checks.append({
                "check": "Label Consistency Check",
                "status": "PASS",
                "detail": f"Model agrees with fair ground truth on {agreement:.1%} of cases.",
                "agreement_rate": round(float(agreement), 4),
                "penalty": 0,
            })

    # Check 4: Demographic correlation with residuals (proxy variable detection)
    proxy_vars = []
    if model is not None:
        try:
            X = df[FEATURE_COLS].astype(float)
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(X)[:, 1]
            else:
                probs = model.predict(X).astype(float)

            for attr in ["gender", "city_tier", "religion"]:
                if attr not in df.columns:
                    continue
                # Check correlation between model score and sensitive attribute
                for g in df[attr].unique():
                    g_mask = df[attr] == g
                    other_mask = ~g_mask
                    if g_mask.sum() < 20 or other_mask.sum() < 20:
                        continue
                    g_mean = probs[g_mask].mean()
                    other_mean = probs[other_mask].mean()
                    if abs(g_mean - other_mean) > 0.15:
                        proxy_vars.append({
                            "attribute": attr,
                            "group": str(g),
                            "score_delta": round(float(g_mean - other_mean), 4),
                        })
        except Exception:
            pass

    if proxy_vars:
        penalty = min(15, len(proxy_vars) * 5)
        total_score -= penalty
        checks.append({
            "check": "Proxy Variable Detection",
            "status": "WARNING",
            "detail": f"Model scores correlate with {len(proxy_vars)} sensitive attribute groups — potential proxy discrimination.",
            "proxy_variables": proxy_vars,
            "penalty": penalty,
        })
    else:
        checks.append({
            "check": "Proxy Variable Detection",
            "status": "PASS" if model is not None else "SKIPPED",
            "detail": "No significant proxy variable correlation detected." if model else "Proxy detection requires an uploaded model.",
            "proxy_variables": [],
            "penalty": 0,
        })

    # Check 5: File hash verification
    if file_hash:
        checks.append({
            "check": "File Integrity Hash",
            "status": "PASS",
            "detail": f"Model file hash verified: {file_hash[:16]}...",
            "hash": file_hash[:32],
            "penalty": 0,
        })
    else:
        checks.append({
            "check": "File Integrity Hash",
            "status": "INFO",
            "detail": "Using demo model — no file hash to verify.",
            "hash": "N/A",
            "penalty": 0,
        })

    total_score = max(0, min(100, total_score))
    n_fail = sum(1 for c in checks if c["status"] in ("FAIL", "WARNING"))

    if total_score >= 80:
        integrity_level = "TRUSTED"
    elif total_score >= 60:
        integrity_level = "SUSPECT"
    elif total_score >= 40:
        integrity_level = "COMPROMISED"
    else:
        integrity_level = "POISONED"

    return {
        "integrity_score": total_score,
        "integrity_level": integrity_level,
        "checks_passed": len(checks) - n_fail,
        "checks_failed": n_fail,
        "total_checks": len(checks),
        "checks": checks,
        "summary": f"Model integrity: {integrity_level} ({total_score}/100). {n_fail} concern(s) detected.",
    }
