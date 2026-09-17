import io
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

SEVERITY_COLORS = {
    "LOW": colors.HexColor("#2563eb"),
    "MEDIUM": colors.HexColor("#d97706"),
    "HIGH": colors.HexColor("#dc2626"),
    "CRITICAL": colors.HexColor("#7f1d1d"),
}


def generate_pdf_report(analysis: Dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleCustom", parent=styles["Title"], fontSize=20)
    h2 = ParagraphStyle("H2Custom", parent=styles["Heading2"], spaceBefore=14, spaceAfter=6)
    normal = styles["Normal"]

    story = []
    story.append(Paragraph("CodeGuard AI — Code Quality Report", title_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"File: {analysis.get('filename')}", normal))
    story.append(Paragraph(f"Language: {analysis.get('language')}", normal))
    story.append(Paragraph(f"Date: {analysis.get('created_at')}", normal))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Overall Results", h2))
    result_table = Table([
        ["Quality Score", f"{analysis.get('quality_score')} / 100"],
        ["Predicted Defect Risk", f"{analysis.get('risk_level')} ({analysis.get('risk_score')}/100)"],
    ], colWidths=[220, 220])
    result_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(result_table)

    sub_scores = analysis.get("sub_scores") or {}
    if sub_scores:
        story.append(Paragraph("Quality Sub-Scores", h2))
        rows = [["Dimension", "Score"]] + [[k.title(), f"{v}/100"] for k, v in sub_scores.items()]
        t = Table(rows, colWidths=[220, 220])
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
        ]))
        story.append(t)

    metrics = analysis.get("metrics") or {}
    if metrics:
        story.append(Paragraph("Code Metrics", h2))
        metric_rows = [
            ["Lines of Code", metrics.get("loc")],
            ["Functions", metrics.get("function_count")],
            ["Classes", metrics.get("class_count")],
            ["Avg Complexity", metrics.get("avg_complexity")],
            ["Max Complexity", metrics.get("max_complexity")],
            ["Avg Function Length", metrics.get("avg_function_length")],
            ["Max Function Length", metrics.get("max_function_length")],
            ["Max Nesting Depth", metrics.get("max_nesting_depth")],
            ["Maintainability Index", metrics.get("maintainability_index")],
        ]
        t = Table([["Metric", "Value"]] + [[str(a), str(b)] for a, b in metric_rows], colWidths=[220, 220])
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        story.append(t)

    findings = analysis.get("findings") or []
    if findings:
        story.append(Paragraph("Code Smells", h2))
        for f in findings:
            line_str = f"Line {f['line']}" if f.get("line") else "Line: N/A"
            story.append(Paragraph(
                f"<b>[{f['severity']}] {f['title']}</b> ({line_str}) — {f['description']}", normal
            ))
            story.append(Spacer(1, 4))

    sec = analysis.get("security_findings") or []
    if sec:
        story.append(Paragraph("Security Findings (Basic Security Pattern Analysis)", h2))
        for f in sec:
            line_str = f"Line {f['line']}" if f.get("line") else "Line: N/A"
            story.append(Paragraph(
                f"<b>[{f['severity']}] {f['issue']}</b> ({line_str}) — {f['explanation']}", normal
            ))
            story.append(Spacer(1, 4))

    recs = analysis.get("recommendations") or []
    if recs:
        story.append(Paragraph("Recommendations", h2))
        for r in recs:
            story.append(Paragraph(f"<b>{r['priority_label']}</b> — {r['recommendation']}", normal))
            story.append(Spacer(1, 4))

    explanation = analysis.get("ai_explanation")
    if explanation:
        story.append(Paragraph("AI Explanation", h2))
        story.append(Paragraph(explanation, normal))

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Disclaimer: Defect Risk is a model-based estimate derived from measurable code-quality "
        "signals, not a guarantee of future bugs. Security findings reflect basic pattern "
        "analysis only and do not replace a full security audit.",
        ParagraphStyle("Disclaimer", parent=normal, fontSize=8, textColor=colors.grey),
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
