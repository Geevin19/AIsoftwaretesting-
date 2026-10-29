"""
Reports Router:
Generates exportable test execution artifacts, including formal IEEE 829 / ISO 29119
PDF and Word (.docx) test summary reports, CSV logs, and pytest export zip archives.
"""
import io
import csv
import json
import zipfile
import logging
from typing import List
from fastapi import APIRouter, Response, HTTPException, status
from schemas import (
    TestResultItem,
    ExportPytestRequest,
    ReportMetadata,
    ReportNarrative,
    ReportNarrativeRequest,
    ReportGenerateRequest,
)
from services.report_builder import build_structured_report
from services.report_pdf import render_pdf_report
from services.report_docx import render_docx_report
from services.llm_client import llm_client
from services.prompts import REPORT_NARRATIVE_SYSTEM_PROMPT, build_report_narrative_prompt

logger = logging.getLogger("reports_router")
router = APIRouter(prefix="/api", tags=["Reports"])


@router.post("/report/narrative", response_model=ReportNarrative, summary="Synthesize AI prose narrative for formal test report")
def generate_report_narrative_endpoint(payload: ReportNarrativeRequest):
    """
    Synthesizes executive summary, risk assessment, recommendations, and defect root causes
    using a single call to the LLM. If Gemini is unavailable, falls back deterministically
    to formal templates derived from computed metrics.
    """
    threshold = payload.metadata.pass_threshold or 90.0
    pass_pct = payload.metrics.pass_percent

    if pass_pct >= threshold and payload.high_severity_count == 0:
        verdict = "ACCEPTED"
    elif pass_pct >= max(0.0, threshold - 15.0) and payload.high_severity_count <= 1:
        verdict = "CONDITIONALLY ACCEPTED"
    else:
        verdict = "REJECTED"

    # Attempt Gemini LLM narrative synthesis
    if llm_client.is_configured():
        prompt = build_report_narrative_prompt(
            metadata=payload.metadata.model_dump(),
            metrics=payload.metrics.model_dump(),
            verdict=verdict,
            failed_defects=payload.failed_tests_summary
        )
        try:
            raw_text = llm_client.generate_text(
                prompt=prompt,
                system_instruction=REPORT_NARRATIVE_SYSTEM_PROMPT
            )
            # Clean JSON fences if present
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                import re
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                cleaned = re.sub(r"\s*```$", "", cleaned)
            parsed = json.loads(cleaned)
            return ReportNarrative(
                executive_summary=parsed.get("executive_summary", ""),
                risk_assessment=parsed.get("risk_assessment", ""),
                recommendations=parsed.get("recommendations", ""),
                defects_analysis=parsed.get("defects_analysis", {})
            )
        except Exception as exc:
            logger.warning(f"AI narrative generation failed ({exc}). Using deterministic engineering template.")

    # Deterministic fallback template
    exec_summary = (
        f"Automated software quality verification was conducted on {payload.metadata.test_date} for "
        f"{payload.metadata.project_name}. A total of {payload.metrics.total} test cases were executed across "
        f"{payload.files_count or 1} module(s) and {payload.functions_count or 1} function interface(s). "
        f"{payload.metrics.passed} test cases passed and {payload.metrics.failed + payload.metrics.error} failed, "
        f"yielding an overall pass rate of {payload.metrics.pass_percent}%. Based on the established quality acceptance "
        f"threshold of {payload.metadata.pass_threshold}%, the formal engineering verdict is {verdict}."
    )

    if payload.high_severity_count > 0:
        risk_text = (
            f"Testing identified {payload.high_severity_count} high-severity defect(s) and "
            f"{max(0, len(payload.failed_tests_summary) - payload.high_severity_count)} boundary limit discrepancy(ies). "
            f"Deploying this build without remediation presents operational risk regarding data integrity and unexpected exceptions in production."
        )
    else:
        risk_text = (
            "No critical defects were identified across tested core components. Residual risk is low, "
            "limited to unexercised asynchronous behaviors and operating system specific filesystem variations."
        )

    if payload.failed_tests_summary:
        recs_text = (
            f"1. Remediate the {len(payload.failed_tests_summary)} identified defect(s) in priority order (P1 critical items first).\n"
            "2. Incorporate explicit boundary guards for comparison operators and None value checks.\n"
            "3. Re-execute the automated test suite to ensure no regression defects are introduced prior to final release."
        )
    else:
        recs_text = (
            "1. Maintain current test suite in the continuous integration pipeline.\n"
            "2. Extend boundary tests to cover edge cases for newly planned modules."
        )

    defect_causes = {}
    for idx, d in enumerate(payload.failed_tests_summary):
        d_id = d.get("defect_id", f"DEF-{idx+1:03d}")
        defect_causes[d_id] = (
            f"Expected outcome '{d.get('expected')}' was not satisfied; received '{d.get('actual')}'. "
            f"Input {d.get('input')} exposed an unhandled logic condition in {d.get('function', 'module')}."
        )

    return ReportNarrative(
        executive_summary=exec_summary,
        risk_assessment=risk_text,
        recommendations=recs_text,
        defects_analysis=defect_causes
    )


