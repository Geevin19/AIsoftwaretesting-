"""
Upload Router:
Handles multi-file, directory, and .zip project uploads with comprehensive
validation, zip-bomb prevention, directory filtering, and AST syntax checks.

SECURITY NOTE:
Uploaded files are NEVER executed at upload time. Files are purely decoded,
parsed with ast.parse to detect syntax errors, and returned to client-side state.
In production, user code execution must only occur in sandboxed microVMs (e.g., Firecracker)
or secure container runtimes (e.g., gVisor, Docker with strict limits).
"""
import io
import os
import ast
import zipfile
from typing import List, Dict, Tuple, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from schemas import UploadResponse, SourceFile, SkippedFile

router = APIRouter(prefix="/api", tags=["Upload"])

# ---------------------------------------------------------------------------
# Security & Validation Constants
# ---------------------------------------------------------------------------
MAX_FILES = 25
MAX_FILE_SIZE_BYTES = 200 * 1024       # 200 KB per file limit
MAX_TOTAL_SIZE_BYTES = 1024 * 1024     # 1 MB project total limit
MAX_ZIP_SIZE_BYTES = 5 * 1024 * 1024   # 5 MB zip archive limit
MAX_ZIP_UNCOMPRESSED_BYTES = 10 * 1024 * 1024  # 10 MB uncompressed cap (zip bomb defense)
ALLOWED_EXTENSIONS = {".py"}
IGNORED_DIRS = {
    ".git", "venv", ".venv", "env", "__pycache__", "node_modules",
    ".idea", ".vscode", "dist", "build", "site-packages"
}


def normalize_rel_path(path_str: str) -> str:
    """Normalizes path string to clean, relative forward-slash format."""
    cleaned = path_str.replace("\\", "/").strip().lstrip("/")
    parts = [p for p in cleaned.split("/") if p and p != "."]
    return "/".join(parts)


def is_ignored_path(path_str: str) -> bool:
    """Checks whether any segment in the path belongs to ignored directories."""
    parts = path_str.replace("\\", "/").split("/")
    return any(p in IGNORED_DIRS for p in parts)


def strip_common_root_prefix(file_dict: Dict[str, Tuple[str, Optional[str]]]) -> Dict[str, Tuple[str, Optional[str]]]:
    """
    If all files share a single common top-level directory (e.g., 'my-repo-main/foo.py'),
    strips that common directory so paths start directly inside the project root.
    """
    if len(file_dict) <= 1:
        # If single file has a folder, only strip if it's a wrapper
        first_path = next(iter(file_dict.keys()))
        parts = first_path.split("/")
        if len(parts) > 1 and parts[0] in ("src", "app"):
            return file_dict
        return file_dict

    paths = list(file_dict.keys())
    split_paths = [p.split("/") for p in paths]
    first_components = [sp[0] for sp in split_paths if len(sp) > 1]

    # If every file with folders shares the exact same first directory name
    if first_components and len(first_components) == len(split_paths) and len(set(first_components)) == 1:
        common_prefix = first_components[0] + "/"
        return {
            p[len(common_prefix):]: val for p, val in file_dict.items()
        }
    return file_dict


