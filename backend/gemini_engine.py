"""
Gemini AI Insights Engine
Uses Google Gemini 1.5 Flash to generate plain-English regulatory
narratives from the bias audit report. Purely additive — no existing
engine is modified.
"""

import os
import json
from typing import Dict, Any
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
_model = genai.GenerativeModel("gemini-1.5-flash")


def _build_prompt(report: Dict[str, Any], mode: str) -> str:
    bias = report.get("bias_analysis", {})
    metrics = report.get("overall_metrics", {})
    risk = report.get("risk_score", 0)
    rbi = report.get("rbi_compliant", False)
    mitigation = report.get("mitigation_suggestions", [])

    # Compact summary sent to Gemini (avoids token waste)
    summary = {
        "audit_id": report.get("audit_id"),
        "risk_score": risk,
        "rbi_compliant": rbi,
        "overall_metrics": metrics,
        "bias_summary": {
            attr: {
                "severity": data["severity"],
                "min_di_ratio": data["min_di_ratio"],
                "flagged_groups": data["flagged_groups"],
            }
            for attr, data in bias.items()
        },
        "mitigation_count": len(mitigation),
    }

    if mode == "narrative":
        return f"""
You are a RegTech compliance officer writing a formal RBI audit narrative for an Indian bank.

Given this bias audit result:
{json.dumps(summary, indent=2)}

Write a concise 3-paragraph regulatory narrative:
1. Executive summary of overall model fairness (1 sentence risk verdict, cite risk score and RBI compliance status)
2. Key bias findings by attribute — gender, religion, city_tier — explaining what the DI ratios mean in plain English for a loan officer
3. Recommended immediate actions citing RBI Fair Practices Code 2023

Be direct, formal, and under 250 words. Do not use bullet points. Do not repeat numbers already in the data without adding interpretation.
"""

    elif mode == "recommendations":
        return f"""
You are a senior ML fairness engineer. Given this loan model audit:
{json.dumps(summary, indent=2)}

Generate exactly 5 prioritized, actionable recommendations to fix the bias issues detected.
Format each as: [PRIORITY] Action — Reason

PRIORITY must be one of: CRITICAL / HIGH / MEDIUM / LOW
Be specific to Indian banking context and RBI guidelines.
Limit to 200 words total.
"""

    elif mode == "layman":
        return f"""
A loan applicant was rejected. Explain to them in simple, empathetic Hindi-English (Hinglish) why AI models can sometimes be unfair, and what the bank is doing to fix it. Keep it under 100 words. Use this context: risk_score={risk}, rbi_compliant={rbi}.
"""

    else:
        raise ValueError(f"Unknown mode: {mode}")


def generate_gemini_insights(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates three types of Gemini-powered insights from an audit report.
    Returns all three in one call to minimize latency.
    """
    results = {}
    for mode in ["narrative", "recommendations", "layman"]:
        try:
            prompt = _build_prompt(report, mode)
            response = _model.generate_content(prompt)
            results[mode] = response.text.strip()
        except Exception as e:
            results[mode] = f"[Gemini unavailable: {str(e)}]"

    return {
        "audit_id": report.get("audit_id"),
        "gemini_model": "gemini-1.5-flash",
        "regulatory_narrative": results["narrative"],
        "prioritized_recommendations": results["recommendations"],
        "applicant_explanation": results["layman"],
        "powered_by": "Google Gemini AI",
    }


def generate_counterfactual_explanation(counterfactual_result: Dict[str, Any]) -> str:
    """
    Takes output from run_counterfactual() and explains it in plain English.
    Call this from the /api/counterfactual endpoint optionally.
    """
    prompt = f"""
A loan applicant's decision was analyzed. Here is the what-if result:
{json.dumps(counterfactual_result, indent=2)}

In 2-3 sentences, explain to a bank compliance officer:
- Whether individual fairness was violated
- Why the decision may have flipped
- What this implies about proxy discrimination

Be factual and cite the specific attribute changed.
"""
    try:
        response = _model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"[Gemini explanation unavailable: {str(e)}]"
