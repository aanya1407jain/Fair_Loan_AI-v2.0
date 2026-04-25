"""
Adversarial Robustness Check
Tests if the model can be "fooled" by slightly perturbing non-sensitive features
to grant loans to high-risk profiles.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
import warnings
warnings.filterwarnings("ignore")

FEATURE_COLS = [
    "cibil_score", "monthly_income", "loan_amount",
    "debt_to_income_ratio", "existing_loans",
    "credit_history_years", "num_late_payments",
]

# Non-sensitive features that could be manipulated
MANIPULABLE_FEATURES = [
    "cibil_score", "monthly_income", "credit_history_years",
    "num_late_payments", "debt_to_income_ratio"
]


def _get_predictions_proba(df: pd.DataFrame, model=None) -> np.ndarray:
    if model is not None and hasattr(model, "predict_proba"):
        X = df[FEATURE_COLS].astype(float)
        return model.predict_proba(X)[:, 1]
    elif model is not None:
        X = df[FEATURE_COLS].astype(float)
        return model.predict(X).astype(float)
    return df["model_score"].values / 100.0


def run_adversarial_check(df: pd.DataFrame, model=None) -> Dict[str, Any]:
    """
    Tests adversarial vulnerability by slightly inflating applicant features
    to see how many high-risk profiles can flip to approval.
    """
    rng = np.random.default_rng(42)

    # Select high-risk applicants (low CIBIL, high DTI, many late payments)
    high_risk_mask = (
        (df["cibil_score"] < 550) &
        (df["debt_to_income_ratio"] > 1.0) &
        (df["num_late_payments"] > 3)
    )
    high_risk = df[high_risk_mask].head(100).copy()

    if len(high_risk) < 5:
        high_risk = df[df["model_approved"] == 0].head(100).copy()

    original_probs = _get_predictions_proba(high_risk, model)
    original_approved = (original_probs >= 0.5).sum()

    # Attack 1: Small perturbation (+5% on CIBIL, -10% on DTI)
    perturbed_small = high_risk.copy()
    perturbed_small["cibil_score"] = np.clip(
        perturbed_small["cibil_score"] * 1.05, 300, 900
    ).astype(int)
    perturbed_small["debt_to_income_ratio"] = np.clip(
        perturbed_small["debt_to_income_ratio"] * 0.90, 0.05, 2.5
    )
    perturbed_small["num_late_payments"] = np.maximum(
        perturbed_small["num_late_payments"] - 1, 0
    )
    small_probs = _get_predictions_proba(perturbed_small, model)
    small_approved = (small_probs >= 0.5).sum()

    # Attack 2: Moderate perturbation (+15% CIBIL, -20% DTI, -2 late payments)
    perturbed_moderate = high_risk.copy()
    perturbed_moderate["cibil_score"] = np.clip(
        perturbed_moderate["cibil_score"] * 1.15, 300, 900
    ).astype(int)
    perturbed_moderate["debt_to_income_ratio"] = np.clip(
        perturbed_moderate["debt_to_income_ratio"] * 0.80, 0.05, 2.5
    )
    perturbed_moderate["num_late_payments"] = np.maximum(
        perturbed_moderate["num_late_payments"] - 2, 0
    )
    moderate_probs = _get_predictions_proba(perturbed_moderate, model)
    moderate_approved = (moderate_probs >= 0.5).sum()

    # Attack 3: Strong perturbation (CIBIL +100, DTI halved, no late payments)
    perturbed_strong = high_risk.copy()
    perturbed_strong["cibil_score"] = np.clip(
        perturbed_strong["cibil_score"] + 100, 300, 900
    ).astype(int)
    perturbed_strong["debt_to_income_ratio"] = np.clip(
        perturbed_strong["debt_to_income_ratio"] * 0.5, 0.05, 2.5
    )
    perturbed_strong["num_late_payments"] = 0
    perturbed_strong["credit_history_years"] = np.minimum(
        perturbed_strong["credit_history_years"] + 3, 30
    )
    strong_probs = _get_predictions_proba(perturbed_strong, model)
    strong_approved = (strong_probs >= 0.5).sum()

    total = len(high_risk)

    # Assess vulnerability level
    flip_rate_small = float(small_approved - original_approved) / total if total > 0 else 0
    flip_rate_moderate = float(moderate_approved - original_approved) / total if total > 0 else 0
    flip_rate_strong = float(strong_approved - original_approved) / total if total > 0 else 0

    if flip_rate_small > 0.30:
        vulnerability = "CRITICAL"
        vuln_desc = "Model is extremely sensitive to small feature changes. Easily exploitable."
    elif flip_rate_small > 0.15:
        vulnerability = "HIGH"
        vuln_desc = "Model can be fooled with minor perturbations (e.g., marginally inflated CIBIL score)."
    elif flip_rate_moderate > 0.20:
        vulnerability = "MEDIUM"
        vuln_desc = "Model requires moderate feature inflation to flip. Some robustness present."
    else:
        vulnerability = "LOW"
        vuln_desc = "Model is relatively robust to feature manipulation."

    # Feature sensitivity analysis
    feature_sensitivity = []
    for feat in MANIPULABLE_FEATURES:
        original_feat = high_risk[feat].copy()
        test_df = high_risk.copy()
        if feat in ["cibil_score", "monthly_income", "credit_history_years"]:
            test_df[feat] = test_df[feat] * 1.10  # +10%
        else:
            test_df[feat] = test_df[feat] * 0.90  # -10%

        test_probs = _get_predictions_proba(test_df, model)
        test_approved = (test_probs >= 0.5).sum()
        delta = int(test_approved) - int(original_approved)
        feature_sensitivity.append({
            "feature": feat,
            "perturbation": "+10%" if feat in ["cibil_score", "monthly_income", "credit_history_years"] else "-10%",
            "additional_approvals": int(delta),
            "flip_rate": round(float(delta) / total, 4) if total > 0 else 0,
            "sensitivity": "HIGH" if abs(delta) / total > 0.1 else "MEDIUM" if abs(delta) / total > 0.05 else "LOW",
        })

    return {
        "vulnerability_level": vulnerability,
        "vulnerability_description": vuln_desc,
        "high_risk_sample_size": total,
        "attack_scenarios": [
            {
                "attack": "Small Perturbation",
                "description": "CIBIL +5%, DTI -10%, 1 fewer late payment",
                "original_approvals": int(original_approved),
                "approvals_after_attack": int(small_approved),
                "additional_approvals": int(small_approved - original_approved),
                "flip_rate": round(flip_rate_small, 4),
            },
            {
                "attack": "Moderate Perturbation",
                "description": "CIBIL +15%, DTI -20%, 2 fewer late payments",
                "original_approvals": int(original_approved),
                "approvals_after_attack": int(moderate_approved),
                "additional_approvals": int(moderate_approved - original_approved),
                "flip_rate": round(flip_rate_moderate, 4),
            },
            {
                "attack": "Strong Perturbation",
                "description": "CIBIL +100pts, DTI halved, 0 late payments, +3yr credit history",
                "original_approvals": int(original_approved),
                "approvals_after_attack": int(strong_approved),
                "additional_approvals": int(strong_approved - original_approved),
                "flip_rate": round(flip_rate_strong, 4),
            },
        ],
        "feature_sensitivity": feature_sensitivity,
        "recommendations": [
            "Implement anomaly detection on input features to flag unusual values.",
            "Add rate-limiting on applications with sudden CIBIL score improvements.",
            "Monitor for correlated feature changes (CIBIL + DTI + late payments all improving simultaneously).",
            "Consider ensemble methods or adversarial training to improve robustness.",
            "Require documentation for large CIBIL score changes (>50 points in <6 months).",
        ] if vulnerability in ("CRITICAL", "HIGH") else [
            "Model shows reasonable robustness. Implement standard input validation.",
            "Continue quarterly adversarial testing as model evolves.",
        ],
    }
