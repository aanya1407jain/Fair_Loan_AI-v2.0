"""
Fair Loan AI — FastAPI Audit Engine v2.0
Advanced bias auditing with mitigation, counterfactual analysis,
adversarial robustness, and regulatory PDF export.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import json
import os
import pickle
import tempfile
import hashlib
from pathlib import Path
from typing import Dict, Any

from audit_engine import run_audit, FEATURE_COLS
from data_generator import generate_synthetic_data
from report_generator import generate_pdf_report
from mitigation_engine import run_mitigation, generate_tradeoff_curve
from counterfactual_engine import run_counterfactual
from adversarial_engine import run_adversarial_check
from model_integrity import compute_integrity_score
from shap_engine import compute_shap_values
import numpy as np


# ── Numpy-safe JSON encoder ───────────────────────────────────────────────────
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def np_safe_response(data: Any) -> JSONResponse:
    """Serialize data with NpEncoder and return a JSONResponse.
    This bypasses FastAPI's built-in jsonable_encoder which cannot
    handle numpy scalar types (numpy.bool_, numpy.int64, etc.)."""
    return JSONResponse(content=json.loads(json.dumps(data, cls=NpEncoder)))


# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Fair Loan AI — Bias Audit Engine",
    description="""
## Fair Loan AI v2.0 — RegTech Bias Auditor

Advanced credit scoring fairness auditor aligned with **RBI Fair Lending Guidelines**.