def check_syntax(content: str) -> Tuple[bool, Optional[str]]:
    """Runs ast.parse to detect syntax errors without executing code."""
    try:
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        line = e.lineno or 1
        msg = e.msg or "Syntax error"
        return False, f"Line {line}: {msg}"


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload individual files, folders, or .zip archive for testing analysis"
)
async def upload_files_endpoint(files: List[UploadFile] = File(...)):
    """
    Accepts raw multipart files (individual, folder trees, or zip archives).
    Applies strict validation:
    - Filters only .py files
    - Ignores venv, node_modules, .git, etc.
    - Limits to max 25 files, 200 KB/file, 1 MB total
    - Checks AST syntax and flags invalid syntax without crashing
    """
    accepted_files: Dict[str, Tuple[str, Optional[str]]] = {}  # path -> (content, syntax_err)
    skipped_files: List[SkippedFile] = []
    total_size_bytes = 0

    for upload in files:
        filename = upload.filename or "uploaded_file"
        raw_bytes = await upload.read()
        file_size = len(raw_bytes)

        # -------------------------------------------------------------------
        # 1. Handle .zip archive uploads
        # -------------------------------------------------------------------
        if filename.lower().endswith(".zip"):
            if file_size > MAX_ZIP_SIZE_BYTES:
                skipped_files.append(SkippedFile(
                    path=filename,
                    reason=f"Zip archive exceeds maximum limit of {MAX_ZIP_SIZE_BYTES // (1024 * 1024)} MB."
                ))
                continue

            try:
                zip_buffer = io.BytesIO(raw_bytes)
                with zipfile.ZipFile(zip_buffer, "r") as zf:
                    uncompressed_total = sum(zinfo.file_size for zinfo in zf.infolist())
                    if uncompressed_total > MAX_ZIP_UNCOMPRESSED_BYTES:
                        skipped_files.append(SkippedFile(
                            path=filename,
                            reason="Zip archive rejected: uncompressed size exceeds 10 MB limit (zip bomb protection)."
                        ))
                        continue

                    for zinfo in zf.infolist():
                        if zinfo.is_dir():
                            continue

                        norm_path = normalize_rel_path(zinfo.filename)
                        parts = norm_path.split("/")

                        # Zip path security checks
                        if ".." in parts or os.path.isabs(norm_path) or norm_path.startswith("/"):
                            skipped_files.append(SkippedFile(
                                path=zinfo.filename,
                                reason="Illegal path traversal characters detected."
                            ))
                            continue

                        # Directory ignore check
                        if is_ignored_path(norm_path):
                            skipped_files.append(SkippedFile(
                                path=norm_path,
                                reason="File is inside an ignored directory (e.g., venv, .git, node_modules)."
                            ))
                            continue

                        # Extension check
                        ext = os.path.splitext(norm_path)[1].lower()
                        if ext not in ALLOWED_EXTENSIONS:
                            skipped_files.append(SkippedFile(
                                path=norm_path,
                                reason=f"Unsupported file type '{ext}'. Only .py files are supported in this version."
                            ))
                            continue

                        # Per-file size check
                        if zinfo.file_size > MAX_FILE_SIZE_BYTES:
                            skipped_files.append(SkippedFile(
                                path=norm_path,
                                reason=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // 1024} KB."
                            ))
                            continue

                        # Project file count cap
                        if len(accepted_files) >= MAX_FILES:
                            skipped_files.append(SkippedFile(
                                path=norm_path,
                                reason=f"Project exceeded maximum file limit of {MAX_FILES} files."
                            ))
                            continue

                        # Decode content
                        try:
                            file_bytes = zf.read(zinfo)
                            content_str = file_bytes.decode("utf-8")
                        except UnicodeDecodeError:
                            skipped_files.append(SkippedFile(
                                path=norm_path,
                                reason="Unable to decode file as UTF-8 text."
                            ))
                            continue

                        # Check total size
                        if total_size_bytes + len(file_bytes) > MAX_TOTAL_SIZE_BYTES:
                            skipped_files.append(SkippedFile(
                                path=norm_path,
                                reason=f"Project exceeds maximum cumulative size of {MAX_TOTAL_SIZE_BYTES // 1024} KB."
                            ))
                            continue

                        # AST Syntax check
                        is_valid, syntax_err = check_syntax(content_str)
                        accepted_files[norm_path] = (content_str, syntax_err)
                        total_size_bytes += len(file_bytes)

            except zipfile.BadZipFile:
                skipped_files.append(SkippedFile(
                    path=filename,
                    reason="Corrupt or invalid zip archive."
                ))
            continue

        # -------------------------------------------------------------------
        # 2. Handle Individual Files and Webkit Directory Uploads
        # -------------------------------------------------------------------
        norm_path = normalize_rel_path(filename)
        parts = norm_path.split("/")

        if ".." in parts or os.path.isabs(norm_path):
            skipped_files.append(SkippedFile(
                path=filename,
                reason="Illegal path traversal characters detected."
            ))
            continue

        if is_ignored_path(norm_path):
            skipped_files.append(SkippedFile(
                path=norm_path,
                reason="File is inside an ignored directory (e.g., venv, .git, node_modules)."
            ))
            continue

        ext = os.path.splitext(norm_path)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            skipped_files.append(SkippedFile(
                path=norm_path,
                reason=f"Unsupported file type '{ext}'. Only .py files are supported in this version."
            ))
            continue

        if file_size > MAX_FILE_SIZE_BYTES:
            skipped_files.append(SkippedFile(
                path=norm_path,
                reason=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // 1024} KB."
            ))
            continue

        if len(accepted_files) >= MAX_FILES:
            skipped_files.append(SkippedFile(
                path=norm_path,
                reason=f"Project exceeded maximum file limit of {MAX_FILES} files."
            ))
            continue

        try:
            content_str = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            skipped_files.append(SkippedFile(
                path=norm_path,
                reason="Unable to decode file as UTF-8 text."
            ))
            continue

        if total_size_bytes + file_size > MAX_TOTAL_SIZE_BYTES:
            skipped_files.append(SkippedFile(
                path=norm_path,
                reason=f"Project exceeds maximum cumulative size of {MAX_TOTAL_SIZE_BYTES // 1024} KB."
            ))
            continue

        # AST Syntax check
        is_valid, syntax_err = check_syntax(content_str)
        accepted_files[norm_path] = (content_str, syntax_err)
        total_size_bytes += file_size

    # Strip single common top-level directory prefix (e.g. 'repo-main/calc.py' -> 'calc.py')
    cleaned_dict = strip_common_root_prefix(accepted_files)

    result_files: List[SourceFile] = []
    for path, (content, syn_err) in cleaned_dict.items():
        result_files.append(SourceFile(
            path=path,
            content=content,
            syntax_error=syn_err,
            included=(syn_err is None)  # exclude files with syntax errors by default
        ))

    return UploadResponse(
        files=result_files,
        skipped=skipped_files,
        total_files=len(result_files),
        total_size_bytes=total_size_bytes
    )
