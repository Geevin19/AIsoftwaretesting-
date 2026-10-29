"""
PDF Report Renderer (ReportLab Platypus).
Generates an IEEE 829 / ISO 29119 compliant formal Software Test Report.
Uses A4 sizing, 2.5cm margins, running headers/footers with 'Page X of Y',
color-coded status badges, and embedded in-memory Matplotlib charts.
"""
import io
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
    KeepTogether,
    HRFlowable
)
from reportlab.pdfgen import canvas
from services.report_builder import StructuredTestReport


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that tracks total page count and prints running
    headers and footers on all pages after the cover page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count: int):
        if self._pageNumber == 1:
            # Skip running header and footer on the cover page
            return

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header (Top of page)
        report_title = getattr(self, "report_title", "Software Test Summary Report")
        doc_id = getattr(self, "doc_id", "TR-20261030-001")
        self.drawString(2.5 * cm, A4[1] - 1.5 * cm, report_title)
        self.drawRightString(A4[0] - 2.5 * cm, A4[1] - 1.5 * cm, doc_id)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(2.5 * cm, A4[1] - 1.7 * cm, A4[0] - 2.5 * cm, A4[1] - 1.7 * cm)

        # Footer (Bottom of page)
        self.line(2.5 * cm, 1.8 * cm, A4[0] - 2.5 * cm, 1.8 * cm)
        self.drawString(2.5 * cm, 1.3 * cm, "CONFIDENTIAL — FOR INTERNAL USE ONLY")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(A4[0] - 2.5 * cm, 1.3 * cm, page_text)
        self.restoreState()


def render_pdf_report(report: StructuredTestReport) -> bytes:
    """Renders structured report object to binary PDF stream."""
    buffer = io.BytesIO()

    # 2.5 cm margins on A4 (595.27 x 841.89 points)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    # Styles
    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#1e3a8a")     # Muted deep blue for headings
    c_text = colors.HexColor("#1e293b")        # Slate-900 body
    c_muted = colors.HexColor("#64748b")       # Slate-500
    c_th_bg = colors.HexColor("#1e293b")       # Dark grey table header
    c_border = colors.HexColor("#cbd5e1")      # Slate-300 border
    c_code_bg = colors.HexColor("#f8fafc")     # Light grey code block background

    style_title = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=c_primary,
        spaceAfter=12
    )

    style_subtitle = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=13,
        leading=16,
        textColor=c_muted,
        spaceAfter=24
    )

    style_h1 = ParagraphStyle(
        "ReportH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    style_h2 = ParagraphStyle(
        "ReportH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    style_body = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=c_text,
        spaceAfter=6
    )

    style_table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    style_table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=c_text
    )

    style_table_code = ParagraphStyle(
        "TableCode",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#0f172a")
    )

    style_code_block = ParagraphStyle(
        "CodeBlock",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
        backColor=c_code_bg,
        borderPadding=6,
        spaceAfter=8
    )

    story = []

    # -----------------------------------------------------------------------
    # COVER PAGE
    # -----------------------------------------------------------------------
    story.append(Spacer(1, 3.5 * cm))
    story.append(Paragraph(report.metadata.report_title, style_title))
    story.append(Paragraph(f"Project: {report.metadata.project_name}", style_subtitle))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=4, spaceAfter=24))

    meta_table_data = [
        [Paragraph("<b>Document Identifier:</b>", style_table_cell), Paragraph(report.metadata.document_id, style_table_cell)],
        [Paragraph("<b>Standard / Specification:</b>", style_table_cell), Paragraph("IEEE 829-2008 / ISO/IEC/IEEE 29119-3", style_table_cell)],
        [Paragraph("<b>Version / Release:</b>", style_table_cell), Paragraph(report.metadata.version, style_table_cell)],
        [Paragraph("<b>Execution Date:</b>", style_table_cell), Paragraph(report.metadata.test_date, style_table_cell)],
        [Paragraph("<b>Prepared By:</b>", style_table_cell), Paragraph(report.metadata.prepared_by, style_table_cell)],
        [Paragraph("<b>Reviewed By:</b>", style_table_cell), Paragraph(report.metadata.reviewed_by, style_table_cell)],
        [Paragraph("<b>Organization / Dept:</b>", style_table_cell), Paragraph(report.metadata.organization, style_table_cell)],
        [Paragraph("<b>Engineering Verdict:</b>", style_table_cell),
         Paragraph(f"<font color='{report.verdict_color}'><b>{report.verdict}</b></font>", style_table_cell)],
    ]

    t_meta = Table(meta_table_data, colWidths=[5.0 * cm, 10.5 * cm])
    t_meta.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
    ]))
    story.append(t_meta)

    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph("<b>CONFIDENTIALITY NOTICE:</b> The information contained in this document is intended solely for authorized personnel. Unauthorized distribution is strictly prohibited.", style_body))
    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # DOCUMENT CONTROL & TOC
    # -----------------------------------------------------------------------
    story.append(Paragraph("Document Control", style_h1))
    story.append(Paragraph("<b>Revision History</b>", style_h2))
    
    rev_data = [
        [Paragraph("Version", style_table_header), Paragraph("Date", style_table_header), Paragraph("Author", style_table_header), Paragraph("Summary of Changes", style_table_header)],
        [Paragraph("1.0", style_table_cell), Paragraph(report.metadata.test_date, style_table_cell), Paragraph(report.metadata.prepared_by, style_table_cell), Paragraph("Initial baseline automated software test report.", style_table_cell)]
    ]
    t_rev = Table(rev_data, colWidths=[2.0 * cm, 3.0 * cm, 4.0 * cm, 6.5 * cm])
    t_rev.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_th_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_rev)

    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Approval & Sign-off Status</b>", style_h2))
    appr_data = [
        [Paragraph("Role", style_table_header), Paragraph("Name", style_table_header), Paragraph("Organization", style_table_header), Paragraph("Approval Status", style_table_header)],
        [Paragraph("Lead QA Tester", style_table_cell), Paragraph(report.metadata.prepared_by, style_table_cell), Paragraph(report.metadata.organization, style_table_cell), Paragraph("Completed", style_table_cell)],
        [Paragraph("Technical Reviewer", style_table_cell), Paragraph(report.metadata.reviewed_by, style_table_cell), Paragraph(report.metadata.organization, style_table_cell), Paragraph("Pending Signature", style_table_cell)],
    ]
    t_appr = Table(appr_data, colWidths=[4.0 * cm, 4.0 * cm, 4.5 * cm, 3.0 * cm])
    t_appr.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_th_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_appr)

    story.append(Spacer(1, 14))
    story.append(Paragraph("Table of Contents", style_h1))
    toc_entries = [
        ("1. Introduction", "3"),
        ("   1.1 Purpose of this document", "3"),
        ("   1.2 Scope of Testing", "3"),
        ("   1.3 Definitions and Abbreviations", "3"),
        ("   1.4 Applicable Standards and References", "3"),
        ("2. Executive Summary", "4"),
        ("3. Test Items and Environment", "4"),
        ("4. Test Approach & Methodology", "5"),
        ("5. Test Case Summary & Metrics", "5"),
        ("6. Detailed Test Execution Results", "6"),
        ("7. Defect Report & Root Cause Analysis", "7"),
        ("8. Requirements / Traceability Matrix", "8"),
        ("9. Quality Metrics & Coverage Analysis", "8"),
        ("10. Regression Comparison", "9"),
        ("11. Risks, Limitations and Assumptions", "9"),
        ("12. Recommendations and Conclusion", "10"),
        ("13. Formal Sign-off", "10"),
        ("Appendix A: Pytest Test Suite Definitions", "11"),
        ("Appendix B: AI-Assisted Fix Proposals", "12"),
    ]
    toc_data = [[Paragraph(entry[0], style_table_cell), Paragraph(entry[1], style_table_cell)] for entry in toc_entries]
    t_toc = Table(toc_data, colWidths=[14.0 * cm, 1.5 * cm])
    t_toc.setStyle(TableStyle([
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))
    story.append(t_toc)
    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # 1. INTRODUCTION
    # -----------------------------------------------------------------------
    story.append(Paragraph("1. Introduction", style_h1))
    
    story.append(Paragraph("1.1 Purpose of this document", style_h2))
    story.append(Paragraph(
        "This document provides a formal Test Summary Report (TSR) in compliance with IEEE 829-2008 and "
        "ISO/IEC/IEEE 29119-3 standards. It consolidates the empirical execution outcomes, defect classifications, "
        "and quality assurance metrics resulting from automated dynamic testing conducted on the target software system.",
        style_body
    ))

    story.append(Paragraph("1.2 Scope of Testing", style_h2))
    files_str = ", ".join([f.path for f in report.files]) if report.files else "Integrated source modules"
    story.append(Paragraph(
        f"The testing scope encompassed {len(report.files)} source file(s) ({files_str}) and {len(report.tested_functions)} "
        f"public function/method interfaces. Testing evaluated typical business logic flows, edge limit boundaries, "
        f"and exception-raising error scenarios.",
        style_body
    ))

    story.append(Paragraph("1.3 Definitions and Abbreviations", style_h2))
    def_data = [
        [Paragraph("Term", style_table_header), Paragraph("Formal Definition", style_table_header)],
        [Paragraph("PASS", style_table_cell), Paragraph("Execution completed with output matching expected specification within 5s timeout.", style_table_cell)],
        [Paragraph("FAIL", style_table_cell), Paragraph("Execution completed but actual return value differed from the required expectation.", style_table_cell)],
        [Paragraph("ERROR", style_table_cell), Paragraph("Execution terminated with an unhandled exception or timed out.", style_table_cell)],
        [Paragraph("Boundary Test", style_table_cell), Paragraph("Verification of limits (zero, minimum, off-by-one, empty collections) derived from AST comparison conditions.", style_table_cell)],
        [Paragraph("AST", style_table_cell), Paragraph("Abstract Syntax Tree — Python standard library static structural representation of code.", style_table_cell)],
    ]
    t_def = Table(def_data, colWidths=[3.5 * cm, 12.0 * cm])
    t_def.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_th_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_def)

    story.append(Paragraph("1.4 Applicable Standards and References", style_h2))
    story.append(Paragraph(
        "• IEEE Std 829-2008: IEEE Standard for Software and System Test Documentation.<br/>"
        "• ISO/IEC/IEEE 29119-3:2013: Software and systems engineering — Software testing — Part 3: Test documentation.<br/>"
        "• PEP 8 / PEP 484: Python Style and Type Hinting Specifications.",
        style_body
    ))
    story.append(Spacer(1, 10))

    # -----------------------------------------------------------------------
    # 2. EXECUTIVE SUMMARY
    # -----------------------------------------------------------------------
    story.append(Paragraph("2. Executive Summary", style_h1))
    story.append(Paragraph(report.executive_summary_text, style_body))

    # Key Metrics Table
    exec_metrics_data = [
        [Paragraph("Metric", style_table_header), Paragraph("Value", style_table_header), Paragraph("Quality Criterion", style_table_header)],
        [Paragraph("Total Executed Tests", style_table_cell), Paragraph(str(report.total_tests), style_table_cell), Paragraph("All generated test cases", style_table_cell)],
        [Paragraph("Passed Test Cases", style_table_cell), Paragraph(f"<font color='#15803d'><b>{report.passed_tests}</b></font>", style_table_cell), Paragraph(f"{report.pass_percent}% of total", style_table_cell)],
        [Paragraph("Failed Test Cases", style_table_cell), Paragraph(f"<font color='#b91c1c'><b>{report.failed_tests}</b></font>", style_table_cell), Paragraph("Functional logic divergence", style_table_cell)],
        [Paragraph("Execution Errors / Crashes", style_table_cell), Paragraph(f"<font color='#b45309'><b>{report.error_tests}</b></font>", style_table_cell), Paragraph("Unhandled exceptions / timeouts", style_table_cell)],
        [Paragraph("Acceptance Pass Threshold", style_table_cell), Paragraph(f"{report.metadata.pass_threshold}%", style_table_cell), Paragraph("Target compliance benchmark", style_table_cell)],
        [Paragraph("Overall Engineering Verdict", style_table_cell),
         Paragraph(f"<font color='{report.verdict_color}'><b>{report.verdict}</b></font>", style_table_cell),
         Paragraph(report.verdict_desc, style_table_cell)],
    ]
    t_em = Table(exec_metrics_data, colWidths=[5.0 * cm, 3.5 * cm, 7.0 * cm])
    t_em.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_th_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_em)
    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # 3. TEST ITEMS AND ENVIRONMENT
    # -----------------------------------------------------------------------
    story.append(Paragraph("3. Test Items and Environment", style_h1))
    story.append(Paragraph("<b>Table of Target Modules and Tested Interfaces</b>", style_h2))

    items_data = [
        [Paragraph("Module / File", style_table_header), Paragraph("Target Function", style_table_header), Paragraph("Branches", style_table_header), Paragraph("Tests Executed", style_table_header), Paragraph("Status", style_table_header)]
    ]
    for fn in report.tested_functions:
        st_color = "#15803d" if fn["failed_count"] == 0 else "#b91c1c"
        st_text = "PASS" if fn["failed_count"] == 0 else f"{fn['failed_count']} FAIL"
        items_data.append([
            Paragraph(fn["file"], style_table_code),
            Paragraph(fn["display_name"], style_table_code),
            Paragraph(str(fn["branches"]), style_table_cell),
            Paragraph(str(fn["tests_count"]), style_table_cell),
            Paragraph(f"<font color='{st_color}'><b>{st_text}</b></font>", style_table_cell)
        ])
    t_items = Table(items_data, colWidths=[4.0 * cm, 5.0 * cm, 2.0 * cm, 2.5 * cm, 2.0 * cm], repeatRows=1)
    t_items.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_th_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_items)

    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Execution Environment Details</b>", style_h2))
    env_data = [
        [Paragraph("Component", style_table_header), Paragraph("Specification / Version", style_table_header)],
        [Paragraph("Operating Environment", style_table_cell), Paragraph(report.metadata.test_environment, style_table_cell)],
        [Paragraph("Execution Engine", style_table_cell), Paragraph("Python Subprocess Isolated Workspace (5-second timeout)", style_table_cell)],
        [Paragraph("Static Analyzer", style_table_cell), Paragraph("Python 3 AST Module (Deterministic Signature Grounding)", style_table_cell)],
        [Paragraph("Test Architecture", style_table_cell), Paragraph("Two-Stage Grounded Test Pipeline with Automated Validation", style_table_cell)],
    ]
    t_env = Table(env_data, colWidths=[5.5 * cm, 10.0 * cm])
    t_env.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_th_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_env)
    story.append(Spacer(1, 10))

    # -----------------------------------------------------------------------
    # 4. TEST APPROACH & METHODOLOGY
    # -----------------------------------------------------------------------
    story.append(Paragraph("4. Test Approach & Methodology", style_h1))
    story.append(Paragraph(
        "<b>4.1 Two-Stage Grounded Pipeline:</b> Testing was executed through an automated two-stage architecture: "
        "(1) Static AST Analysis extracts method signatures, parameters, classes, and comparison condition limits without AI. "
        "(2) Grounded Generation produces balanced tests targeting normal, boundary, and invalid input domains. "
        "Crucially, expected results are derived from intended specifications and docstrings rather than running unverified code.",
        style_body
    ))
    story.append(Paragraph(
        "<b>4.2 Suspension and Resumption Criteria:</b> Execution suspends if catastrophic environment failure occurs or if "
        "an infinite loop breaches the 5.00-second subprocess timeout. Resumption occurs automatically on the subsequent test case.",
        style_body
    ))
    story.append(Spacer(1, 10))

    # -----------------------------------------------------------------------
    # 5. TEST CASE SUMMARY & CHARTS
    # -----------------------------------------------------------------------
    story.append(Paragraph("5. Test Case Summary & Metrics", style_h1))
    
    # Embedded Matplotlib Charts
    chart_cells = []
    if report.pie_chart_png:
        img_pie = Image(io.BytesIO(report.pie_chart_png), width=7.2 * cm, height=5.4 * cm)
        chart_cells.append(img_pie)
    else:
        chart_cells.append(Paragraph("Pass/Fail Chart Unavailable", style_body))

    if report.category_chart_png:
        img_bar = Image(io.BytesIO(report.category_chart_png), width=7.8 * cm, height=5.4 * cm)
        chart_cells.append(img_bar)
    else:
        chart_cells.append(Paragraph("Category Chart Unavailable", style_body))

    t_charts = Table([[chart_cells[0], chart_cells[1]]], colWidths=[7.7 * cm, 7.8 * cm])
    t_charts.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(t_charts)
    story.append(Spacer(1, 10))
    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # 6. DETAILED TEST RESULTS
    # -----------------------------------------------------------------------
    story.append(Paragraph("6. Detailed Test Execution Results", style_h1))
    story.append(Paragraph("Comprehensive tabular log of all dynamic test executions grouped by target module.", style_body))

    # Group results by file
    files_grouped = {}
    for r in report.results:
        f_name = r.file or "main.py"
        if f_name not in files_grouped:
            files_grouped[f_name] = []
        files_grouped[f_name].append(r)

    for f_name, f_results in files_grouped.items():
        story.append(Paragraph(f"<b>File: {f_name}</b>", style_h2))
        res_data = [
            [
                Paragraph("Test ID", style_table_header),
                Paragraph("Target", style_table_header),
                Paragraph("Cat.", style_table_header),
                Paragraph("Input Arguments", style_table_header),
                Paragraph("Expected", style_table_header),
                Paragraph("Actual Result", style_table_header),
                Paragraph("Status", style_table_header),
                Paragraph("Time", style_table_header),
            ]
        ]
        for idx, res in enumerate(f_results):
            tc_id = f"TC-{idx+1:03d}"
            st_color = "#15803d" if res.status == "PASS" else ("#b91c1c" if res.status == "FAIL" else "#b45309")
            
            # Format inputs and constructor if class method
            in_str = str(res.input)
            if res.class_name and res.constructor_args:
                in_str = f"init:{res.constructor_args} args:{res.input}"

            res_data.append([
                Paragraph(tc_id, style_table_code),
                Paragraph(f"{res.function_name}()", style_table_code),
                Paragraph(res.category[:4].upper(), style_table_cell),
                Paragraph(in_str[:45] + ("..." if len(in_str) > 45 else ""), style_table_code),
                Paragraph(str(res.expected)[:30], style_table_code),
                Paragraph(str(res.actual)[:30], style_table_code),
                Paragraph(f"<font color='{st_color}'><b>{res.status}</b></font>", style_table_cell),
                Paragraph(f"{res.execution_time_ms}ms", style_table_cell),
            ])

        t_res = Table(res_data, colWidths=[1.8 * cm, 2.5 * cm, 1.2 * cm, 3.8 * cm, 2.3 * cm, 2.3 * cm, 1.3 * cm, 1.3 * cm], repeatRows=1)
        t_res.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_th_bg),
            ("GRID", (0, 0), (-1, -1), 0.5, c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ]))
        story.append(t_res)
        story.append(Spacer(1, 10))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # 7. DEFECT REPORT
    # -----------------------------------------------------------------------
    story.append(Paragraph("7. Defect Report & Root Cause Analysis", style_h1))
    if not report.defects:
        story.append(Paragraph("<b>No defects identified.</b> All executed test assertions were successfully satisfied.", style_body))
    else:
        story.append(Paragraph(
            f"A total of {len(report.defects)} defect(s) were recorded during automated execution: "
            f"{report.high_severity_count} High severity, {report.medium_severity_count} Medium severity, "
            f"{report.low_severity_count} Low severity.",
            style_body
        ))
        story.append(Spacer(1, 6))

        for d in report.defects:
            d_block = []
            d_block.append(Paragraph(
                f"<b>{d['defect_id']}: {d['title']}</b> "
                f"[Severity: <font color='#b91c1c'><b>{d['severity']}</b></font> | Priority: {d['priority']} | Status: {d['status']}]",
                style_h2
            ))

            d_table_data = [
                [Paragraph("<b>Target File / Function:</b>", style_table_cell), Paragraph(f"{d['file']} &rarr; {d['function']}()", style_table_cell)],
                [Paragraph("<b>Reproduction Call:</b>", style_table_cell), Paragraph(d["steps"], style_table_code)],
                [Paragraph("<b>Expected Outcome:</b>", style_table_cell), Paragraph(d["expected"], style_table_cell)],
                [Paragraph("<b>Actual Received:</b>", style_table_cell), Paragraph(d["actual"], style_table_cell)],
                [Paragraph("<b>Technical Root Cause:</b>", style_table_cell), Paragraph(d["root_cause"], style_table_cell)],
            ]
            if d.get("recommended_fix"):
                d_table_data.append([
                    Paragraph("<b>Recommended Fix:</b>", style_table_cell),
                    Paragraph(d["recommended_fix"][:200], style_table_code)
                ])

            t_d = Table(d_table_data, colWidths=[4.2 * cm, 11.3 * cm])
            t_d.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 0.5, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            d_block.append(t_d)
            d_block.append(Spacer(1, 8))
            story.append(KeepTogether(d_block))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # 8. REQUIREMENTS / TRACEABILITY MATRIX
    # -----------------------------------------------------------------------
    story.append(Paragraph("8. Requirements / Traceability Matrix", style_h1))
    story.append(Paragraph(
        "Demonstrates bidirectional coverage across individual functions and testing categories "
        "(Normal, Boundary, and Invalid/Exception).",
        style_body
    ))

    tm_data = [
        [
            Paragraph("Function / Interface", style_table_header),
            Paragraph("File", style_table_header),
            Paragraph("Normal Cases", style_table_header),
            Paragraph("Boundary Limits", style_table_header),
            Paragraph("Invalid / Errors", style_table_header),
            Paragraph("Total", style_table_header),
            Paragraph("Status", style_table_header),
        ]
    ]
    for row in report.traceability_matrix:
        st_color = "#15803d" if row["status"] == "PASS" else "#b91c1c"
        tm_data.append([
            Paragraph(row["function"], style_table_code),
            Paragraph(row["file"], style_table_cell),
            Paragraph(row["normal"], style_table_cell),
            Paragraph(row["boundary"], style_table_cell),
            Paragraph(row["invalid"], style_table_cell),
            Paragraph(str(row["total"]), style_table_cell),
            Paragraph(f"<font color='{st_color}'><b>{row['status']}</b></font>", style_table_cell),
        ])
    t_tm = Table(tm_data, colWidths=[4.0 * cm, 3.0 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 1.2 * cm, 1.5 * cm], repeatRows=1)
    t_tm.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_th_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_tm)
    story.append(Spacer(1, 12))

    # -----------------------------------------------------------------------
    # 9. QUALITY METRICS & COVERAGE ANALYSIS
    # -----------------------------------------------------------------------
    story.append(Paragraph("9. Quality Metrics & Coverage Analysis", style_h1))
    qm_data = [
        [Paragraph("Metric Indicator", style_table_header), Paragraph("Observed Value", style_table_header), Paragraph("Interpretation", style_table_header)],
        [Paragraph("Function Interface Coverage", style_table_cell), Paragraph(f"{report.function_coverage_pct}%", style_table_cell), Paragraph(f"{len(report.tested_functions)} of {report.total_project_functions} functions exercised", style_table_cell)],
        [Paragraph("Estimated Branch Coverage", style_table_cell), Paragraph(f"{report.estimated_branch_coverage_pct}%", style_table_cell), Paragraph("Synthesized decision and condition paths", style_table_cell)],
        [Paragraph("Execution Pass Rate", style_table_cell), Paragraph(f"{report.pass_percent}%", style_table_cell), Paragraph(f"Benchmark threshold: {report.metadata.pass_threshold}%", style_table_cell)],
        [Paragraph("Defect Density", style_table_cell), Paragraph(f"{report.defect_density} def/fn", style_table_cell), Paragraph("Average defects identified per tested interface", style_table_cell)],
        [Paragraph("Mean Execution Latency", style_table_cell), Paragraph(f"{report.avg_execution_time_ms} ms", style_table_cell), Paragraph("Average per-test subprocess runtime", style_table_cell)],
    ]
    t_qm = Table(qm_data, colWidths=[5.5 * cm, 3.0 * cm, 7.0 * cm])
    t_qm.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_th_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_qm)
    story.append(Spacer(1, 12))

    # -----------------------------------------------------------------------
    # 10. REGRESSION COMPARISON
    # -----------------------------------------------------------------------
    story.append(Paragraph("10. Regression Comparison", style_h1))
    if not report.has_regression_data:
        story.append(Paragraph(
            "<b>Single Run Session:</b> This test report represents the initial quality baseline (Run 1). "
            "Comparative regression metrics, delta charts, and fixed defect verifications will automatically populate "
            "when a second test execution run is performed in this session.",
            style_body
        ))
    else:
        story.append(Paragraph("Comparative regression analysis against prior test execution baseline.", style_body))
        if report.regression_chart_png:
            img_reg = Image(io.BytesIO(report.regression_chart_png), width=10.0 * cm, height=5.0 * cm)
            story.append(img_reg)
            story.append(Spacer(1, 6))

        reg_data = [
            [Paragraph("Category", style_table_header), Paragraph("Count", style_table_header), Paragraph("Summary", style_table_header)],
            [Paragraph("Defects Fixed", style_table_cell), Paragraph(str(len(report.regression_details.get("fixed", []))), style_table_cell), Paragraph("Tests that previously failed and now pass.", style_table_cell)],
            [Paragraph("Regressions", style_table_cell), Paragraph(str(len(report.regression_details.get("regressions", []))), style_table_cell), Paragraph("Tests that previously passed and now fail.", style_table_cell)],
            [Paragraph("Unchanged", style_table_cell), Paragraph(str(len(report.regression_details.get("unchanged", []))), style_table_cell), Paragraph("Stable outcomes across executions.", style_table_cell)],
        ]
        t_reg = Table(reg_data, colWidths=[4.0 * cm, 2.5 * cm, 9.0 * cm])
        t_reg.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_th_bg),
            ("GRID", (0, 0), (-1, -1), 0.5, c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(t_reg)

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # 11. RISKS, LIMITATIONS AND ASSUMPTIONS
    # -----------------------------------------------------------------------
    story.append(Paragraph("11. Risks, Limitations and Assumptions", style_h1))
    story.append(Paragraph(report.risk_assessment_text, style_body))
    story.append(Paragraph(
        "<b>Technical Boundaries:</b><br/>"
        "• <b>Subprocess Timeout:</b> Tests are executed in local sub-processes with an isolated 5.00-second execution ceiling.<br/>"
        "• <b>Language Support:</b> Dynamic execution and AST parsing is currently scoped to Python source code.<br/>"
        "• <b>Human Review:</b> AI-generated unit test assertions reflect intended specifications and should undergo peer review.",
        style_body
    ))
    story.append(Spacer(1, 10))

    # -----------------------------------------------------------------------
    # 12. RECOMMENDATIONS AND CONCLUSION
    # -----------------------------------------------------------------------
    story.append(Paragraph("12. Recommendations and Conclusion", style_h1))
    story.append(Paragraph(report.recommendations_text, style_body))
    story.append(Paragraph(
        f"<b>Final Recommendation:</b> The target system is <b>{report.verdict}</b> for delivery. "
        f"{report.verdict_desc}",
        style_body
    ))
    story.append(Spacer(1, 12))

    # -----------------------------------------------------------------------
    # 13. FORMAL SIGN-OFF
    # -----------------------------------------------------------------------
    story.append(Paragraph("13. Formal Sign-off", style_h1))
    sign_data = [
        [Paragraph("Role", style_table_header), Paragraph("Name", style_table_header), Paragraph("Signature", style_table_header), Paragraph("Date", style_table_header)],
        [Paragraph("Test Engineer", style_table_cell), Paragraph(report.metadata.prepared_by, style_table_cell), Paragraph("___________________________", style_table_cell), Paragraph(report.metadata.test_date, style_table_cell)],
        [Paragraph("QA Lead", style_table_cell), Paragraph(report.metadata.reviewed_by, style_table_cell), Paragraph("___________________________", style_table_cell), Paragraph(report.metadata.test_date, style_table_cell)],
        [Paragraph("Project Manager", style_table_cell), Paragraph("Authorized Representative", style_table_cell), Paragraph("___________________________", style_table_cell), Paragraph(report.metadata.test_date, style_table_cell)],
    ]
    t_sign = Table(sign_data, colWidths=[3.5 * cm, 4.5 * cm, 4.5 * cm, 3.0 * cm])
    t_sign.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_th_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_sign)
    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # APPENDIX A & B
    # -----------------------------------------------------------------------
    story.append(Paragraph("Appendix A: Generated Test Definitions", style_h1))
    story.append(Paragraph(
        f"A total of {report.total_tests} unit test cases were synthesized. Full pytest-compatible "
        f"suite archives can be exported directly via the application workspace.",
        style_body
    ))
    for idx, r in enumerate(report.results[:12]):
        tc_code = f"# Test {idx+1}: {r.name}\ndef test_{r.function_name}_{idx+1}():\n    assert {r.function_name}(*{r.input}) == {repr(r.expected)}"
        story.append(Paragraph(tc_code.replace("\n", "<br/>").replace(" ", "&nbsp;"), style_code_block))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Appendix B: AI-Assisted Fix Proposals", style_h1))
    if not report.suggestions:
        story.append(Paragraph("No automated code fix proposals were generated.", style_body))
    else:
        for s in report.suggestions[:4]:
            fn_title = s.get("function_name") or s.get("file") or "Remediation"
            story.append(Paragraph(f"<b>Fix Proposal for {fn_title}:</b>", style_h2))
            if s.get("explanation"):
                story.append(Paragraph(s["explanation"], style_body))
            if s.get("suggested_fix"):
                story.append(Paragraph(s["suggested_fix"].replace("\n", "<br/>").replace(" ", "&nbsp;"), style_code_block))

    # Bind metadata attributes to canvas before building
    def make_canvas(*args, **kwargs):
        c = NumberedCanvas(*args, **kwargs)
        c.report_title = report.metadata.report_title
        c.doc_id = report.metadata.document_id
        return c

    doc.build(story, canvasmaker=make_canvas)
    buffer.seek(0)
    return buffer.getvalue()
