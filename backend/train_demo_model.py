"""
Train a demo credit scoring model (intentionally biased) for testing the audit tool.
Run: python train_demo_model.py
Outputs: models/demo_model.pkl
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("scikit-learn not installed. Install with: pip install scikit-learn")

import sys
sys.path.append(str(Path(__file__).parent))
from data_generator import generate_synthetic_data


FEATURE_COLS = [
    "cibil_score", "monthly_income", "loan_amount",
    "debt_to_income_ratio", "existing_loans",
    "credit_history_years", "num_late_payments",
    "city_tier",  # <-- intentionally included as a proxy for geography bias
]


def train_biased_model():
    print("Generating training data...")
    df = generate_synthetic_data(n_samples=10000, seed=123)

    X = df[FEATURE_COLS].values
    y = df["model_approved"].values  # biased labels

    print(f"Training on {len(df)} samples, approval rate: {y.mean():.2%}")

    if not HAS_SKLEARN:
        print("Cannot train — scikit-learn missing.")
        return

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", GradientBoostingClassifier(n_estimators=100, max_depth=4, random_state=42))
    ])

    model.fit(X, y)

    Path("models").mkdir(exist_ok=True)
    with open("models/demo_model.pkl", "wb") as f:
        pickle.dump(model, f)

    print("✓ Model saved to models/demo_model.pkl")
    print("  Upload this file to the dashboard to audit it!")

    # Quick eval
    preds = model.predict(X)
    acc = (preds == y).mean()
    print(f"  Training accuracy: {acc:.2%}")


class SimpleThresholdModel:
    """
    Fallback model if sklearn is not available.
    A rule-based model that intentionally has gender/geography bias.
    """
    def predict(self, X):
        # X columns: cibil, income, loan_amt, dti, existing_loans, credit_hist, late_pmts, city_tier
        scores = (
            (X[:, 0] - 300) / 600 * 0.4 +   # cibil
            np.clip(X[:, 1] / 100000, 0, 1) * 0.25 +
            np.clip(1 - X[:, 3], 0, 1) * 0.2 +
            np.clip(X[:, 5] / 20, 0, 1) * 0.1 -
            X[:, 6] * 0.02 -
            (X[:, 7] == 3) * 0.08  # city tier 3 penalty
        )
        return (scores > 0.5).astype(int)

    def predict_proba(self, X):
        preds = self.predict(X)
        proba = np.zeros((len(X), 2))
        proba[:, 1] = preds
        proba[:, 0] = 1 - preds
        return proba


if __name__ == "__main__":
    train_biased_model()
