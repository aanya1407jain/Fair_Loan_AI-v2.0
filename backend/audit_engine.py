"""
Audit Engine v2.0 — Core bias analysis
"""

import numpy as np
import pandas as pd
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
import warnings
warnings.filterwarnings("ignore")

FEATURE_COLS = [
    "cibil_score", "monthly_income", "loan_amount",
    "debt_to_income_ratio", "existing_loans",
    "credit_history_years", "num_late_payments",
]

PROTECTED_ATTRS = ["gender", "religion", "city_tier"]

PRIVILEGED = {
    "gender": "Male",
    "religion": "Hindu",
    "city_tier": 1,
}


def _predict_with_model(model, X: pd.DataFrame) -> np.ndarray:
    try:
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X)
            return (probs[:, 1] >= 0.5).astype(int)
        return model.predict(X).astype(int)
    except Exception:
        return np.zeros(len(X), dtype=int)


def _build_demo_model(df: pd.DataFrame):
    """Train a biased logistic regression model on model_approved labels."""
    X = df[FEATURE_COLS].astype(float)
    y = df["model_approved"].values
    scaler = StandardScaler()
    X_s = scaler.fit_transform(X)
    lr = LogisticRegression(max_iter=500, random_state=42)
    lr.fit(X_s, y)
    # Patch predict to include scaler
    class PatchedModel:
        def __init__(self, lr, scaler):
            self.lr = lr; self.scaler = scaler
        def predict(self, X):
            return self.lr.predict(self.scaler.transform(X))
        def predict_proba(self, X):
            return self.lr.predict_proba(self.scaler.transform(X))
    return PatchedModel(lr, scaler)


def _compute_disparate_impact(df: pd.DataFrame, preds: np.ndarray, attr: str) -> Dict:
    privileged_val = PRIVILEGED.get(attr)
    priv_mask = df[attr] == privileged_val
    priv_rate = preds[priv_mask].mean() if priv_mask.sum() > 0 else 0.0001

    result = {}
    for group in df[attr].unique():
        mask = df[attr] == group
        if mask.sum() < 10:
            continue
        rate = float(preds[mask].mean())
        di = rate / priv_rate if priv_rate > 0 else 0.0
        result[str(group)] = {
            "approval_rate": round(rate, 4),
            "di_ratio": round(di, 4),
            "count": int(mask.sum()),
            "flagged": di < 0.8 and str(group) != str(privileged_val),
        }
    return result


def _compute_demographic_parity(df: pd.DataFrame, preds: np.ndarray, attr: str) -> Dict:
    overall_rate = preds.mean()
    result = {}
    for group in df[attr].unique():
        mask = df[attr] == group
        if mask.sum() < 10:
            continue
        rate = float(preds[mask].mean())
        result[str(group)] = {
            "approval_rate": round(rate, 4),
            "dpd": round(float(rate - overall_rate), 4),
            "count": int(mask.sum()),
        }
    return result


def _compute_equal_opportunity(df: pd.DataFrame, preds: np.ndarray, y_true: np.ndarray, attr: str) -> Dict:
    privileged_val = PRIVILEGED.get(attr)
    result = {}
    priv_mask = df[attr] == privileged_val
    if priv_mask.sum() > 0 and y_true[priv_mask].sum() > 0:
        priv_tpr = float(preds[(priv_mask) & (y_true == 1)].mean()) if (priv_mask & (y_true == 1)).sum() > 0 else 0
    else:
        priv_tpr = 0.5

    for group in df[attr].unique():
        mask = df[attr] == group
        if mask.sum() < 10:
            continue
        pos_mask = mask & (y_true == 1)
        tpr = float(preds[pos_mask].mean()) if pos_mask.sum() > 0 else 0.0
        result[str(group)] = {
            "tpr": round(tpr, 4),
            "eo_gap": round(float(tpr - priv_tpr), 4),
            "count": int(mask.sum()),
        }
    return result


def _severity(di_values: list) -> str:
    min_di = min(di_values) if di_values else 1.0
    if min_di < 0.5:
        return "CRITICAL"
    elif min_di < 0.7:
        return "HIGH"
    elif min_di < 0.8:
        return "MEDIUM"
    elif min_di < 0.9:
        return "LOW"
    return "PASS"


