"""
Samples Router:
Endpoints to list and retrieve pre-configured buggy Python code samples
designed for college software testing demonstrations.
"""
import os
from typing import List
from fastapi import APIRouter, HTTPException
from schemas import SampleMetadata, SampleResponse

router = APIRouter(prefix="/api/samples", tags=["Samples"])

SAMPLES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "samples"))

SAMPLE_CATALOG = {
    "calculator": {
        "id": "calculator",
        "title": "Calculator with Edge-Case Bug",
        "filename": "calculator.py",
        "description": "Standard arithmetic calculator that mistakenly returns 0.0 on division by zero instead of raising ZeroDivisionError.",
        "language": "python"
    },
    "login_validator": {
        "id": "login_validator",
        "title": "Login Credential Validator",
        "filename": "login_validator.py",
        "description": "User credential validator with a boundary bug allowing 6-character passwords instead of enforcing the 8-character requirement.",
        "language": "python"
    }
}


@router.get("", response_model=List[SampleMetadata])
def list_samples():
    """Returns catalog of available sample buggy programs."""
    return list(SAMPLE_CATALOG.values())


@router.get("/{name}", response_model=SampleResponse)
def get_sample_by_name(name: str):
    """Retrieves metadata and full source code for a specific sample."""
    sample_key = name.lower().replace(".py", "")
    if sample_key not in SAMPLE_CATALOG:
        raise HTTPException(status_code=404, detail=f"Sample '{name}' not found. Available: {list(SAMPLE_CATALOG.keys())}")

    meta = SAMPLE_CATALOG[sample_key]
    file_path = os.path.join(SAMPLES_DIR, meta["filename"])

    if not os.path.exists(file_path):
        raise HTTPException(status_code=500, detail=f"Sample source file '{meta['filename']}' missing on disk.")

    with open(file_path, "r", encoding="utf-8") as f:
        code_content = f.read()

    return SampleResponse(
        id=meta["id"],
        title=meta["title"],
        filename=meta["filename"],
        description=meta["description"],
        language=meta["language"],
        code=code_content
    )
