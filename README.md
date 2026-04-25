# Fair Loan AI v2.0 — RegTech Bias Auditor

Advanced ML fairness auditing for Indian credit scoring models. Aligned with RBI Fair Lending Guidelines.

## Features
- **Disparate Impact Heatmap** — Red/Green grid across Gender × Religion × City Tier
- **Mitigation Engine** — ThresholdOptimizer before/after comparison
- **Counterfactual What-If** — Test individual fairness by flipping one attribute
- **Adversarial Robustness** — Detect model exploitation vulnerabilities
- **SHAP Waterfall Charts** — Feature attribution for rejection decisions
- **Accuracy-Fairness Pareto Curve** — Optimal operating point selection
- **Model Integrity Score** — Data poisoning & tampering detection
- **Human-in-the-Loop Queue** — Borderline case review dashboard
- **RBI Compliance PDF** — One-click regulatory report export

## Deployment

### Backend (Render)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```
Set env var: `FRONTEND_URL=https://your-vercel-url.vercel.app`

### Frontend (Vercel)
```bash
cd frontend
npm install
npm run build
```
Set env var: `VITE_API_URL=https://your-render-backend.onrender.com`

## API Documentation
Visit `/docs` on your backend URL for Swagger UI.

## Fairness Metrics
| Metric | Threshold | Standard |
|--------|-----------|----------|
| Disparate Impact | ≥ 0.80 | 4/5ths Rule |
| Demographic Parity Diff | ≤ 0.05 | NIST AI RMF |
| Equal Opportunity Gap | ≤ 0.10 | Equalized Odds |