@router.post("/report/pdf", summary="Generate downloadable IEEE 829 PDF test report")
def export_pdf_report(payload: ReportGenerateRequest):
    """
    Builds the formal structured report and renders a publication-grade PDF
    with running headers/footers, embedded charts, and IEEE 829 / ISO 29119 sections.
    """
    if not payload.results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot generate report from an empty test result list. Please execute tests first."
        )

    try:
        structured_report = build_structured_report(payload)
        pdf_bytes = render_pdf_report(structured_report)

        filename = f"{payload.metadata.project_name.replace(' ', '_')}_Test_Report.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as exc:
        logger.error(f"PDF generation failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF report generation failed: {str(exc)}"
        )


@router.post("/report/docx", summary="Generate downloadable IEEE 829 Word (.docx) test report")
def export_docx_report(payload: ReportGenerateRequest):
    """
    Builds the formal structured report and renders a Microsoft Word (.docx) document
    with real heading styles, dynamic TOC field, embedded charts, and IEEE 829 sections.
    """
    if not payload.results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot generate report from an empty test result list. Please execute tests first."
        )

    try:
        structured_report = build_structured_report(payload)
        docx_bytes = render_docx_report(structured_report)

        filename = f"{payload.metadata.project_name.replace(' ', '_')}_Test_Report.docx"
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as exc:
        logger.error(f"Word (.docx) generation failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Word (.docx) report generation failed: {str(exc)}"
        )


@router.post("/report/csv", summary="Export test results to a CSV file")
def export_csv_report(results: List[TestResultItem]):
    """
    Accepts executed test results and outputs a formatted CSV stream
    ready for browser download, including File and Module tracking.
    """
    if not results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot generate report from an empty test result list."
        )

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    writer.writerow([
        "File",
        "Module",
        "Test ID",
        "Test Name",
        "Category",
        "Function",
        "Inputs",
        "Expected",
        "Actual",
        "Status",
        "Execution Time (ms)",
        "Purpose",
        "Error Message"
    ])

    for item in results:
        writer.writerow([
            item.file,
            item.module,
            item.id,
            item.name,
            item.category,
            item.function_name,
            str(item.input),
            str(item.expected),
            str(item.actual),
            item.status,
            item.execution_time_ms,
            item.purpose or "",
            item.error_message or ""
        ])

    csv_data = output.getvalue()
    output.close()

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="ai_test_execution_report.csv"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


@router.post("/export/pytest", summary="Export full project with generated pytest suite as a zip archive")
def export_pytest_suite(payload: ExportPytestRequest):
    """
    Generates a ready-to-run pytest project packaged as a downloadable .zip archive.
    """
    if not payload.files:
        raise HTTPException(status_code=400, detail="No project files provided for export.")

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for sfile in payload.files:
            clean_path = sfile.path.replace("\\", "/").strip().lstrip("/")
            zf.writestr(clean_path, sfile.content)

        conftest_content = """# Pytest Configuration
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
"""
        zf.writestr("conftest.py", conftest_content)

        test_code_lines = [
            "# Auto-Generated Pytest Test Suite",
            "import pytest",
            "import sys",
            "import os",
            "sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))",
            "",
        ]

        imported_modules = set()
        for t in payload.tests:
            mod = t.module or "main"
            if mod not in imported_modules:
                test_code_lines.append(f"import {mod}")
                imported_modules.add(mod)

        test_code_lines.append("\n")

        for idx, t in enumerate(payload.tests):
            fn_call_target = f"{t.module}.{t.function_name}"
            test_fn_name = f"test_{t.function_name}_{idx + 1}"
            exp_val = t.expected

            test_code_lines.append(f"def {test_fn_name}():")
            test_code_lines.append(f"    \"\"\"{t.name} - {t.purpose}\"\"\"")

            if isinstance(exp_val, str) and exp_val.endswith("Error"):
                test_code_lines.append(f"    with pytest.raises({exp_val}):")
                test_code_lines.append(f"        {fn_call_target}(*{t.input})")
            else:
                test_code_lines.append(f"    actual = {fn_call_target}(*{t.input})")
                test_code_lines.append(f"    assert actual == {repr(exp_val)}")
            test_code_lines.append("")

        zf.writestr("tests/test_suite.py", "\n".join(test_code_lines))

    zip_buffer.seek(0)
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="pytest_project_suite.zip"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )
