"""
Counterfactual What-If Analysis Engine
Allows changing one attribute on a rejected application to see if decision flips.
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

CHANGEABLE_ATTRS = {
    "gender": ["Male", "Female", "Other"],
    "religion": ["Hindu", "Muslim", "Christian", "Sikh", "Buddhist", "Jain", "Other"],
    "city_tier": [1, 2, 3],
    "city": None,  # free text
    "age": None,
    "education": ["Below 10th", "10th Pass", "12th Pass", "Graduate", "Post-Graduate", "Professional"],
    "employment_type": ["Salaried", "Self-Employed", "Business", "Farmer", "Daily-Wage", "Unemployed"],
}


def _predict_single(df_row: pd.DataFrame, model=None) -> tuple:
    """Returns (prediction, score)"""
    if model is not None:
        X = df_row[FEATURE_COLS].astype(float)
        if hasattr(model, "predict_proba"):
            prob = model.predict_proba(X)[0, 1]
            return int(prob >= 0.5), round(float(prob * 100), 2)
        pred = model.predict(X)[0]
        return int(pred), float(pred * 100)
    else:
        # Demo mode: use model_approved / model_score
        pred = int(df_row["model_approved"].iloc[0])
        score = float(df_row["model_score"].iloc[0])
        return pred, score


def run_counterfactual(
    df: pd.DataFrame,
    model,
    applicant_index: int,
    change_attribute: str,
    change_to: Any,
) -> Dict[str, Any]:
    """
    Runs counterfactual analysis: changes one attribute and checks if decision flips.
    """
    if applicant_index >= len(df):
        applicant_index = 0

    original_row = df.iloc[[applicant_index]].copy()
    modified_row = original_row.copy()

    # Apply the change
    original_value = original_row[change_attribute].iloc[0]
    modified_row[change_attribute] = change_to

    # If changing city_tier, also update model_score heuristically
    if change_attribute == "city_tier":
        tier_boost = {1: 5, 2: 0, 3: -5}
        score_delta = tier_boost.get(int(change_to), 0) - tier_boost.get(int(original_value), 0)
        if "model_score" in modified_row.columns:
            modified_row["model_score"] = np.clip(
                float(modified_row["model_score"].iloc[0]) + score_delta, 0, 100
            )

    # If changing gender, adjust income heuristically (reflects the bias in the model)
    if change_attribute == "gender" and model is None:
        income_map = {"Male": 1.0, "Female": 0.78, "Other": 0.85}
        orig_mult = income_map.get(str(original_value), 1.0)
        new_mult = income_map.get(str(change_to), 1.0)
        if orig_mult > 0:
            modified_row["monthly_income"] = int(
                float(original_row["monthly_income"].iloc[0]) * new_mult / orig_mult
            )
        # Adjust score by gender bias amount
        if "model_score" in modified_row.columns:
            score_delta = (new_mult - orig_mult) * 15
            modified_row["model_score"] = np.clip(
                float(original_row["model_score"].iloc[0]) + score_delta, 0, 100
            )
        if "model_approved" in modified_row.columns:
            modified_row["model_approved"] = int(float(modified_row["model_score"].iloc[0]) > 55)

    orig_pred, orig_score = _predict_single(original_row, model)
    new_pred, new_score = _predict_single(modified_row, model)

    decision_flipped = orig_pred != new_pred

    # Identify proxy variable risk
    proxy_warning = None
    if change_attribute in ("gender", "religion", "city_tier") and decision_flipped:
        proxy_warning = (
            f"⚠ Decision flipped when changing {change_attribute} from "
            f"'{original_value}' to '{change_to}'. "
            f"This indicates the model is using {change_attribute} as a discriminatory feature "
            f"or that correlated features (like monthly_income) act as proxy variables."
        )

    # Build feature comparison
    feature_comparison = {}
    for col in FEATURE_COLS + [change_attribute]:
        orig_val = original_row[col].iloc[0] if col in original_row.columns else "N/A"
        new_val = modified_row[col].iloc[0] if col in modified_row.columns else "N/A"
        feature_comparison[col] = {
            "original": orig_val if not isinstance(orig_val, (np.integer, np.floating)) else float(orig_val),
            "modified": new_val if not isinstance(new_val, (np.integer, np.floating)) else float(new_val),
            "changed": col == change_attribute or orig_val != new_val,
        }

    return {
        "applicant_index": applicant_index,
        "applicant_id": str(original_row["applicant_id"].iloc[0]),
        "change_attribute": change_attribute,
        "original_value": str(original_value),
        "new_value": str(change_to),
        "original_decision": "APPROVED" if orig_pred == 1 else "REJECTED",
        "new_decision": "APPROVED" if new_pred == 1 else "REJECTED",
        "original_score": orig_score,
        "new_score": new_score,
        "score_delta": round(new_score - orig_score, 2),
        "decision_flipped": decision_flipped,
        "proxy_warning": proxy_warning,
        "individual_fairness_violation": decision_flipped and change_attribute in ("gender", "religion"),
        "feature_comparison": feature_comparison,
        "interpretation": (
            f"Changing {change_attribute} from '{original_value}' to '{change_to}' "
            f"{'FLIPPED the decision from REJECTED → APPROVED' if decision_flipped and new_pred == 1 else 'FLIPPED the decision from APPROVED → REJECTED' if decision_flipped else 'did NOT change the decision'}. "
            f"Score changed by {new_score - orig_score:+.1f} points."
        ),
        "available_changes": CHANGEABLE_ATTRS.get(change_attribute, []),
    }