### Core Features
- **Disparate Impact Analysis** — 4/5ths rule across gender, religion, city tier
- **Equal Opportunity & Demographic Parity** auditing
- **Post-processing Mitigation** — ThresholdOptimizer before/after comparison
- **Counterfactual What-If** — flip one attribute to test individual fairness
- **Adversarial Robustness** — detect manipulation vulnerabilities
- **SHAP Feature Attribution** — waterfall charts explaining rejections
- **Model Integrity Score** — detect data poisoning & tampering
- **RBI Compliance PDF Export** — regulator-ready reports
    """,
    version="2.0.0",
    openapi_tags=[
        {"name": "audit",      "description": "Core bias audit endpoints"},
        {"name": "mitigation", "description": "Bias mitigation and trade-off analysis"},
        {"name": "explain",    "description": "Explainability and counterfactual analysis"},
        {"name": "security",   "description": "Adversarial robustness and model integrity"},
        {"name": "export",     "description": "Report generation and export"},
        {"name": "data",       "description": "Synthetic data generation"},
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

BASE_DIR    = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

_audit_cache: Dict[str, Any] = {}


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["audit"])
def root():
    return {"message": "Fair Loan AI Audit Engine v2.0", "version": "2.0.0", "docs": "/docs"}


@app.get("/api/demo-audit", tags=["audit"])
def demo_audit():
    df        = generate_synthetic_data(n_samples=5000, seed=42)
    report    = run_audit(df, model_type="demo")
    integrity = compute_integrity_score(df, None, None)
    report["model_integrity"] = integrity
    _audit_cache[report["audit_id"]] = {"report": report, "df": df}
    with open(REPORTS_DIR / f"{report['audit_id']}.json", "w") as f:
        json.dump(report, f, indent=2, cls=NpEncoder)
    return np_safe_response(report)


@app.post("/api/upload-model", tags=["audit"], summary="Upload model for bias audit")
async def upload_model(file: UploadFile = File(...)):
    if not file.filename.endswith(".pkl"):
        raise HTTPException(status_code=400, detail="Only .pkl files supported")
    contents  = await file.read()
    file_hash = hashlib.sha256(contents).hexdigest()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as f:
            model = pickle.load(f)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to load model: {str(e)}")
    finally:
        os.unlink(tmp_path)
    df = generate_synthetic_data(n_samples=5000, seed=42)
    report = run_audit(df, model=model, model_type="uploaded")
    report["model_hash"] = file_hash[:16]
    integrity = compute_integrity_score(df, model, file_hash)
    report["model_integrity"] = integrity
    _audit_cache[report["audit_id"]] = {"report": report, "df": df, "model": model}
    with open(REPORTS_DIR / f"{report['audit_id']}.json", "w") as f:
        json.dump(report, f, indent=2, cls=NpEncoder)
    return np_safe_response(report)


@app.post("/api/audit-json", tags=["audit"])
async def audit_json(payload: dict = Body(...)):
    n_samples = payload.get("n_samples", 5000)
    seed      = payload.get("seed", 42)
    df        = generate_synthetic_data(n_samples=n_samples, seed=seed)
    report    = run_audit(df, model_type="demo")
    _audit_cache[report["audit_id"]] = {"report": report, "df": df}
    return np_safe_response(report)


@app.post("/api/mitigation/{audit_id}", tags=["mitigation"],
          summary="Apply ThresholdOptimizer mitigation")
def apply_mitigation(audit_id: str, payload: dict = Body(default={})):
    if audit_id not in _audit_cache:
        df     = generate_synthetic_data(n_samples=5000, seed=42)
        report = run_audit(df, model_type="demo")
        _audit_cache[audit_id] = {"report": report, "df": df}
    cached         = _audit_cache[audit_id]
    df             = cached["df"]
    model          = cached.get("model", None)
    sensitive_attr = payload.get("sensitive_attr", "gender")
    constraint     = payload.get("constraint", "demographic_parity")
    result         = run_mitigation(df, model, sensitive_attr=sensitive_attr, constraint=constraint)
    return np_safe_response(result)


@app.get("/api/tradeoff-curve/{audit_id}", tags=["mitigation"],
         summary="Accuracy vs Fairness Pareto curve")
def tradeoff_curve(audit_id: str):
    if audit_id not in _audit_cache:
        df = generate_synthetic_data(n_samples=5000, seed=42)
        _audit_cache[audit_id] = {"df": df}
    df    = _audit_cache[audit_id]["df"]
    model = _audit_cache[audit_id].get("model", None)
    curve = generate_tradeoff_curve(df, model)
    return np_safe_response({"tradeoff_curve": curve})


@app.post("/api/counterfactual", tags=["explain"],
          summary="Counterfactual what-if analysis")
def counterfactual_analysis(payload: dict = Body(...)):
    applicant_index  = payload.get("applicant_index", 0)
    change_attribute = payload.get("change_attribute", "gender")
    change_to        = payload.get("change_to", "Male")
    audit_id         = payload.get("audit_id", "")
    if audit_id and audit_id in _audit_cache:
        df    = _audit_cache[audit_id]["df"]
        model = _audit_cache[audit_id].get("model", None)
    else:
        df    = generate_synthetic_data(n_samples=5000, seed=42)
        model = None
    result = run_counterfactual(df, model, applicant_index, change_attribute, change_to)
    return np_safe_response(result)


@app.get("/api/shap/{audit_id}", tags=["explain"],
         summary="SHAP feature attribution")
def shap_attribution(audit_id: str, n_samples: int = 100):
    if audit_id in _audit_cache:
        df    = _audit_cache[audit_id]["df"]
        model = _audit_cache[audit_id].get("model", None)
    else:
        df    = generate_synthetic_data(n_samples=5000, seed=42)
        model = None
    result = compute_shap_values(df, model, n_samples=n_samples)
    return np_safe_response(result)


@app.get("/api/rejected-applications/{audit_id}", tags=["explain"],
         summary="List rejected applications")
def get_rejected_applications(audit_id: str, limit: int = 20):
    if audit_id in _audit_cache:
        df    = _audit_cache[audit_id]["df"].copy()
        model = _audit_cache[audit_id].get("model", None)
    else:
        df    = generate_synthetic_data(n_samples=5000, seed=42)
        model = None
    if model is not None:
        from audit_engine import _predict_with_model
        X     = df[FEATURE_COLS].astype(float)
        preds = _predict_with_model(model, X)
    else:
        preds = df["model_approved"].values
    rejected = df[preds == 0].head(limit)
    records  = []
    for idx, row in rejected.iterrows():
        records.append({
            "index":                int(idx),
            "applicant_id":         row["applicant_id"],
            "gender":               row["gender"],
            "age":                  int(row["age"]),
            "religion":             row["religion"],
            "city_tier":            int(row["city_tier"]),
            "city":                 row["city"],
            "cibil_score":          int(row["cibil_score"]),
            "monthly_income":       int(row["monthly_income"]),
            "loan_amount":          int(row["loan_amount"]),
            "debt_to_income_ratio": float(row["debt_to_income_ratio"]),
            "model_score":          float(row.get("model_score", 0)),
            "fair_approved":        int(row["fair_approved"]),
        })
    return np_safe_response({"rejected_applications": records, "total": len(records)})


@app.get("/api/adversarial/{audit_id}", tags=["security"],
         summary="Adversarial robustness check")
def adversarial_check(audit_id: str):
    if audit_id in _audit_cache:
        df    = _audit_cache[audit_id]["df"]
        model = _audit_cache[audit_id].get("model", None)
    else:
        df    = generate_synthetic_data(n_samples=5000, seed=42)
        model = None
    result = run_adversarial_check(df, model)
    return np_safe_response(result)


@app.get("/api/model-integrity/{audit_id}", tags=["security"],
         summary="Model integrity check")
def model_integrity_check(audit_id: str):
    if audit_id in _audit_cache:
        cached = _audit_cache[audit_id]
        return np_safe_response(cached.get("report", {}).get("model_integrity", {}))
    raise HTTPException(status_code=404, detail="Audit not found. Run an audit first.")


@app.get("/api/export-pdf/{audit_id}", tags=["export"],
         summary="Download RBI Compliance PDF")
def export_pdf(audit_id: str):
    report_path = REPORTS_DIR / f"{audit_id}.json"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Audit report not found")
    with open(report_path) as f:
        report = json.load(f)
    pdf_path = generate_pdf_report(report, audit_id)
    return FileResponse(pdf_path, media_type="application/pdf",
                        filename=f"RBI_Compliance_Report_{audit_id}.pdf")


@app.get("/api/export-json/{audit_id}", tags=["export"],
         summary="Download audit as JSON")
def export_json(audit_id: str):
    report_path = REPORTS_DIR / f"{audit_id}.json"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Audit report not found")
    return FileResponse(str(report_path), media_type="application/json",
                        filename=f"audit_report_{audit_id}.json")


@app.get("/api/generate-data", tags=["data"],
         summary="Generate synthetic Indian banking data")
def generate_data(n_samples: int = 1000, seed: int = 42):
    df      = generate_synthetic_data(n_samples=n_samples, seed=seed)
    preview = df.head(100).to_dict(orient="records")
    return np_safe_response({
        "total_rows": len(df),
        "columns":    list(df.columns),
        "preview":    preview,
        "statistics": {
            "gender_distribution":    df["gender"].value_counts().to_dict(),
            "city_tier_distribution": df["city_tier"].value_counts().to_dict(),
            "religion_distribution":  df["religion"].value_counts().to_dict(),
            "approval_rate":          round(float(df["model_approved"].mean()), 4),
        }
    })


@app.get("/api/manual-review-queue/{audit_id}", tags=["audit"],
         summary="Human-in-the-loop review queue")
def manual_review_queue(audit_id: str, limit: int = 10):
    if audit_id in _audit_cache:
        df = _audit_cache[audit_id]["df"].copy()
    else:
        df = generate_synthetic_data(n_samples=5000, seed=42)
    borderline = df[(df["model_approved"] == 0) & (df["fair_approved"] == 1)].head(limit)
    cases = []
    for idx, row in borderline.iterrows():
        score = float(row.get("model_score", 50))
        flags = []
        if row["gender"] == "Female":
            flags.append("Possible gender bias — fair model approves")
        if row["city_tier"] == 3:
            flags.append(f"Tier-3 city ({row['city']}) disadvantage detected")
        if row["religion"] in ["Muslim", "Christian"]:
            flags.append(f"Religion proxy variable risk ({row['religion']})")
        if not flags:
            flags.append("Borderline score — near decision boundary")
        cases.append({
            "case_id":             f"HR-{idx:04d}",
            "applicant_id":        row["applicant_id"],
            "gender":              row["gender"],
            "age":                 int(row["age"]),
            "religion":            row["religion"],
            "city_tier":           int(row["city_tier"]),
            "city":                row["city"],
            "cibil_score":         int(row["cibil_score"]),
            "monthly_income":      int(row["monthly_income"]),
            "loan_amount":         int(row["loan_amount"]),
            "model_decision":      "REJECTED",
            "fair_model_decision": "APPROVED",
            "risk_flags":          flags,
            "bias_score":          round(min(abs(score - 55) / 45 * 100, 99), 1),
            "review_priority":     "HIGH" if row["gender"] == "Female" or row["city_tier"] == 3 else "MEDIUM",
        })
    return np_safe_response({"queue": cases, "total": len(cases)})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