def run_audit(
    df: pd.DataFrame,
    model=None,
    model_type: str = "demo",
) -> Dict[str, Any]:
    audit_id = uuid.uuid4().hex[:8].upper()
    ts = datetime.now(timezone.utc).isoformat()

    # Build model if demo
    if model is None:
        model = _build_demo_model(df)

    X = df[FEATURE_COLS].astype(float)
    preds = _predict_with_model(model, X)
    y_true = df["fair_approved"].values

    # Overall metrics
    acc = float(accuracy_score(y_true, preds))
    f1 = float(f1_score(y_true, preds, zero_division=0))
    try:
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X)[:, 1]
        else:
            probs = preds.astype(float)
        auc = float(roc_auc_score(y_true, probs))
    except:
        auc = 0.0

    overall_metrics = {
        "accuracy": round(acc, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(auc, 4),
        "total_samples": len(df),
        "total_approved": int(preds.sum()),
        "total_rejected": int((preds == 0).sum()),
        "approval_rate": round(float(preds.mean()), 4),
    }

    # Bias analysis per attribute
    bias_analysis = {}
    all_flagged = False

    for attr in PROTECTED_ATTRS:
        di = _compute_disparate_impact(df, preds, attr)
        dp = _compute_demographic_parity(df, preds, attr)
        eo = _compute_equal_opportunity(df, preds, y_true, attr)

        flagged = [v for v in di.values() if v.get("flagged")]
        di_vals = [v["di_ratio"] for v in di.values()]
        sev = _severity(di_vals)
        if sev in ("CRITICAL", "HIGH", "MEDIUM"):
            all_flagged = True

        priv = PRIVILEGED.get(attr)
        priv_rate = di.get(str(priv), {}).get("approval_rate", 0)
        min_di = min(di_vals) if di_vals else 1.0

        bias_analysis[attr] = {
            "severity": sev,
            "disparate_impact": di,
            "demographic_parity": dp,
            "equal_opportunity": eo,
            "privileged_group": str(priv),
            "privileged_approval_rate": round(priv_rate, 4),
            "min_di_ratio": round(min_di, 4),
            "flagged_groups": [str(g) for g in df[attr].unique() if di.get(str(g), {}).get("flagged")],
            "summary": _generate_summary(attr, sev, di, min_di),
        }

    # Intersectional analysis
    intersectional = []
    for gender in df["gender"].unique():
        for tier in sorted(df["city_tier"].unique()):
            mask = (df["gender"] == gender) & (df["city_tier"] == tier)
            if mask.sum() < 20:
                continue
            rate = float(preds[mask].mean())
            intersectional.append({
                "gender": gender,
                "city_tier": int(tier),
                "approval_rate": round(rate, 4),
                "count": int(mask.sum()),
            })

    # Risk score
    max_sev_order = {"PASS": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    top_sev = max((d["severity"] for d in bias_analysis.values()), key=lambda s: max_sev_order.get(s, 0))
    risk_score = max_sev_order[top_sev] * 20 + (20 - int(min(acc, 1) * 20))
    risk_score = min(100, max(0, risk_score))

    risk_level_map = {0: "PASS", 1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}
    risk_level = risk_level_map.get(max_sev_order.get(top_sev, 0), "UNKNOWN")

    rbi_compliant = top_sev in ("PASS", "LOW")

    # Mitigation suggestions
    mitigation = []
    for attr, data in bias_analysis.items():
        if data["severity"] in ("CRITICAL", "HIGH", "MEDIUM"):
            priority = "HIGH" if data["severity"] in ("CRITICAL", "HIGH") else "MEDIUM"
            mitigation.append({
                "attribute": attr,
                "severity": data["severity"],
                "priority": priority,
                "technique": "ThresholdOptimizer (Post-processing)",
                "description": (
                    f"Apply Fairlearn's ThresholdOptimizer with demographic_parity constraint "
                    f"on '{attr}'. Flagged groups: {', '.join(data['flagged_groups'])}. "
                    f"Min DI ratio: {data['min_di_ratio']:.3f} (threshold: 0.800)."
                ),
                "fairlearn_api": f"ThresholdOptimizer(estimator=model, constraints=DemographicParity()).fit(X_train, y_train, sensitive_features=df['{attr}'])",
            })

    # Regulatory notes
    reg_notes = []
    for attr, data in bias_analysis.items():
        if data["severity"] == "CRITICAL":
            reg_notes.append(
                f"CRITICAL: {attr.upper()} shows min DI ratio of {data['min_di_ratio']:.3f}, "
                f"far below the RBI 80% threshold. Immediate mitigation required."
            )
        elif data["severity"] == "HIGH":
            reg_notes.append(
                f"HIGH: {attr.upper()} DI ratio {data['min_di_ratio']:.3f} violates the 4/5ths rule. "
                f"Deploy ThresholdOptimizer before production."
            )
    if rbi_compliant:
        reg_notes.append("Model meets minimum RBI fair lending standards for all tested protected attributes.")
    reg_notes.append("Audit conducted under RBI Master Circular on Fair Practices Code for Lenders (2023).")
    reg_notes.append(f"Dataset: {len(df):,} synthetic Indian applicants across Tier-1/2/3 cities.")

    return {
        "audit_id": audit_id,
        "timestamp": ts,
        "model_type": model_type,
        "dataset": {
            "total_samples": len(df),
            "source": "synthetic_indian_demographics",
            "features": FEATURE_COLS,
            "protected_attributes": PROTECTED_ATTRS,
            "city_distribution": {str(t): int((df["city_tier"] == t).sum()) for t in [1, 2, 3]},
            "gender_distribution": df["gender"].value_counts().to_dict(),
        },
        "overall_metrics": overall_metrics,
        "bias_analysis": bias_analysis,
        "intersectional": intersectional,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "rbi_compliant": rbi_compliant,
        "mitigation_suggestions": mitigation,
        "regulatory_notes": reg_notes,
        "model_integrity": None,  # filled by main.py
    }


def _generate_summary(attr: str, sev: str, di: dict, min_di: float) -> str:
    flagged = [g for g, v in di.items() if v.get("flagged")]
    if not flagged:
        return f"All groups pass the 80% rule. Min DI ratio: {min_di:.3f}."
    return (
        f"Severity: {sev}. Groups {', '.join(flagged)} show DI ratio below 0.800 "
        f"(min: {min_di:.3f}). This indicates {attr.replace('_', ' ')} discrimination."
    )
