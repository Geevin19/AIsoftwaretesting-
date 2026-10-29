"""
Analysis Router:
Endpoint to diagnose test failures and generate AI-assisted bug fixes
targeting specific files in single-file or multi-file projects.
"""
from fastapi import APIRouter, HTTPException, status
from schemas import AnalyzeRequest, AnalyzeResponse, SourceFile
from services.bug_analyzer import analyze_test_failure_multi

router = APIRouter(prefix="/api", tags=["Analysis"])


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Diagnose failing test and propose source code fix for target file"
)
def analyze_failure_endpoint(payload: AnalyzeRequest):
    """
    Receives failing test context and project files, diagnoses root cause,
    and returns explanation along with corrected code for the failing file.
    """
    files = payload.files
    if not files:
        if payload.code and payload.code.strip():
            files = [SourceFile(path="main.py", content=payload.code)]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source files or code must be provided for bug analysis."
            )

    try:
        result = analyze_test_failure_multi(
            files=files,
            test=payload.test,
            actual=str(payload.actual),
            status=payload.status
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bug analysis failed: {str(exc)}"
        )
