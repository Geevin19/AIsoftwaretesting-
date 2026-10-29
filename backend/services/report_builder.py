"""
Report Builder Service.
Computes all IEEE 829 / ISO/IEC/IEEE 29119-3 metrics, tables, defect logs,
function traceability matrix, and charts once as a unified structured model.
Prevents duplication of content logic between PDF and Word renderers.
"""
import io
import os
import tempfile
from typing import List, Dict, Any, Tuple, Optional
from schemas import (
    ReportMetadata,
    ReportGenerateRequest,
    TestResultItem,
    TestRunMetrics,
    SourceFile,
    AnalyzeCodeResponse,
    ReportNarrative
)

# Configure Matplotlib for headless, thread-safe memory rendering
os.environ["MPLCONFIGDIR"] = tempfile.gettempdir()
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def generate_pie_chart(passed: int, failed: int, errors: int) -> Optional[bytes]:
    """Generates a clean pass/fail pie chart and returns PNG image bytes."""
    labels = []
    sizes = []
    colors = []

    if passed > 0:
        labels.append(f"Pass ({passed})")
        sizes.append(passed)
        colors.append("#16a34a")  # Muted green
    if failed > 0:
        labels.append(f"Fail ({failed})")
        sizes.append(failed)
        colors.append("#dc2626")  # Muted red
    if errors > 0:
        labels.append(f"Error ({errors})")
        sizes.append(errors)
        colors.append("#d97706")  # Muted amber

    if not sizes:
        labels = ["No Runs"]
        sizes = [1]
        colors = ["#94a3b8"]

    try:
        fig, ax = plt.subplots(figsize=(4.0, 3.0), dpi=180)
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%" if sum(sizes) > 0 and sizes != [1] else "",
            startangle=140,
            textprops={"fontsize": 8, "color": "#1e293b"}
        )
        for at in autotexts:
            at.set_fontsize(8)
            at.set_color("white")
            at.set_weight("bold")
        ax.axis("equal")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", transparent=False, facecolor="#ffffff")
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
    except Exception as exc:
        print(f"Pie chart generation warning: {exc}")
        return None


def generate_category_bar_chart(normal_count: int, boundary_count: int, invalid_count: int) -> Optional[bytes]:
    """Generates a category distribution bar chart and returns PNG image bytes."""
    categories = ["Normal Cases", "Boundary Limits", "Invalid / Errors"]
    counts = [normal_count, boundary_count, invalid_count]
    colors = ["#2563eb", "#7c3aed", "#d97706"]

    try:
        fig, ax = plt.subplots(figsize=(4.5, 3.0), dpi=180)
        bars = ax.bar(categories, counts, color=colors, width=0.55, edgecolor="#cbd5e1", linewidth=0.8)
        ax.set_ylabel("Number of Test Cases", fontsize=8, color="#334155")
        ax.tick_params(axis="x", labelsize=8, colors="#334155")
        ax.tick_params(axis="y", labelsize=8, colors="#334155")
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.set_axisbelow(True)

        for bar in bars:
            height = bar.get_height()
            ax.annotate(
                f"{height}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 2),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                weight="bold",
                color="#1e293b"
            )

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", transparent=False, facecolor="#ffffff")
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
    except Exception as exc:
        print(f"Bar chart generation warning: {exc}")
        return None


def generate_regression_chart(before: Dict[str, Any], after: Dict[str, Any]) -> Optional[bytes]:
    """Generates a grouped regression comparison bar chart and returns PNG image bytes."""
    import numpy as np
    labels = ["Passed", "Failed", "Errors"]
    before_vals = [before.get("passed", 0), before.get("failed", 0), before.get("error", 0)]
    after_vals = [after.get("passed", 0), after.get("failed", 0), after.get("error", 0)]

    try:
        x = np.arange(len(labels))
        width = 0.35

        fig, ax = plt.subplots(figsize=(5.0, 3.0), dpi=180)
        rects1 = ax.bar(x - width/2, before_vals, width, label="Baseline Run", color="#94a3b8", edgecolor="#64748b")
        rects2 = ax.bar(x + width/2, after_vals, width, label="Current Run", color="#2563eb", edgecolor="#1d4ed8")

        ax.set_ylabel("Count", fontsize=8, color="#334155")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=8, color="#334155")
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.set_axisbelow(True)

        for rect in rects1:
            h = rect.get_height()
            ax.annotate(f"{h}", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 2),
                        textcoords="offset points", ha="center", va="bottom", fontsize=7)
        for rect in rects2:
            h = rect.get_height()
            ax.annotate(f"{h}", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 2),
                        textcoords="offset points", ha="center", va="bottom", fontsize=7, weight="bold")

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", transparent=False, facecolor="#ffffff")
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
    except Exception as exc:
        print(f"Regression chart generation warning: {exc}")
        return None


