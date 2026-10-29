"""
Word (.docx) Report Renderer (python-docx).
Generates an IEEE 829 / ISO 29119 compliant formal Software Test Report.
Uses A4 sizing, 2.5cm margins, running headers/footers, real Word heading styles,
repeatable table headers across page breaks, and embedded Matplotlib charts.
"""
import io
from typing import List, Dict, Any, Optional
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
from services.report_builder import StructuredTestReport


def set_cell_background(cell, hex_color: str):
    """Sets cell background fill color using openxml shading."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets internal cell padding in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def set_table_header_and_cant_split(table):
    """Marks row 0 as repeating header across pages and prevents rows from splitting across page breaks."""
    for i, row in enumerate(table.rows):
        trPr = row._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        if i == 0:
            trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))


def add_word_toc(paragraph):
    """Inserts a real Microsoft Word dynamic Table of Contents field."""
    run = paragraph.add_run()
    fldChar1 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>')
    instrText = parse_xml(f'<w:instrText {nsdecls("w")} xml:space="preserve"> TOC \\o "1-3" \\h \\z \\u </w:instrText>')
    fldChar2 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="separate"/>')
    fldChar3 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>')
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)


def render_docx_report(report: StructuredTestReport) -> bytes:
    """Renders structured report object to binary Word (.docx) stream."""
    doc = docx.Document()

    # 1. Page Setup: A4 with 2.5 cm margins (0.984 inches)
    section = doc.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = Inches(0.984)
    section.bottom_margin = Inches(0.984)
    section.left_margin = Inches(0.984)
    section.right_margin = Inches(0.984)

    # Different first page for cover
    section.different_first_page_header_footer = True

    # Running header on subsequent pages
    header = section.header
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hrun1 = hp.add_run(f"{report.metadata.report_title}    |    {report.metadata.document_id}")
    hrun1.font.name = "Calibri"
    hrun1.font.size = Pt(8)
    hrun1.font.color.rgb = RGBColor(100, 116, 139)

    # Running footer on subsequent pages
    footer = section.footer
    fp = footer.paragraphs[0]
    frun1 = fp.add_run("CONFIDENTIAL — FOR INTERNAL USE ONLY")
    frun1.font.name = "Calibri"
    frun1.font.size = Pt(8)
    frun1.font.color.rgb = RGBColor(100, 116, 139)

    # Palette
    color_primary = RGBColor(30, 58, 138)     # Deep blue (#1e3a8a)
    color_text = RGBColor(30, 41, 59)         # Slate-900 (#1e293b)
    color_muted = RGBColor(100, 116, 139)     # Slate-500 (#64748b)

    # -----------------------------------------------------------------------
    # COVER PAGE
    # -----------------------------------------------------------------------
    p_pre = doc.add_paragraph()
    p_pre.paragraph_format.space_before = Pt(80)

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_after = Pt(4)
    run_title = p_title.add_run(report.metadata.report_title)
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(24)
    run_title.font.bold = True
    run_title.font.color.rgb = color_primary

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(24)
    run_sub = p_sub.add_run(f"Project: {report.metadata.project_name}")
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(13)
    run_sub.font.color.rgb = color_muted

    # Meta Table on Cover
    cover_table = doc.add_table(rows=8, cols=2)
    cover_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cover_table.autofit = False

    meta_items = [
        ("Document Identifier:", report.metadata.document_id),
        ("Standard / Specification:", "IEEE 829-2008 / ISO/IEC/IEEE 29119-3"),
        ("Version / Release:", report.metadata.version),
        ("Execution Date:", report.metadata.test_date),
        ("Prepared By:", report.metadata.prepared_by),
        ("Reviewed By:", report.metadata.reviewed_by),
        ("Organization / Dept:", report.metadata.organization),
        ("Engineering Verdict:", f"{report.verdict} — {report.verdict_desc}"),
    ]

    for idx, (label, val) in enumerate(meta_items):
        row = cover_table.rows[idx]
        row.cells[0].width = Inches(2.2)
        row.cells[1].width = Inches(4.1)

        set_cell_margins(row.cells[0], top=60, bottom=60, left=80, right=80)
        set_cell_margins(row.cells[1], top=60, bottom=60, left=80, right=80)

        p0 = row.cells[0].paragraphs[0]
        r0 = p0.add_run(label)
        r0.font.name = "Calibri"
        r0.font.bold = True
        r0.font.size = Pt(10)
        r0.font.color.rgb = color_text

        p1 = row.cells[1].paragraphs[0]
        r1 = p1.add_run(val)
        r1.font.name = "Calibri"
        r1.font.size = Pt(10)
        if "ACCEPTED" in val:
            r1.font.bold = True
            r1.font.color.rgb = RGBColor(21, 128, 61) if "CONDITIONALLY" not in val else RGBColor(180, 83, 9)
        elif "REJECTED" in val:
            r1.font.bold = True
            r1.font.color.rgb = RGBColor(185, 28, 28)
        else:
            r1.font.color.rgb = color_text

    p_notice = doc.add_paragraph()
    p_notice.paragraph_format.space_before = Pt(120)
    r_not = p_notice.add_run("CONFIDENTIALITY NOTICE: The information contained in this document is intended solely for authorized personnel. Unauthorized distribution is strictly prohibited.")
    r_not.font.name = "Calibri"
    r_not.font.size = Pt(9)
    r_not.font.italic = True
    r_not.font.color.rgb = color_muted

    doc.add_page_break()

    # -----------------------------------------------------------------------
    # DOCUMENT CONTROL & TOC
    # -----------------------------------------------------------------------
    h_doc = doc.add_heading("Document Control", level=1)
    h_doc.style.font.color.rgb = color_primary

    p_rev_h = doc.add_paragraph()
    p_rev_h.add_run("Revision History").font.bold = True

    t_rev = doc.add_table(rows=2, cols=4)
    t_rev.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_header_and_cant_split(t_rev)

    rev_headers = ["Version", "Date", "Author", "Summary of Changes"]
    for c_idx, h_text in enumerate(rev_headers):
        cell = t_rev.cell(0, c_idx)
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        r = p.add_run(h_text)
        r.font.name = "Calibri"
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        r.font.size = Pt(9)

    rev_row_vals = ["1.0", report.metadata.test_date, report.metadata.prepared_by, "Initial baseline automated software test report."]
    for c_idx, val in enumerate(rev_row_vals):
        cell = t_rev.cell(1, c_idx)
        set_cell_margins(cell, top=60, bottom=60, left=100, right=100)
        p = cell.paragraphs[0]
        r = p.add_run(val)
        r.font.name = "Calibri"
        r.font.size = Pt(9)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Dynamic TOC
    h_toc = doc.add_heading("Table of Contents", level=1)
    h_toc.style.font.color.rgb = color_primary
    p_toc = doc.add_paragraph()
    add_word_toc(p_toc)
    p_toc_note = doc.add_paragraph()
    r_tn = p_toc_note.add_run("[Right-click and select 'Update Field' in Microsoft Word to refresh page numbers]")
    r_tn.font.size = Pt(8)
    r_tn.font.italic = True
    r_tn.font.color.rgb = color_muted

    doc.add_page_break()

    # -----------------------------------------------------------------------
    # 1. INTRODUCTION
    # -----------------------------------------------------------------------
    doc.add_heading("1. Introduction", level=1)

    doc.add_heading("1.1 Purpose of this document", level=2)
    p = doc.add_paragraph(
        "This document provides a formal Test Summary Report (TSR) in compliance with IEEE 829-2008 and "
        "ISO/IEC/IEEE 29119-3 standards. It consolidates the empirical execution outcomes, defect classifications, "
        "and quality assurance metrics resulting from automated dynamic testing conducted on the target software system."
    )
    p.style.font.name = "Calibri"
    p.style.font.size = Pt(11)

    doc.add_heading("1.2 Scope of Testing", level=2)
    files_str = ", ".join([f.path for f in report.files]) if report.files else "Integrated source modules"
    p = doc.add_paragraph(
        f"The testing scope encompassed {len(report.files)} source file(s) ({files_str}) and {len(report.tested_functions)} "
        f"public function/method interfaces. Testing evaluated typical business logic flows, edge limit boundaries, "
        f"and exception-raising error scenarios."
    )
    p.style.font.name = "Calibri"
    p.style.font.size = Pt(11)

    doc.add_heading("1.3 Definitions and Abbreviations", level=2)
    t_def = doc.add_table(rows=6, cols=2)
    t_def.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_header_and_cant_split(t_def)

    def_data = [
        ("Term", "Formal Definition"),
        ("PASS", "Execution completed with output matching expected specification within 5s timeout."),
        ("FAIL", "Execution completed but actual return value differed from the required expectation."),
        ("ERROR", "Execution terminated with an unhandled exception or timed out."),
        ("Boundary Test", "Verification of limits (zero, minimum, off-by-one, empty collections) derived from AST comparison conditions."),
        ("AST", "Abstract Syntax Tree — Python standard library static structural representation of code.")
    ]
    for r_idx, (term, d_text) in enumerate(def_data):
        row = t_def.rows[r_idx]
        for c_idx, val in enumerate((term, d_text)):
            cell = row.cells[c_idx]
            if r_idx == 0:
                set_cell_background(cell, "1E293B")
            set_cell_margins(cell, top=50, bottom=50, left=80, right=80)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9)
            if r_idx == 0:
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)

    doc.add_heading("1.4 Applicable Standards and References", level=2)
    doc.add_paragraph("• IEEE Std 829-2008: Standard for Software Test Documentation.\n• ISO/IEC/IEEE 29119-3:2013: Software testing — Part 3: Test documentation.\n• PEP 8 / PEP 484: Python Style and Type Hinting Specifications.")

    doc.add_page_break()

    # -----------------------------------------------------------------------
    # 2. EXECUTIVE SUMMARY
    # -----------------------------------------------------------------------
    doc.add_heading("2. Executive Summary", level=1)
    doc.add_paragraph(report.executive_summary_text)

    # Key Metrics Table
    t_em = doc.add_table(rows=7, cols=3)
    t_em.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_header_and_cant_split(t_em)

    em_rows = [
        ("Metric", "Value", "Quality Criterion"),
        ("Total Executed Tests", str(report.total_tests), "All generated test cases"),
        ("Passed Test Cases", f"{report.passed_tests} ({report.pass_percent}%)", "Satisfied all assertions"),
        ("Failed Test Cases", str(report.failed_tests), "Functional logic divergence"),
        ("Execution Errors / Crashes", str(report.error_tests), "Unhandled exceptions / timeouts"),
        ("Acceptance Pass Threshold", f"{report.metadata.pass_threshold}%", "Target compliance benchmark"),
        ("Overall Engineering Verdict", report.verdict, report.verdict_desc),
    ]

    for r_idx, (m_lbl, m_val, m_crit) in enumerate(em_rows):
        row = t_em.rows[r_idx]
        for c_idx, txt in enumerate((m_lbl, m_val, m_crit)):
            cell = row.cells[c_idx]
            if r_idx == 0:
                set_cell_background(cell, "1E293B")
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            p = cell.paragraphs[0]
            r = p.add_run(txt)
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            if r_idx == 0:
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)
            elif c_idx == 1 and "ACCEPTED" in txt:
                r.font.bold = True
                r.font.color.rgb = RGBColor(21, 128, 61)
            elif c_idx == 1 and "REJECTED" in txt:
                r.font.bold = True
                r.font.color.rgb = RGBColor(185, 28, 28)

    doc.add_page_break()

    # -----------------------------------------------------------------------
    # 3. TEST ITEMS AND ENVIRONMENT
    # -----------------------------------------------------------------------
    doc.add_heading("3. Test Items and Environment", level=1)
    doc.add_heading("3.1 Tested Module Interfaces", level=2)

    t_ti = doc.add_table(rows=len(report.tested_functions) + 1, cols=5)
    t_ti.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_header_and_cant_split(t_ti)

    ti_headers = ["Module / File", "Target Function", "Branches", "Tests Executed", "Status"]
    for c_idx, h_text in enumerate(ti_headers):
        cell = t_ti.cell(0, c_idx)
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
        p = cell.paragraphs[0]
        r = p.add_run(h_text)
        r.font.name = "Calibri"
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        r.font.size = Pt(9)

    for idx, fn in enumerate(report.tested_functions):
        row = t_ti.rows[idx + 1]
        st_text = "PASS" if fn["failed_count"] == 0 else f"{fn['failed_count']} FAIL"
        row_vals = [fn["file"], fn["display_name"], str(fn["branches"]), str(fn["tests_count"]), st_text]
        for c_idx, val in enumerate(row_vals):
            cell = row.cells[c_idx]
            set_cell_margins(cell, top=40, bottom=40, left=80, right=80)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Consolas" if c_idx < 2 else "Calibri"
            r.font.size = Pt(8.5)
            if c_idx == 4:
                r.font.bold = True
                r.font.color.rgb = RGBColor(21, 128, 61) if "PASS" in val else RGBColor(185, 28, 28)

    doc.add_heading("3.2 Test Execution Environment", level=2)
    doc.add_paragraph(
        f"• Host Environment: {report.metadata.test_environment}\n"
        "• Execution Engine: Subprocess Isolated Workspace (5-second timeout per test)\n"
        "• Static Analyzer: Python AST Module (Deterministic Signature Grounding)\n"
        "• Test Generation: Two-Stage Pipeline (Static Analysis + Grounded Synthesis)"
    )

    # -----------------------------------------------------------------------
    # 4. TEST APPROACH & METHODOLOGY
    # -----------------------------------------------------------------------
    doc.add_heading("4. Test Approach & Methodology", level=1)
    doc.add_paragraph(
        "4.1 Two-Stage Grounded Pipeline:\n"
        "Testing was executed using an automated two-stage architecture: (1) Static AST Analysis extracts method signatures, "
        "parameter types, and comparison condition limits without AI. (2) Grounded Generation creates balanced test cases targeting "
        "normal, boundary, and invalid input domains. Expected values are derived strictly from intended logic and docstrings, "
        "never by running unverified code.\n\n"
        "4.2 Suspension and Resumption Criteria:\n"
        "Execution suspends if an environment fault occurs or if a test breaches the 5.00-second timeout (infinite loop prevention). "
        "Resumption occurs automatically on the subsequent test case."
    )

    doc.add_page_break()

    # -----------------------------------------------------------------------
    # 5. TEST CASE SUMMARY & CHARTS
    # -----------------------------------------------------------------------
    doc.add_heading("5. Test Case Summary & Metrics", level=1)
    doc.add_paragraph("Visual distribution of test outcomes and category breakdown:")

    # Embed in-memory Matplotlib charts into document
    if report.pie_chart_png or report.category_chart_png:
        t_ch = doc.add_table(rows=1, cols=2)
        t_ch.alignment = WD_TABLE_ALIGNMENT.CENTER
        if report.pie_chart_png:
            p_pie = t_ch.cell(0, 0).paragraphs[0]
            p_pie.add_run().add_picture(io.BytesIO(report.pie_chart_png), width=Inches(3.0))
        if report.category_chart_png:
            p_bar = t_ch.cell(0, 1).paragraphs[0]
            p_bar.add_run().add_picture(io.BytesIO(report.category_chart_png), width=Inches(3.2))

    doc.add_page_break()

    # -----------------------------------------------------------------------
    # 6. DETAILED TEST RESULTS
    # -----------------------------------------------------------------------
    doc.add_heading("6. Detailed Test Execution Results", level=1)
    
    files_grouped = {}
    for r in report.results:
        f_name = r.file or "main.py"
        if f_name not in files_grouped:
            files_grouped[f_name] = []
        files_grouped[f_name].append(r)

    for f_name, f_results in files_grouped.items():
        doc.add_heading(f"Module File: {f_name}", level=2)
        t_res = doc.add_table(rows=len(f_results) + 1, cols=8)
        t_res.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_header_and_cant_split(t_res)

        res_hdrs = ["Test ID", "Target", "Cat.", "Input Arguments", "Expected", "Actual Result", "Status", "Time"]
        for c_idx, h_text in enumerate(res_hdrs):
            cell = t_res.cell(0, c_idx)
            set_cell_background(cell, "1E293B")
            set_cell_margins(cell, top=50, bottom=50, left=60, right=60)
            p = cell.paragraphs[0]
            r = p.add_run(h_text)
            r.font.name = "Calibri"
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.size = Pt(8.5)

        for idx, res in enumerate(f_results):
            row = t_res.rows[idx + 1]
            in_str = str(res.input)
            if res.class_name and res.constructor_args:
                in_str = f"init:{res.constructor_args} args:{res.input}"

            row_vals = [
                f"TC-{idx+1:03d}",
                f"{res.function_name}()",
                res.category[:4].upper(),
                in_str[:40] + ("..." if len(in_str) > 40 else ""),
                str(res.expected)[:25],
                str(res.actual)[:25],
                res.status,
                f"{res.execution_time_ms}ms"
            ]
            for c_idx, val in enumerate(row_vals):
                cell = row.cells[c_idx]
                set_cell_margins(cell, top=40, bottom=40, left=60, right=60)
                p = cell.paragraphs[0]
                r = p.add_run(val)
                r.font.name = "Consolas" if c_idx in (0, 1, 3, 4, 5) else "Calibri"
                r.font.size = Pt(8)
                if c_idx == 6:
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(21, 128, 61) if val == "PASS" else RGBColor(185, 28, 28)

    doc.add_page_break()

    # -----------------------------------------------------------------------
    # 7. DEFECT REPORT
    # -----------------------------------------------------------------------
    doc.add_heading("7. Defect Report & Root Cause Analysis", level=1)
    if not report.defects:
        doc.add_paragraph("No defects identified. All executed test assertions were successfully satisfied.")
    else:
        doc.add_paragraph(
            f"A total of {len(report.defects)} defect(s) were recorded: "
            f"{report.high_severity_count} High severity, {report.medium_severity_count} Medium severity, "
            f"{report.low_severity_count} Low severity."
        )

        for d in report.defects:
            h_def = doc.add_heading(f"{d['defect_id']}: {d['title']}", level=2)
            h_def.style.font.color.rgb = RGBColor(185, 28, 28) if d["severity"] == "High" else RGBColor(180, 83, 9)

            t_d = doc.add_table(rows=5, cols=2)
            t_d.alignment = WD_TABLE_ALIGNMENT.CENTER
            set_table_header_and_cant_split(t_d)

            d_items = [
                ("Severity / Priority:", f"{d['severity']} ({d['priority']}) | Status: {d['status']}"),
                ("Target Function:", f"{d['file']} -> {d['function']}()"),
                ("Reproduction Call:", d["steps"]),
                ("Expected vs Actual:", f"Expected: {d['expected']}  |  Actual: {d['actual']}"),
                ("Root Cause Analysis:", d["root_cause"]),
            ]
            for r_idx, (lbl, val) in enumerate(d_items):
                row = t_d.rows[r_idx]
                row.cells[0].width = Inches(1.8)
                row.cells[1].width = Inches(4.5)
                set_cell_background(row.cells[0], "F8FAFC")
                set_cell_margins(row.cells[0], top=40, bottom=40, left=80, right=80)
                set_cell_margins(row.cells[1], top=40, bottom=40, left=80, right=80)

                p0 = row.cells[0].paragraphs[0]
                r0 = p0.add_run(lbl)
                r0.font.bold = True
                r0.font.size = Pt(8.5)

                p1 = row.cells[1].paragraphs[0]
                r1 = p1.add_run(val)
                r1.font.name = "Consolas" if r_idx == 2 else "Calibri"
                r1.font.size = Pt(8.5)

            if d.get("recommended_fix"):
                p_fix_lbl = doc.add_paragraph()
                p_fix_lbl.paragraph_format.space_before = Pt(4)
                p_fix_lbl.add_run("Recommended Code Remediation:").font.bold = True
                p_code = doc.add_paragraph()
                p_code.paragraph_format.left_indent = Inches(0.2)
                r_c = p_code.add_run(d["recommended_fix"][:250])
                r_c.font.name = "Consolas"
                r_c.font.size = Pt(8)

    doc.add_page_break()

    # -----------------------------------------------------------------------
    # 8. REQUIREMENTS / TRACEABILITY MATRIX
    # -----------------------------------------------------------------------
    doc.add_heading("8. Requirements / Traceability Matrix", level=1)
    doc.add_paragraph("Demonstrates test category coverage across individual function interfaces:")

    t_tm = doc.add_table(rows=len(report.traceability_matrix) + 1, cols=7)
    t_tm.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_header_and_cant_split(t_tm)

    tm_hdrs = ["Function / Interface", "File", "Normal Cases", "Boundary Limits", "Invalid Inputs", "Total", "Status"]
    for c_idx, h_text in enumerate(tm_hdrs):
        cell = t_tm.cell(0, c_idx)
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, top=50, bottom=50, left=70, right=70)
        p = cell.paragraphs[0]
        r = p.add_run(h_text)
        r.font.name = "Calibri"
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        r.font.size = Pt(8.5)

    for idx, row_data in enumerate(report.traceability_matrix):
        row = t_tm.rows[idx + 1]
        vals = [row_data["function"], row_data["file"], row_data["normal"], row_data["boundary"], row_data["invalid"], str(row_data["total"]), row_data["status"]]
        for c_idx, val in enumerate(vals):
            cell = row.cells[c_idx]
            set_cell_margins(cell, top=40, bottom=40, left=70, right=70)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Consolas" if c_idx == 0 else "Calibri"
            r.font.size = Pt(8.5)
            if c_idx == 6:
                r.font.bold = True
                r.font.color.rgb = RGBColor(21, 128, 61) if val == "PASS" else RGBColor(185, 28, 28)

    doc.add_page_break()

    # -----------------------------------------------------------------------
    # 9. QUALITY METRICS & COVERAGE ANALYSIS
    # -----------------------------------------------------------------------
    doc.add_heading("9. Quality Metrics & Coverage Analysis", level=1)
    t_qm = doc.add_table(rows=6, cols=3)
    t_qm.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_header_and_cant_split(t_qm)

    qm_rows = [
        ("Metric Indicator", "Observed Value", "Interpretation"),
        ("Function Interface Coverage", f"{report.function_coverage_pct}%", f"{len(report.tested_functions)} of {report.total_project_functions} functions exercised"),
        ("Estimated Branch Coverage", f"{report.estimated_branch_coverage_pct}%", "Synthesized conditional decision paths"),
        ("Execution Pass Rate", f"{report.pass_percent}%", f"Benchmark threshold: {report.metadata.pass_threshold}%"),
        ("Defect Density", f"{report.defect_density} def/fn", "Average defects per tested function"),
        ("Mean Execution Latency", f"{report.avg_execution_time_ms} ms", "Average per-test subprocess runtime"),
    ]
    for r_idx, (m_lbl, m_val, m_crit) in enumerate(qm_rows):
        row = t_qm.rows[r_idx]
        for c_idx, txt in enumerate((m_lbl, m_val, m_crit)):
            cell = row.cells[c_idx]
            if r_idx == 0:
                set_cell_background(cell, "1E293B")
            set_cell_margins(cell, top=50, bottom=50, left=80, right=80)
            p = cell.paragraphs[0]
            r = p.add_run(txt)
            r.font.name = "Calibri"
            r.font.size = Pt(9)
            if r_idx == 0:
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)

    # -----------------------------------------------------------------------
    # 10. REGRESSION COMPARISON
    # -----------------------------------------------------------------------
    doc.add_heading("10. Regression Comparison", level=1)
    if not report.has_regression_data:
        doc.add_paragraph(
            "Single Run Session: This test report represents the initial quality baseline (Run 1). "
            "Comparative regression metrics, delta charts, and fixed defect verifications will automatically populate "
            "when a second test execution run is performed in this session."
        )
    else:
        doc.add_paragraph("Comparative regression metrics against prior test execution baseline:")
        if report.regression_chart_png:
            p_reg = doc.add_paragraph()
            p_reg.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_reg.add_run().add_picture(io.BytesIO(report.regression_chart_png), width=Inches(4.5))

    doc.add_page_break()

    # -----------------------------------------------------------------------
    # 11. RISKS, LIMITATIONS AND ASSUMPTIONS
    # -----------------------------------------------------------------------
    doc.add_heading("11. Risks, Limitations and Assumptions", level=1)
    doc.add_paragraph(report.risk_assessment_text)
    doc.add_paragraph(
        "Technical Boundaries & Constraints:\n"
        "• Subprocess Execution Timeout: Test cases run with an isolated 5.00-second execution limit.\n"
        "• Static AST Scope: Dynamic testing and AST introspection are currently scoped to Python source files.\n"
        "• Human Review: AI-generated expectations represent intended specifications and should undergo peer review."
    )

    # -----------------------------------------------------------------------
    # 12. RECOMMENDATIONS AND CONCLUSION
    # -----------------------------------------------------------------------
    doc.add_heading("12. Recommendations and Conclusion", level=1)
    doc.add_paragraph(report.recommendations_text)
    doc.add_paragraph(f"Final Recommendation: The target system is {report.verdict} for delivery. {report.verdict_desc}")

    # -----------------------------------------------------------------------
    # 13. FORMAL SIGN-OFF
    # -----------------------------------------------------------------------
    doc.add_heading("13. Formal Sign-off", level=1)
    t_sign = doc.add_table(rows=4, cols=4)
    t_sign.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_header_and_cant_split(t_sign)

    sign_hdrs = ["Role", "Name", "Signature", "Date"]
    for c_idx, h_text in enumerate(sign_hdrs):
        cell = t_sign.cell(0, c_idx)
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
        p = cell.paragraphs[0]
        r = p.add_run(h_text)
        r.font.name = "Calibri"
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        r.font.size = Pt(9)

    sign_rows = [
        ("Test Engineer", report.metadata.prepared_by, "_______________________", report.metadata.test_date),
        ("QA Lead", report.metadata.reviewed_by, "_______________________", report.metadata.test_date),
        ("Project Manager", "Authorized Representative", "_______________________", report.metadata.test_date),
    ]
    for r_idx, (role, name, sig, dt) in enumerate(sign_rows):
        row = t_sign.rows[r_idx + 1]
        for c_idx, val in enumerate((role, name, sig, dt)):
            cell = row.cells[c_idx]
            set_cell_margins(cell, top=50, bottom=50, left=80, right=80)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9)

    doc.add_page_break()

    # -----------------------------------------------------------------------
    # APPENDIX A & B
    # -----------------------------------------------------------------------
    doc.add_heading("Appendix A: Generated Test Definitions", level=1)
    doc.add_paragraph(f"Sample test definitions from the {report.total_tests} synthesized test cases:")
    for idx, r in enumerate(report.results[:10]):
        p_c = doc.add_paragraph()
        p_c.paragraph_format.left_indent = Inches(0.2)
        p_c.paragraph_format.space_after = Pt(4)
        tc_code = f"# Test {idx+1}: {r.name}\ndef test_{r.function_name}_{idx+1}():\n    assert {r.function_name}(*{r.input}) == {repr(r.expected)}"
        rc = p_c.add_run(tc_code)
        rc.font.name = "Consolas"
        rc.font.size = Pt(8)

    doc.add_heading("Appendix B: AI-Assisted Fix Proposals", level=1)
    if not report.suggestions:
        doc.add_paragraph("No automated code fix proposals were generated.")
    else:
        for s in report.suggestions[:4]:
            doc.add_heading(f"Remediation Proposal: {s.get('function_name', 'Module')}", level=2)
            if s.get("explanation"):
                doc.add_paragraph(s["explanation"])
            if s.get("suggested_fix"):
                p_fx = doc.add_paragraph()
                p_fx.paragraph_format.left_indent = Inches(0.2)
                rc = p_fx.add_run(s["suggested_fix"][:300])
                rc.font.name = "Consolas"
                rc.font.size = Pt(8)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()
