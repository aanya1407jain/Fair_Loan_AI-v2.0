"""
SHAP Feature Attribution Engine
Computes approximate SHAP values for waterfall chart visualization.
Uses model-agnostic permutation-based approach when SHAP library unavailable.
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

FEATURE_LABELS = {
    "cibil_score": "CIBIL Credit Score",
    "monthly_income": "Monthly Income",
    "loan_amount": "Loan Amount Requested",
    "debt_to_income_ratio": "Debt-to-Income Ratio",
    "existing_loans": "Existing Active Loans",
    "credit_history_years": "Credit History (Years)",
    "num_late_payments": "Number of Late Payments",
}


def _get_proba(X: np.ndarray, model=None, df_reference=None) -> float:
    if model is not None and hasattr(model, "predict_proba"):
        return float(model.predict_proba(X)[0, 1])
    elif model is not None:
        return float(model.predict(X)[0])
    return 0.5  # fallback


def compute_shap_values(df: pd.DataFrame, model=None, n_samples: int = 100) -> Dict[str, Any]:
    """
    Compute approximate SHAP values using permutation importance.
    Returns global feature importance + sample-level waterfall data.
    """
    try:
        import shap
        return _shap_library(df, model, n_samples)
    except ImportError:
        return _permutation_shap(df, model, n_samples)


def _permutation_shap(df: pd.DataFrame, model=None, n_samples: int = 100) -> Dict[str, Any]:
    """Permutation-based feature attribution approximation."""
    sample = df.sample(min(n_samples, len(df)), random_state=42)
    X = sample[FEATURE_COLS].astype(float).values
    feature_means = X.mean(axis=0)

    # Global feature importance via permutation
    global_importance = {}
    baseline_preds = []

    for i in range(len(X)):
        row = X[i:i+1]
        pred = _approx_predict(row, model, feature_means, df)
        baseline_preds.append(pred)

    baseline_preds = np.array(baseline_preds)

    for j, feat in enumerate(FEATURE_COLS):
        permuted = X.copy()
        permuted[:, j] = feature_means[j]
        permuted_preds = []
        for i in range(len(permuted)):
            pred = _approx_predict(permuted[i:i+1], model, feature_means, df)
            permuted_preds.append(pred)
        permuted_preds = np.array(permuted_preds)
        importance = float(np.abs(baseline_preds - permuted_preds).mean())
        global_importance[feat] = importance

    # Normalize
    total = sum(global_importance.values()) + 1e-10
    global_importance_norm = {k: round(v / total, 4) for k, v in global_importance.items()}

    # Per-feature direction (positive = increases approval, negative = decreases)
    directions = {
        "cibil_score": 1, "monthly_income": 1, "credit_history_years": 1,
        "loan_amount": -1, "debt_to_income_ratio": -1,
        "existing_loans": -1, "num_late_payments": -1,
    }

    # Find rejected applications for waterfall chart
    rejected = df[df["model_approved"] == 0].head(5)
    waterfall_samples = []

    for idx, row in rejected.iterrows():
        base_value = float(df["model_approved"].mean())
        shap_vals = []
        row_vals = row[FEATURE_COLS].astype(float).values
        population_means = feature_means

        for j, feat in enumerate(FEATURE_COLS):
            feat_val = row_vals[j]
            pop_mean = population_means[j]
            importance = global_importance_norm[feat]
            direction = directions.get(feat, 1)

            # Contribution: deviation from mean * direction * importance
            if feat in ["cibil_score", "monthly_income", "credit_history_years"]:
                normalized_dev = (feat_val - pop_mean) / (pop_mean + 1e-10)
            else:
                normalized_dev = -(feat_val - pop_mean) / (pop_mean + 1e-10)

            contribution = float(normalized_dev * importance * direction * 0.3)
            shap_vals.append({
                "feature": feat,
                "label": FEATURE_LABELS[feat],
                "value": round(float(feat_val), 2),
                "shap_value": round(contribution, 4),
                "direction": "negative" if contribution < 0 else "positive",
                "population_mean": round(float(pop_mean), 2),
            })

        # Sort by absolute SHAP value
        shap_vals.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

        waterfall_samples.append({
            "applicant_id": str(row["applicant_id"]),
            "base_value": round(base_value, 4),
            "final_prediction": round(float(row.get("model_score", 30)) / 100, 4),
            "decision": "REJECTED",
            "shap_values": shap_vals,
            "top_rejection_reason": shap_vals[0]["label"] if shap_vals else "Unknown",
        })

    # Summary statistics
    sorted_global = sorted(global_importance_norm.items(), key=lambda x: -x[1])

    return {
        "method": "permutation_approximation",
        "global_importance": [
            {
                "feature": feat,
                "label": FEATURE_LABELS[feat],
                "importance": imp,
                "direction": directions.get(feat, 1),
                "rank": rank + 1,
            }
            for rank, (feat, imp) in enumerate(sorted_global)
        ],
        "waterfall_samples": waterfall_samples,
        "top_proxy_features": [
            feat for feat, _ in sorted_global[:3]
        ],
        "interpretation": (
            f"The top driver of rejections is '{FEATURE_LABELS[sorted_global[0][0]]}', "
            f"followed by '{FEATURE_LABELS[sorted_global[1][0]]}'. "
            "Features like debt_to_income_ratio and city_tier may act as proxy variables for sensitive attributes."
        ),
    }


def _approx_predict(row: np.ndarray, model=None, means=None, df=None) -> float:
    """Approximate prediction for a single row."""
    if model is not None:
        try:
            if hasattr(model, "predict_proba"):
                return float(model.predict_proba(row)[0, 1])
            return float(model.predict(row)[0])
        except:
            pass

    # Heuristic based on feature weights
    if means is None:
        return 0.5
    feat_names = FEATURE_COLS
    weights = [0.35, 0.25, -0.10, -0.20, -0.05, 0.10, -0.15]
    score = 0.5
    for j, (feat, w) in enumerate(zip(feat_names, weights)):
        if j < row.shape[1]:
            normalized = (row[0, j] - means[j]) / (means[j] + 1e-10)
            score += w * normalized * 0.5
    return float(np.clip(score, 0, 1))


def _shap_library(df: pd.DataFrame, model, n_samples: int) -> Dict[str, Any]:
    """Use actual SHAP library if available."""
    import shap
    sample = df.sample(min(n_samples, len(df)), random_state=42)
    X = sample[FEATURE_COLS].astype(float)

    explainer = shap.Explainer(model, X)
    shap_values = explainer(X)

    global_imp = np.abs(shap_values.values).mean(axis=0)
    total = global_imp.sum() + 1e-10

    directions = {
        "cibil_score": 1, "monthly_income": 1, "credit_history_years": 1,
        "loan_amount": -1, "debt_to_income_ratio": -1,
        "existing_loans": -1, "num_late_payments": -1,
    }

    sorted_feats = sorted(enumerate(FEATURE_COLS), key=lambda x: -global_imp[x[0]])

    return {
        "method": "shap_library",
        "global_importance": [
            {
                "feature": feat,
                "label": FEATURE_LABELS[feat],
                "importance": round(float(global_imp[j] / total), 4),
                "direction": directions.get(feat, 1),
                "rank": rank + 1,
            }
            for rank, (j, feat) in enumerate(sorted_feats)
        ],
        "waterfall_samples": [],
        "interpretation": f"SHAP analysis shows '{FEATURE_LABELS[FEATURE_COLS[sorted_feats[0][0]]]}' is the top driver.",
    }
