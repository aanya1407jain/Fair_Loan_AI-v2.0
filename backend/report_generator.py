"""
Professional PDF Report Generator v2.0
Generates RBI-ready compliance reports with model cards, mitigation steps, and full audit trail.
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import json

REPORTS_DIR = Path("./reports")
REPORTS_DIR.mkdir(exist_ok=True)


def generate_pdf_report(report: Dict[str, Any], audit_id: str) -> str:
    try:
        from reportlab.lib.pagesizes import A4
        return _generate_reportlab_pdf(report, audit_id)
    except ImportError:
        return _generate_html_report(report, audit_id)


def _generate_reportlab_pdf(report: Dict, audit_id: str) -> str:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak, KeepTogether
    )

    pdf_path = str(REPORTS_DIR / f"{audit_id}.pdf")
    doc = SimpleDocTemplate(
        pdf_path, pagesize=A4,
        topMargin=2*cm, bottomMargin=2.5*cm,
        leftMargin=2.5*cm, rightMargin=2.5*cm
    )

    BRAND_DARK = colors.HexColor("#0a0f1e")
    BRAND_BLUE = colors.HexColor("#1e3a5f")
    BRAND_ACCENT = colors.HexColor("#e94560")
    BRAND_GREEN = colors.HexColor("#06d6a0")
    BRAND_YELLOW = colors.HexColor("#ffd166")
    BRAND_LIGHT = colors.HexColor("#f8fafc")
    BRAND_GRAY = colors.HexColor("#64748b")

    styles = getSampleStyleSheet()

    def style(name, **kwargs):
        base = styles.get(name, styles["Normal"])
        return ParagraphStyle(f"custom_{name}_{id(kwargs)}", parent=base, **kwargs)

    title_s = style("Normal", fontSize=22, fontName="Helvetica-Bold", textColor=BRAND_DARK, spaceAfter=4)
    subtitle_s = style("Normal", fontSize=11, fontName="Helvetica", textColor=BRAND_GRAY, spaceAfter=2)
    h1_s = style("Normal", fontSize=15, fontName="Helvetica-Bold", textColor=BRAND_BLUE, spaceBefore=16, spaceAfter=8)
    h2_s = style("Normal", fontSize=12, fontName="Helvetica-Bold", textColor=BRAND_DARK, spaceBefore=10, spaceAfter=5)
    body_s = style("Normal", fontSize=9, fontName="Helvetica", textColor=BRAND_DARK, leading=14, spaceAfter=4)
    small_s = style("Normal", fontSize=8, fontName="Helvetica", textColor=BRAND_GRAY, leading=12)
    code_s = style("Normal", fontSize=8, fontName="Courier", textColor=BRAND_BLUE, backColor=colors.HexColor("#f0f4f8"), leading=12)

    W = 16 * cm  # usable width

    story = []

    # ── COVER PAGE ───────────────────────────────────────────────
    story.append(Spacer(1, 1*cm))

    # Header banner
    header_table = Table(
        [[Paragraph("FAIR LOAN AI", style("Normal", fontSize=28, fontName="Helvetica-Bold",
                                           textColor=colors.white)),
          Paragraph("v2.0", style("Normal", fontSize=12, fontName="Helvetica",
                                   textColor=colors.HexColor("#94a3b8")))]],
        colWidths=[13*cm, 3*cm]
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_DARK),
        ("PADDING", (0, 0), (-1, -1), 16),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.3*cm))

    # Accent line
    story.append(HRFlowable(width=W, thickness=4, color=BRAND_ACCENT))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("RBI Fair Lending Compliance Report", title_s))
    story.append(Paragraph("Credit Scoring Bias Audit — Regulatory Submission Document", subtitle_s))
    story.append(Spacer(1, 0.5*cm))

    # Meta info grid
    risk = report.get("risk_score", 0)
    risk_level = report.get("risk_level", "UNKNOWN")
    risk_color = BRAND_ACCENT if risk_level in ("CRITICAL", "HIGH") else BRAND_YELLOW if risk_level == "MEDIUM" else BRAND_GREEN
    compliant = report.get("rbi_compliant", False)

    meta_data = [
        ["Audit ID", report.get("audit_id", "N/A"),
         "Date", report.get("timestamp", "")[:10]],
        ["Model Type", report.get("model_type", "demo").upper(),
         "Dataset Size", f"{report.get('dataset', {}).get('total_samples', 0):,} samples"],
        ["Risk Score", f"{risk}/100",
         "Risk Level", risk_level],
        ["RBI Compliant", "✓ YES" if compliant else "✗ NO",
         "Audit Version", "Fair Loan AI v2.0"],
    ]
    t = Table(meta_data, colWidths=[3.5*cm, 5*cm, 3.5*cm, 4*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), BRAND_LIGHT),
        ("BACKGROUND", (2, 0), (2, -1), BRAND_LIGHT),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (1, 2), (1, 2), risk_color),
        ("TEXTCOLOR", (1, 3), (1, 3), BRAND_GREEN if compliant else BRAND_ACCENT),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    # Regulatory disclaimer
    story.append(Paragraph(
        "This report has been generated in accordance with the Reserve Bank of India (RBI) "
        "Master Circular on Fair Practices Code for Lenders (2023) and follows the Equal Credit "
        "Opportunity principles. The 4/5ths (80%) rule threshold is applied for disparate impact analysis.",
        style("Normal", fontSize=8, fontName="Helvetica-Oblique",
              textColor=BRAND_GRAY, borderPadding=10,
              backColor=colors.HexColor("#eff6ff"), leading=13)
    ))
    story.append(PageBreak())

    # ── EXECUTIVE SUMMARY ────────────────────────────────────────
    story.append(Paragraph("1. Executive Summary", h1_s))
    story.append(HRFlowable(width=W, thickness=1, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 0.3*cm))

    om = report.get("overall_metrics", {})
    exec_data = [
        ["Overall Accuracy", f"{om.get('accuracy', 0)*100:.1f}%",
         "F1 Score", f"{om.get('f1_score', 0)*100:.1f}%"],
        ["Total Applications", f"{om.get('total_samples', 0):,}",
         "Approvals", f"{om.get('total_approved', 0):,}"],
        ["Approval Rate", f"{om.get('approval_rate', 0)*100:.1f}%",
         "Rejections", f"{om.get('total_rejected', 0):,}"],
    ]
    t_exec = Table(exec_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
    t_exec.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_LIGHT),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#dbeafe")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#dbeafe")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bfdbfe")),
        ("PADDING", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ALIGN", (3, 0), (3, -1), "CENTER"),
    ]))
    story.append(t_exec)
    story.append(Spacer(1, 0.5*cm))

    # Bias summary
    bias_analysis = report.get("bias_analysis", {})
    critical_attrs = [a for a, d in bias_analysis.items() if d.get("severity") in ("CRITICAL", "HIGH")]
    if critical_attrs:
        story.append(Paragraph(
            f"⚠ CRITICAL FINDING: Significant bias detected in {', '.join(critical_attrs).upper()}. "
            "Immediate remediation required before production deployment.",
            style("Normal", fontSize=10, fontName="Helvetica-Bold",
                  textColor=BRAND_ACCENT, borderPadding=12,
                  backColor=colors.HexColor("#fff5f5"), leading=15)
        ))
    else:
        story.append(Paragraph(
            "✓ No critical bias violations detected. Model demonstrates acceptable fairness.",
            style("Normal", fontSize=10, fontName="Helvetica-Bold",
                  textColor=BRAND_GREEN, leading=14)
        ))

    story.append(Spacer(1, 0.5*cm))

    # ── MODEL CARD ───────────────────────────────────────────────
    story.append(Paragraph("2. Model Card", h1_s))
    story.append(HRFlowable(width=W, thickness=1, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 0.3*cm))

    dataset_info = report.get("dataset", {})
    model_card_data = [
        ["Field", "Value"],
        ["Model Name", "Credit Scoring Bias Audit Model"],
        ["Model Type", report.get("model_type", "demo").replace("_", " ").title()],
        ["Training Data", dataset_info.get("source", "synthetic_indian_demographics").replace("_", " ").title()],
        ["Dataset Size", f"{dataset_info.get('total_samples', 0):,} applicants"],
        ["Input Features", ", ".join(dataset_info.get("features", []))],
        ["Protected Attributes", "Gender, Religion, City Tier (proxy for geography/caste)"],
        ["Output", "Binary loan approval decision (0=Reject, 1=Approve)"],
        ["Evaluation Date", report.get("timestamp", "")[:10]],
        ["Audit Framework", "Fairlearn 0.10+ / RBI Fair Practices Code 2023"],
    ]
    t_mc = Table(model_card_data, colWidths=[5*cm, 11*cm])
    t_mc.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_mc)
    story.append(Spacer(1, 0.5*cm))

    # ── BIAS ANALYSIS ────────────────────────────────────────────
    story.append(Paragraph("3. Bias Analysis by Protected Attribute", h1_s))
    story.append(HRFlowable(width=W, thickness=1, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 0.3*cm))

    for attr, data in bias_analysis.items():
        severity = data.get("severity", "PASS")
        sev_color = BRAND_ACCENT if severity == "CRITICAL" else colors.HexColor("#f97316") if severity == "HIGH" else BRAND_YELLOW if severity == "MEDIUM" else BRAND_GREEN

        attr_block = []
        attr_block.append(Paragraph(
            f"{attr.replace('_', ' ').upper()} — <font color='{sev_color.hexval() if hasattr(sev_color,'hexval') else '#e94560'}'>{severity}</font>",
            h2_s
        ))
        attr_block.append(Paragraph(data.get("summary", ""), body_s))
        attr_block.append(Spacer(1, 0.2*cm))

        # Disparate Impact table
        di = data.get("disparate_impact", {})
        if di:
            di_rows = [["Group", "Approval Rate", "DI Ratio", "Count", "Status"]]
            for g, v in di.items():
                status = "⚠ FLAGGED" if v.get("flagged") else "✓ PASS"
                di_rows.append([
                    g,
                    f"{v.get('approval_rate', 0):.2%}",
                    f"{v.get('di_ratio', 0):.3f}",
                    str(v.get("count", 0)),
                    status,
                ])
            t_di = Table(di_rows, colWidths=[4*cm, 3.5*cm, 3*cm, 2.5*cm, 3*cm])
            t_di.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BRAND_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("TEXTCOLOR", (4, 1), (4, -1), BRAND_ACCENT),
            ]))
            attr_block.append(t_di)
            attr_block.append(Spacer(1, 0.3*cm))

        story.append(KeepTogether(attr_block))

    # ── MITIGATION PLAN ──────────────────────────────────────────
    story.append(Paragraph("4. Recommended Mitigation Steps", h1_s))
    story.append(HRFlowable(width=W, thickness=1, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 0.3*cm))

    for i, m in enumerate(report.get("mitigation_suggestions", []), 1):
        priority = m.get("priority", "LOW")
        p_color = BRAND_ACCENT if priority == "HIGH" else BRAND_YELLOW if priority == "MEDIUM" else BRAND_GREEN
        mit_block = [
            Paragraph(f"Step {i}: [{priority}] {m.get('technique', '')} — {m.get('attribute', '').upper()}", h2_s),
            Paragraph(m.get("description", ""), body_s),
        ]
        if m.get("fairlearn_api"):
            mit_block.append(Paragraph(f"API: {m['fairlearn_api']}", code_s))
        mit_block.append(Spacer(1, 0.3*cm))
        story.append(KeepTogether(mit_block))

    # ── MODEL INTEGRITY ──────────────────────────────────────────
    integrity = report.get("model_integrity", {})
    if integrity:
        story.append(PageBreak())
        story.append(Paragraph("5. Model Integrity Assessment", h1_s))
        story.append(HRFlowable(width=W, thickness=1, color=colors.HexColor("#e2e8f0")))
        story.append(Spacer(1, 0.3*cm))

        int_score = integrity.get("integrity_score", 100)
        int_level = integrity.get("integrity_level", "TRUSTED")
        int_color = BRAND_ACCENT if int_level in ("POISONED", "COMPROMISED") else BRAND_YELLOW if int_level == "SUSPECT" else BRAND_GREEN

        story.append(Paragraph(
            f"Integrity Score: {int_score}/100 — {int_level}",
            style("Normal", fontSize=14, fontName="Helvetica-Bold", textColor=int_color)
        ))
        story.append(Paragraph(integrity.get("summary", ""), body_s))
        story.append(Spacer(1, 0.3*cm))

        int_rows = [["Check", "Status", "Detail"]]
        for check in integrity.get("checks", []):
            status = check.get("status", "INFO")
            s_color = BRAND_ACCENT if status == "FAIL" else BRAND_YELLOW if status == "WARNING" else BRAND_GREEN
            int_rows.append([
                check.get("check", ""),
                status,
                check.get("detail", "")[:80],
            ])
        t_int = Table(int_rows, colWidths=[5*cm, 2.5*cm, 8.5*cm])
        t_int.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("WORDWRAP", (2, 1), (2, -1), True),
        ]))
        story.append(t_int)
        story.append(Spacer(1, 0.5*cm))

    # ── REGULATORY NOTES ─────────────────────────────────────────
    story.append(Paragraph("6. Regulatory Notes & Compliance Statement", h1_s))
    story.append(HRFlowable(width=W, thickness=1, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 0.3*cm))

    for note in report.get("regulatory_notes", []):
        story.append(Paragraph(f"• {note}", body_s))

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        f"Compliance Status: {'COMPLIANT' if report.get('rbi_compliant') else 'NON-COMPLIANT'} "
        f"— Risk Score {report.get('risk_score', 0)}/100",
        style("Normal", fontSize=12, fontName="Helvetica-Bold",
              textColor=BRAND_GREEN if report.get("rbi_compliant") else BRAND_ACCENT)
    ))

    # ── FOOTER ───────────────────────────────────────────────────
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width=W, thickness=1, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"Generated by Fair Loan AI v2.0 — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | "
        f"Audit ID: {report.get('audit_id', 'N/A')} | Confidential — For Regulatory Use Only",
        small_s
    ))

    doc.build(story)
    return pdf_path


def _generate_html_report(report: Dict, audit_id: str) -> str:
    html_path = str(REPORTS_DIR / f"{audit_id}.html")
    risk = report.get("risk_score", 0)
    risk_level = report.get("risk_level", "UNKNOWN")
    compliant = report.get("rbi_compliant", False)
    om = report.get("overall_metrics", {})

    bias_rows = ""
    for attr, data in report.get("bias_analysis", {}).items():
        severity = data.get("severity", "PASS")
        cls = "critical" if severity == "CRITICAL" else "high" if severity == "HIGH" else "medium" if severity == "MEDIUM" else "pass"
        bias_rows += f"<tr><td>{attr.replace('_',' ').title()}</td><td class='{cls}'>{severity}</td><td>{data.get('summary','')}</td></tr>"

    mit_rows = ""
    for m in report.get("mitigation_suggestions", []):
        mit_rows += f"<tr><td>[{m['priority']}]</td><td>{m['technique']}</td><td>{m['description']}</td></tr>"

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>RBI Compliance Report — {audit_id}</title>
<style>
  body{{font-family:'Segoe UI',sans-serif;max-width:960px;margin:40px auto;padding:0 20px;color:#1a202c;background:#fff}}
  .header{{background:#0a0f1e;color:white;padding:24px 32px;border-radius:8px 8px 0 0;display:flex;justify-content:space-between;align-items:center}}
  .header h1{{margin:0;font-size:24px}} .header span{{font-size:12px;color:#94a3b8}}
  .accent-bar{{height:4px;background:#e94560}}
  h2{{color:#1e3a5f;border-bottom:2px solid #e2e8f0;padding-bottom:8px;margin-top:32px}}
  table{{border-collapse:collapse;width:100%;margin:16px 0}}
  th{{background:#1e3a5f;color:white;padding:10px;text-align:left;font-size:13px}}
  td{{padding:9px 10px;border:1px solid #e2e8f0;font-size:13px}}
  tr:nth-child(even){{background:#f8fafc}}
  .critical{{color:#e94560;font-weight:bold}} .high{{color:#f97316;font-weight:bold}}
  .medium{{color:#f59e0b;font-weight:bold}} .pass{{color:#06d6a0;font-weight:bold}}
  .badge{{display:inline-block;padding:4px 12px;border-radius:20px;font-weight:bold;font-size:13px}}
  .badge-pass{{background:#dcfce7;color:#16a34a}} .badge-fail{{background:#fee2e2;color:#dc2626}}
  .footer{{margin-top:40px;padding:16px;background:#f8fafc;border-radius:8px;font-size:11px;color:#64748b;text-align:center}}
</style>
</head>
<body>
<div class="header">
  <div><h1>FAIR LOAN AI — RBI Compliance Report</h1>
  <span>Audit ID: {audit_id} | {report.get('timestamp','')[:10]}</span></div>
  <div><span class="badge {'badge-pass' if compliant else 'badge-fail'}">{'✓ RBI COMPLIANT' if compliant else '✗ NON-COMPLIANT'}</span></div>
</div>
<div class="accent-bar"></div>

<h2>1. Executive Summary</h2>
<table>
<tr><th>Risk Score</th><th>Risk Level</th><th>Accuracy</th><th>Approval Rate</th><th>Total Samples</th></tr>
<tr><td class="{'critical' if risk>=70 else 'high' if risk>=50 else 'medium' if risk>=30 else 'pass'}">{risk}/100</td>
<td class="{'critical' if risk_level in ('CRITICAL','HIGH') else 'pass'}">{risk_level}</td>
<td>{om.get('accuracy',0)*100:.1f}%</td><td>{om.get('approval_rate',0)*100:.1f}%</td>
<td>{om.get('total_samples',0):,}</td></tr>
</table>

<h2>2. Bias Analysis</h2>
<table><tr><th>Attribute</th><th>Severity</th><th>Summary</th></tr>{bias_rows}</table>

<h2>3. Mitigation Plan</h2>
<table><tr><th>Priority</th><th>Technique</th><th>Description</th></tr>{mit_rows}</table>

<h2>4. Regulatory Notes</h2>
<ul>{"".join(f"<li>{n}</li>" for n in report.get("regulatory_notes",[]))}</ul>

<div class="footer">Generated by Fair Loan AI v2.0 — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}<br>
Audit ID: {audit_id} | Confidential — For Regulatory Use Only</div>
</body></html>"""

    with open(html_path, "w") as f:
        f.write(html)
    return html_path