class StructuredTestReport:
    """Consolidated report data model matching IEEE 829 / ISO 29119 structure."""

    def __init__(self, payload: ReportGenerateRequest):
        self.metadata = payload.metadata
        self.files = payload.files or []
        self.results = payload.results or []
        self.metrics = payload.metrics
        self.analysis = payload.analysis
        self.suggestions = payload.suggestions or []
        self.comparison = payload.comparison
        self.narrative = payload.narrative

        # Extract counts
        self.total_tests = len(self.results)
        self.passed_tests = sum(1 for r in self.results if r.status == "PASS")
        self.failed_tests = sum(1 for r in self.results if r.status == "FAIL")
        self.error_tests = sum(1 for r in self.results if r.status == "ERROR")
        self.pass_percent = round((self.passed_tests / self.total_tests * 100.0) if self.total_tests > 0 else 0.0, 1)

        self.normal_count = sum(1 for r in self.results if r.category == "normal")
        self.boundary_count = sum(1 for r in self.results if r.category == "boundary")
        self.invalid_count = sum(1 for r in self.results if r.category == "invalid")

        # Compute defects
        self.defects = self._build_defect_list()
        self.high_severity_count = sum(1 for d in self.defects if d["severity"] == "High")
        self.medium_severity_count = sum(1 for d in self.defects if d["severity"] == "Medium")
        self.low_severity_count = sum(1 for d in self.defects if d["severity"] == "Low")

        # Overall engineering verdict
        threshold = self.metadata.pass_threshold or 90.0
        if self.pass_percent >= threshold and self.high_severity_count == 0:
            self.verdict = "ACCEPTED"
            self.verdict_color = "#15803d"  # green
            self.verdict_desc = f"Meets quality criteria: pass rate ({self.pass_percent}%) exceeds threshold ({threshold}%) with zero high-severity defects."
        elif self.pass_percent >= max(0.0, threshold - 15.0) and self.high_severity_count <= 1:
            self.verdict = "CONDITIONALLY ACCEPTED"
            self.verdict_color = "#b45309"  # amber
            self.verdict_desc = f"Acceptance conditional upon resolution of identified defects prior to deployment. Pass rate ({self.pass_percent}%) is near threshold ({threshold}%)."
        else:
            self.verdict = "REJECTED"
            self.verdict_color = "#b91c1c"  # red
            self.verdict_desc = f"Failed acceptance criteria: pass rate ({self.pass_percent}%) below threshold ({threshold}%) or contains critical defects ({self.high_severity_count} high severity)."

        # Test items & functions catalog
        self.tested_functions = self._build_tested_functions()
        self.traceability_matrix = self._build_traceability_matrix()

        # Quality metrics
        self.total_project_functions = len(self.analysis.functions) if self.analysis and self.analysis.functions else max(len(self.tested_functions), 1)
        self.function_coverage_pct = round((len(self.tested_functions) / self.total_project_functions) * 100.0, 1)
        self.estimated_branch_coverage_pct = self._calculate_branch_coverage()
        self.defect_density = round(len(self.defects) / max(len(self.tested_functions), 1), 2)
        self.avg_execution_time_ms = round(self.metrics.total_time_ms / max(self.total_tests, 1), 2)

        # Regression analysis
        self.has_regression_data = bool(self.comparison and self.comparison.get("has_previous_run"))
        self.regression_details = self._build_regression_details()

        # In-memory rendered charts
        self.pie_chart_png = generate_pie_chart(self.passed_tests, self.failed_tests, self.error_tests)
        self.category_chart_png = generate_category_bar_chart(self.normal_count, self.boundary_count, self.invalid_count)
        self.regression_chart_png = None
        if self.has_regression_data:
            self.regression_chart_png = generate_regression_chart(
                self.comparison.get("previous_metrics", {}),
                self.metrics.model_dump()
            )

        # Ensure narratives
        self._ensure_narratives()

    def _build_defect_list(self) -> List[Dict[str, Any]]:
        """Constructs formal defect entries for each failing/errored test."""
        defects: List[Dict[str, Any]] = []
        defect_idx = 1

        for r in self.results:
            if r.status in ("FAIL", "ERROR"):
                # Severity rules:
                # High: crash/error, failed test on normal input, or risky operations
                # Medium: boundary condition failure
                # Low: invalid input handling failure
                if r.status == "ERROR" or r.category == "normal":
                    sev = "High"
                    priority = "P1"
                elif r.category == "boundary":
                    sev = "Medium"
                    priority = "P2"
                else:
                    sev = "Low"
                    priority = "P3"

                def_id = f"DEF-{defect_idx:03d}"
                defect_idx += 1

                # Reproduction invocation call
                repro = ""
                if r.class_name:
                    repro = f'{r.class_name}(*{r.constructor_args}).{r.function_name}(*{r.input})'
                else:
                    repro = f'{r.function_name}(*{r.input})'

                # Look up matching suggestion if available
                matching_sug = ""
                for s in self.suggestions:
                    if s.get("function_name") == r.function_name or s.get("file") == r.file:
                        matching_sug = s.get("suggested_fix") or s.get("explanation") or ""
                        break

                defects.append({
                    "defect_id": def_id,
                    "title": f"Assertion failure in {r.function_name}: {r.name}",
                    "severity": sev,
                    "priority": priority,
                    "status": "Open",
                    "file": r.file,
                    "function": r.function_name,
                    "category": r.category,
                    "steps": repro,
                    "input": str(r.input),
                    "expected": str(r.expected),
                    "actual": str(r.actual),
                    "error_message": r.error_message or "",
                    "root_cause": "",
                    "recommended_fix": matching_sug
                })
        return defects

    def _build_tested_functions(self) -> List[Dict[str, Any]]:
        """Extracts unique tested functions with AST structural data."""
        fns_map = {}
        for r in self.results:
            key = f"{r.file}::{r.class_name + '.' if r.class_name else ''}{r.function_name}"
            if key not in fns_map:
                fns_map[key] = {
                    "id": key,
                    "file": r.file,
                    "module": r.module,
                    "class_name": r.class_name or "-",
                    "function_name": r.function_name,
                    "display_name": f"{r.class_name + '.' if r.class_name else ''}{r.function_name}",
                    "tests_count": 0,
                    "passed_count": 0,
                    "failed_count": 0,
                    "branches": 1,
                    "raises": []
                }
            fns_map[key]["tests_count"] += 1
            if r.status == "PASS":
                fns_map[key]["passed_count"] += 1
            else:
                fns_map[key]["failed_count"] += 1

        # Enrich with AST analysis if present
        if self.analysis and self.analysis.functions:
            for afn in self.analysis.functions:
                key = f"{afn.file}::{afn.class_name + '.' if afn.class_name else ''}{afn.function_name}"
                if key in fns_map:
                    fns_map[key]["branches"] = afn.branch_count
                    fns_map[key]["raises"] = afn.raises

        return list(fns_map.values())

    def _build_traceability_matrix(self) -> List[Dict[str, Any]]:
        """Builds requirements/function traceability matrix across categories."""
        matrix = []
        for fn in self.tested_functions:
            fn_results = [
                r for r in self.results
                if r.file == fn["file"] and r.function_name == fn["function_name"]
            ]

            normal_tests = [r for r in fn_results if r.category == "normal"]
            boundary_tests = [r for r in fn_results if r.category == "boundary"]
            invalid_tests = [r for r in fn_results if r.category == "invalid"]

            n_pass = sum(1 for r in normal_tests if r.status == "PASS")
            b_pass = sum(1 for r in boundary_tests if r.status == "PASS")
            i_pass = sum(1 for r in invalid_tests if r.status == "PASS")

            n_str = f"{len(normal_tests)} ({n_pass} Pass)" if normal_tests else "-"
            b_str = f"{len(boundary_tests)} ({b_pass} Pass)" if boundary_tests else "-"
            i_str = f"{len(invalid_tests)} ({i_pass} Pass)" if invalid_tests else "-"

            overall = "PASS" if all(r.status == "PASS" for r in fn_results) else "FAIL"

            matrix.append({
                "function": fn["display_name"],
                "file": fn["file"],
                "normal": n_str,
                "boundary": b_str,
                "invalid": i_str,
                "total": len(fn_results),
                "status": overall
            })
        return matrix

    def _calculate_branch_coverage(self) -> float:
        """Estimates branch coverage percentage based on exercised paths."""
        total_branches = sum(fn["branches"] for fn in self.tested_functions) or 1
        covered_branches = 0
        for fn in self.tested_functions:
            fn_results = [r for r in self.results if r.function_name == fn["function_name"]]
            # Heuristic: distinct inputs exercise distinct branches up to total branch count
            distinct_inputs = len(set(str(r.input) for r in fn_results))
            covered_branches += min(fn["branches"], max(1, distinct_inputs))
        return round(min(100.0, (covered_branches / total_branches) * 100.0), 1)

    def _build_regression_details(self) -> Dict[str, Any]:
        """Classifies regression outcomes between consecutive runs."""
        if not self.has_regression_data:
            return {}

        prev_results = self.comparison.get("previous_results", [])
        prev_map = {r.get("name"): r.get("status") for r in prev_results if "name" in r}

        fixed = []
        regressions = []
        unchanged = []

        for curr in self.results:
            name = curr.name
            prev_status = prev_map.get(name)
            curr_status = curr.status

            if prev_status:
                if prev_status in ("FAIL", "ERROR") and curr_status == "PASS":
                    fixed.append({"name": name, "file": curr.file, "was": prev_status, "now": curr_status})
                elif prev_status == "PASS" and curr_status in ("FAIL", "ERROR"):
                    regressions.append({"name": name, "file": curr.file, "was": prev_status, "now": curr_status})
                else:
                    unchanged.append({"name": name, "file": curr.file, "status": curr_status})

        return {
            "fixed": fixed,
            "regressions": regressions,
            "unchanged": unchanged,
            "prev_metrics": self.comparison.get("previous_metrics", {})
        }

    def _ensure_narratives(self):
        """Builds formal third-person past-tense template prose if AI narrative is absent."""
        # 1. Executive Summary
        if not self.narrative or not self.narrative.executive_summary:
            exec_p = (
                f"Automated software quality verification was conducted on {self.metadata.test_date} for "
                f"{self.metadata.project_name}. A total of {self.total_tests} test cases were executed across "
                f"{len(self.files) or 1} module(s) and {len(self.tested_functions)} function(s). "
                f"{self.passed_tests} test cases passed and {self.failed_tests + self.error_tests} test cases failed, "
                f"yielding an overall pass rate of {self.pass_percent}%. Based on the established quality acceptance "
                f"threshold of {self.metadata.pass_threshold}%, the formal engineering verdict is {self.verdict}."
            )
        else:
            exec_p = self.narrative.executive_summary

        # 2. Risk Assessment
        if not self.narrative or not self.narrative.risk_assessment:
            if self.high_severity_count > 0:
                risk_p = (
                    f"Testing identified {self.high_severity_count} high-severity defect(s) and "
                    f"{self.medium_severity_count} boundary limit discrepancy(ies). Deploying this build without remediation "
                    f"presents significant operational risk regarding data integrity and unexpected exceptions in production."
                )
            else:
                risk_p = (
                    f"No critical defects were identified across tested core components. Residual risk is low, "
                    f"limited to unexercised asynchronous behaviors and operating system specific filesystem variations."
                )
        else:
            risk_p = self.narrative.risk_assessment

        # 3. Recommendations
        if not self.narrative or not self.narrative.recommendations:
            if self.defects:
                recs_p = (
                    f"1. Remediate the {len(self.defects)} identified defect(s) in priority order (P1 critical items first). "
                    f"2. Incorporate explicit boundary guards for comparison operators and None value checks. "
                    f"3. Re-execute the automated test suite to ensure no regression defects are introduced prior to final release."
                )
            else:
                recs_p = (
                    f"1. Maintain current test suite in the continuous integration pipeline. "
                    f"2. Extend boundary tests to cover edge cases for newly planned modules."
                )
        else:
            recs_p = self.narrative.recommendations

        # 4. Defect root causes
        defects_analysis = self.narrative.defects_analysis if self.narrative else {}
        for d in self.defects:
            did = d["defect_id"]
            if did in defects_analysis and defects_analysis[did]:
                d["root_cause"] = defects_analysis[did]
            else:
                d["root_cause"] = (
                    f"Expected outcome '{d['expected']}' was not met; received '{d['actual']}'. "
                    f"Input {d['input']} triggered an unhandled condition or incorrect comparison in {d['function']}."
                )

        self.executive_summary_text = exec_p
        self.risk_assessment_text = risk_p
        self.recommendations_text = recs_p


def build_structured_report(payload: ReportGenerateRequest) -> StructuredTestReport:
    """Factory function to build and populate structured report object."""
    return StructuredTestReport(payload)
