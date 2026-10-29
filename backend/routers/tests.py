"""
Tests Router:
Endpoints for Static AST Code Analysis, Two-Stage Grounded AI Test Generation,
Targeted Test Generation, and Subprocess Test Execution.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from schemas import (
    SourceFile,
    GenerateTestsRequest,
    GenerateTestsResponse,
    GenerateMoreRequest,
    RunTestsRequest,
    RunTestsResponse,
    AnalyzeCodeRequest,
    AnalyzeCodeResponse,
    TestCase
)
from services.code_analyzer import analyze_source_files
from services.test_generator import generate_tests_pipeline, synthesize_ast_grounded_fallback
from services.test_validator import validate_test_cases
from services.test_runner import execute_test_suite_multi

router = APIRouter(prefix="/api", tags=["Tests & Code Analysis"])


@router.post(
    "/analyze-code",
    response_model=AnalyzeCodeResponse,
    summary="Stage 1: Perform Static AST Analysis across project files (No AI)"
)
def analyze_code_endpoint(payload: AnalyzeCodeRequest):
    """
    Parses every included source file using Python's ast module.
    Extracts public functions, classes, methods, parameters with type hints,
    constructor arguments, raised exceptions, branches, conditions, and risky calls.
    """
    files = payload.files
    if not files:
        if payload.code and payload.code.strip():
            files = [SourceFile(path="main.py", content=payload.code, included=True)]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source files or code must be provided for static analysis."
            )

    try:
        functions, syntax_errors, summary = analyze_source_files(files)
        return AnalyzeCodeResponse(
            functions=functions,
            syntax_errors=syntax_errors,
            summary=summary
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AST Code Analysis failed: {str(e)}"
        )


@router.post(
    "/generate-tests",
    response_model=GenerateTestsResponse,
    summary="Stage 2: Generate Grounded Unit Test Cases using AST Metadata"
)
def generate_tests_endpoint(payload: GenerateTestsRequest):
    """
    Generates unit test cases grounded in Stage 1 Static AST analysis:
    - Analyzes included files
    - Filters selected functions if specified
    - Invokes Gemini LLM in batches or grounded AST synthesizer
    - Validates argument count, constructor args, and prevents hallucinations
    - Caps tests at maximum 40 per request
    """
    files = payload.files
    if not files:
        if payload.code and payload.code.strip():
            files = [SourceFile(path="main.py", content=payload.code, included=True)]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source files or code must be provided for test generation."
            )

    try:
        selected_ids = None
        if payload.selected_functions:
            selected_ids = []
            for item in payload.selected_functions:
                if isinstance(item, str):
                    selected_ids.append(item)
                elif hasattr(item, "id") and getattr(item, "id"):
                    selected_ids.append(getattr(item, "id"))
                elif isinstance(item, dict) and "id" in item:
                    selected_ids.append(item["id"])
                elif hasattr(item, "function_name") and getattr(item, "function_name"):
                    selected_ids.append(getattr(item, "function_name"))
                elif isinstance(item, dict) and "function_name" in item:
                    selected_ids.append(item["function_name"])
                elif isinstance(item, dict) and "name" in item:
                    selected_ids.append(item["name"])

        valid_tests, rejected, skipped_functions, coverage_notes = generate_tests_pipeline(
            files=files,
            selected_function_ids=selected_ids,
            per_function=payload.per_function or 6,
            language=payload.language
        )

        return GenerateTestsResponse(
            tests=valid_tests,
            count=len(valid_tests),
            rejected=rejected,
            skipped_functions=skipped_functions,
            coverage_notes=coverage_notes,
            message=f"Generated and validated {len(valid_tests)} test cases across project functions."
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test generation error: {str(e)}"
        )


@router.post(
    "/generate-more",
    response_model=GenerateTestsResponse,
    summary="Generate additional test cases for a specific function or category"
)
def generate_more_endpoint(payload: GenerateMoreRequest):
    """Generates extra validated, deduplicated tests for a specific function or category."""
    if not payload.files:
        raise HTTPException(status_code=400, detail="Project files required.")

    functions, _, _ = analyze_source_files(payload.files)
    if not functions:
        raise HTTPException(status_code=400, detail="No functions found in project files.")

    target_fn = None
    if payload.function_id and payload.function_id != "all":
        target_fn = next((f for f in functions if f.id == payload.function_id or f.function_name == payload.function_id), None)

    target_fns = [target_fn] if target_fn else functions

    new_tests: List[TestCase] = []
    for fn in target_fns:
        synthesized = synthesize_ast_grounded_fallback(fn, per_function=max(3, payload.count))
        if payload.category and payload.category != "all":
            synthesized = [t for t in synthesized if t.category == payload.category]
        new_tests.extend(synthesized[:payload.count])

    valid_tests, rejected, skipped_functions, coverage_notes = validate_test_cases(
        new_tests,
        target_fns
    )

    # Filter out tests that are already in existing_tests
    existing_fingerprints = set(
        (t.module, t.class_name or "", t.function_name, str(t.input), str(t.expected))
        for t in payload.existing_tests
    )
    deduped = [
        t for t in valid_tests
        if (t.module, t.class_name or "", t.function_name, str(t.input), str(t.expected)) not in existing_fingerprints
    ]

    return GenerateTestsResponse(
        tests=deduped,
        count=len(deduped),
        rejected=rejected,
        skipped_functions=skipped_functions,
        coverage_notes=coverage_notes,
        message=f"Generated {len(deduped)} additional validated tests."
    )


@router.post(
    "/run-tests",
    response_model=RunTestsResponse,
    summary="Execute Unit Tests in Isolated Subprocess Harness"
)
def run_tests_endpoint(payload: RunTestsRequest):
    """
    Executes tests against project files written to a temporary workspace with 5-second timeouts.
    Supports top-level functions and class method invocations.
    """
    files = payload.files
    if not files:
        if payload.code and payload.code.strip():
            files = [SourceFile(path="main.py", content=payload.code, included=True)]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source files or code must be provided to run tests."
            )

    if not payload.tests:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one test case must be provided."
        )

    try:
        response = execute_test_suite_multi(files, payload.tests)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test suite execution failed: {str(e)}"
        )
