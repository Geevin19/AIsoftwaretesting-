"""
Pydantic Schemas for AI-Assisted Software Testing Assistant.
Defines strong input/output data validation models across all API endpoints,
including static AST analysis, grounded test generation, validation, and execution.
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class SourceFile(BaseModel):
    """Represents an individual source code file in a project."""
    path: str = Field(..., description="Relative file path, e.g. 'main.py' or 'utils/math_ops.py'")
    content: str = Field(..., description="Decoded UTF-8 source text")
    syntax_error: Optional[str] = Field(default=None, description="Syntax error message with line number if any")
    included: bool = Field(default=True, description="Whether to include in automated test analysis")


class SkippedFile(BaseModel):
    """Details of a file skipped during upload validation."""
    path: str = Field(..., description="File path that was skipped")
    reason: str = Field(..., description="Clear explanation for why the file was skipped")


class UploadResponse(BaseModel):
    """Response returned by /api/upload containing processed and skipped files."""
    files: List[SourceFile] = Field(default_factory=list, description="Accepted source files")
    skipped: List[SkippedFile] = Field(default_factory=list, description="Skipped files with reasons")
    total_files: int = 0
    total_size_bytes: int = 0


# ---------------------------------------------------------------------------
# Stage 1: Static AST Analysis Models
# ---------------------------------------------------------------------------

class ParameterMeta(BaseModel):
    """Parameter signature details extracted via AST."""
    name: str
    type_hint: Optional[str] = None
    default: Optional[str] = None
    required: bool = True

    @property
    def is_required(self) -> bool:
        return self.required


class FunctionMetadata(BaseModel):
    """Complete structural metadata for a function or class method extracted via AST."""
    id: str = Field(..., description="Unique identifier e.g. 'utils/math.py::Calculator::divide'")
    file: str = Field(..., description="File path containing definition")
    module: str = Field(..., description="Python dotted module path")
    class_name: Optional[str] = Field(default=None, description="Class name if method, else None")
    function_name: str = Field(..., description="Function or method name")
    is_method: bool = False
    is_async: bool = False
    parameters: List[ParameterMeta] = Field(default_factory=list)
    constructor_args: List[ParameterMeta] = Field(default_factory=list, description="Arguments for class __init__")
    return_annotation: Optional[str] = None
    docstring: Optional[str] = None
    raises: List[str] = Field(default_factory=list, description="Exception types raised in function body")
    branch_count: int = Field(default=1, description="Cyclomatic complexity / decision branches count")
    comparison_conditions: List[str] = Field(default_factory=list, description="Comparison code snippets")
    risky_calls: List[str] = Field(default_factory=list, description="Detected risky operations e.g. open, input, eval")


class SyntaxErrorItem(BaseModel):
    """Reported syntax error in a source file."""
    file: str
    line: int
    message: str


class AnalysisSummary(BaseModel):
    """High level statistics from AST code analysis."""
    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0
    risky_functions_count: int = 0


class AnalyzeCodeRequest(BaseModel):
    """Request payload to perform Stage 1 Static AST Analysis."""
    files: Optional[List[SourceFile]] = None
    code: Optional[str] = None


class AnalyzeCodeResponse(BaseModel):
    """Response returned by /api/analyze-code."""
    functions: List[FunctionMetadata] = Field(default_factory=list)
    syntax_errors: List[SyntaxErrorItem] = Field(default_factory=list)
    summary: AnalysisSummary


# ---------------------------------------------------------------------------
# Stage 2: Test Case & Generation Models
# ---------------------------------------------------------------------------

class TestCase(BaseModel):
    """Represents an individual unit test case."""
    id: Optional[str] = Field(default=None, description="Unique identifier for the test case")
    name: str = Field(..., description="Short descriptive test case name")
    category: str = Field(..., description="Category: 'normal', 'boundary', or 'invalid'")
    file: str = Field(default="main.py", description="Source file containing target function")
    module: str = Field(default="main", description="Python dotted import path")
    class_name: Optional[str] = Field(default=None, description="Target class name if calling an instance method")
    constructor_args: List[Any] = Field(default_factory=list, description="Arguments passed to class constructor")
    function_name: str = Field(..., description="Target function or method name to invoke")
    input: List[Any] = Field(default_factory=list, description="Ordered arguments passed to function")
    expected: Any = Field(..., description="Expected return value or exception name")
    purpose: str = Field(..., description="One-line human explanation of what this test verifies")
    is_ai: bool = Field(default=True, description="True if AI-generated, False if manual")
    coverage_note: Optional[str] = Field(default=None, description="Coverage details e.g. covers 3 of 4 branches")


class GenerateTestsRequest(BaseModel):
    """Payload to request automated test case generation."""
    files: Optional[List[SourceFile]] = Field(default=None, description="Project files")
    code: Optional[str] = Field(default=None, description="Single file snippet fallback")
    selected_functions: Optional[List[Union[str, Dict[str, Any], FunctionMetadata]]] = Field(
        default=None, description="List of function IDs or function metadata objects to target"
    )
    per_function: int = Field(default=6, description="Number of tests per function (normal, boundary, invalid)")
    language: str = Field(default="python", description="Programming language")


class GenerateTestsResponse(BaseModel):
    """Response containing AI-generated and validated test suite."""
    tests: List[TestCase]
    count: int
    rejected: List[Dict[str, Any]] = Field(default_factory=list, description="Tests rejected during validation")
    skipped_functions: List[Dict[str, Any]] = Field(default_factory=list, description="Functions skipped e.g. risky calls")
    coverage_notes: List[Dict[str, Any]] = Field(default_factory=list, description="Coverage summary per function")
    message: Optional[str] = "Tests generated successfully"


class GenerateMoreRequest(BaseModel):
    """Payload to request additional tests for a specific function."""
    files: List[SourceFile]
    function_id: Optional[str] = None
    category: Optional[str] = None
    count: int = 3
    existing_tests: List[TestCase] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Test Execution Models
# ---------------------------------------------------------------------------

class RunTestsRequest(BaseModel):
    """Payload to execute test suite against user code or multi-file project."""
    files: Optional[List[SourceFile]] = Field(default=None, description="Project files")
    code: Optional[str] = Field(default=None, description="Single file snippet fallback")
    tests: List[TestCase] = Field(..., min_length=1, description="List of test cases to execute")


class TestResultItem(BaseModel):
    """Execution result for an individual test case."""
    id: str
    name: str
    category: str
    file: str = "main.py"
    module: str = "main"
    class_name: Optional[str] = None
    constructor_args: List[Any] = Field(default_factory=list)
    function_name: str
    input: List[Any]
    expected: Any
    actual: Any
    status: str = Field(..., description="Execution status: 'PASS', 'FAIL', or 'ERROR'")
    execution_time_ms: float = Field(..., description="Execution duration in milliseconds")
    error_message: Optional[str] = None
    purpose: Optional[str] = None
    is_ai: bool = True


class TestRunMetrics(BaseModel):
    """Aggregated statistical metrics of a test execution run."""
    total: int
    passed: int
    failed: int
    error: int
    pass_percent: float
    total_time_ms: float


class RunTestsResponse(BaseModel):
    """Overall response containing test run results and metrics."""
    results: List[TestResultItem]
    metrics: TestRunMetrics


# ---------------------------------------------------------------------------
# Analysis & Export Models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    """Payload to request AI bug explanation and fix suggestion for a failing test."""
    files: Optional[List[SourceFile]] = Field(default=None, description="Full project files for context")
    code: Optional[str] = Field(default=None, description="Single source code fallback")
    test: TestCase = Field(..., description="The failing test case details")
    actual: Any = Field(..., description="Actual output or exception received during execution")
    status: str = Field(..., description="Result status ('FAIL' or 'ERROR')")


class AnalyzeResponse(BaseModel):
    """Response containing root-cause analysis and proposed code fix for a specific file."""
    explanation: str = Field(..., description="Clear explanation of the bug and why the test failed")
    suggested_fix: str = Field(..., description="Corrected source code resolving the issue")
    file: str = Field(default="main.py", description="The specific file that was fixed")


class ExportPytestRequest(BaseModel):
    """Payload to export project files with generated pytest suite."""
    files: List[SourceFile] = Field(..., min_length=1, description="Source files")
    tests: List[TestCase] = Field(..., min_length=1, description="Test cases")


class SampleMetadata(BaseModel):
    """Metadata describing an available code sample."""
    id: str
    title: str
    filename: str
    description: str
    language: str = "python"


class SampleResponse(SampleMetadata):
    """Full sample details including source code."""
    code: str


# ---------------------------------------------------------------------------
# Stage 5: Formal Software Test Report Models (IEEE 829 / ISO 29119)
# ---------------------------------------------------------------------------

class ReportMetadata(BaseModel):
    """Metadata details for formal IEEE 829 / ISO 29119 test summary report."""
    project_name: str = Field(default="AI-Assisted Software Testing Project")
    report_title: str = Field(default="Software Test Summary Report")
    document_id: str = Field(default="TR-20261030-001")
    version: str = Field(default="1.0")
    organization: str = Field(default="Department of Software Engineering")
    prepared_by: str = Field(default="QA Automation Lead")
    reviewed_by: str = Field(default="Principal Systems Architect")
    test_environment: str = Field(default="Windows 11 / Python 3.9 / FastAPI / Isolated Subprocess Runner")
    test_date: str = Field(default="2026-10-30")
    pass_threshold: float = Field(default=90.0, ge=0.0, le=100.0)


class ReportNarrative(BaseModel):
    """AI-synthesized prose sections for the formal test report."""
    executive_summary: str = Field(default="")
    risk_assessment: str = Field(default="")
    recommendations: str = Field(default="")
    defects_analysis: Dict[str, str] = Field(default_factory=dict, description="defect_id -> root cause analysis")


class ReportNarrativeRequest(BaseModel):
    """Payload to synthesize AI narrative paragraphs for the report."""
    metadata: ReportMetadata
    metrics: TestRunMetrics
    results: List[TestResultItem]
    functions_count: int = 0
    files_count: int = 0
    high_severity_count: int = 0
    failed_tests_summary: List[Dict[str, Any]] = Field(default_factory=list)


class ReportGenerateRequest(BaseModel):
    """Payload to build and render formal PDF or Word (.docx) test reports."""
    metadata: ReportMetadata
    files: List[SourceFile] = Field(default_factory=list)
    results: List[TestResultItem] = Field(default_factory=list)
    metrics: TestRunMetrics
    analysis: Optional[AnalyzeCodeResponse] = None
    suggestions: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    comparison: Optional[Dict[str, Any]] = None
    narrative: Optional[ReportNarrative] = None

