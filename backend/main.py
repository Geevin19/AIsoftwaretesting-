"""
FastAPI Main Application Entry Point.
AI-Assisted Software Testing Assistant.

Features:
- FastAPI REST API for test generation, project upload, subprocess runner, bug diagnosis, and reporting
- Clean terminal logging (suppresses Python 3.9 library deprecation warnings)
- Direct frontend serving: When accessed from a web browser on http://127.0.0.1:8000,
  serves the built React application directly!
- Full CORS support for Vite dev server on http://localhost:5173
- Eliminates 404 on favicon.ico
"""
import os
import warnings

# Suppress noisy library deprecation / end-of-life warnings in terminal
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", module="google")

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load local environment variables from .env file
load_dotenv()

# Import sub-routers
from routers import samples, tests, analysis, reports, upload

app = FastAPI(
    title="AI-Assisted Software Testing Assistant API",
    description="Stateless Backend API for multi-file project test generation, subprocess test execution, AI bug explanation, and QA reporting.",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Allowed frontend origins (Vite dev server)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*"  # Allows smooth local micro project testing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(upload.router)
app.include_router(samples.router)
app.include_router(tests.router)
app.include_router(analysis.router)
app.include_router(reports.router)

# Suppress favicon 404 in logs
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

# Path to built frontend
FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
ASSETS_DIR = os.path.join(FRONTEND_DIST, "assets")

if os.path.exists(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


@app.get("/api/health", tags=["Health Check"])
def health_check():
    """Explicit JSON health check endpoint."""
    return {
        "status": "online",
        "service": "AI-Assisted Software Testing Assistant Backend",
        "version": "1.1.0",
        "docs": "/docs",
        "endpoints": [
            "/api/upload",
            "/api/samples",
            "/api/samples/{name}",
            "/api/generate-tests",
            "/api/run-tests",
            "/api/analyze",
            "/api/report/csv",
            "/api/export/pytest"
        ]
    }


# Serve React Single Page Application or JSON based on Accept header
@app.get("/{full_path:path}", tags=["Frontend UI"])
def serve_frontend_or_api(request: Request, full_path: str):
    """
    If accessed by a web browser, serves the interactive React Application.
    If requested as JSON (e.g., API client / curl), returns backend service status.
    """
    index_html = os.path.join(FRONTEND_DIST, "index.html")

    accept = request.headers.get("accept", "")
    if "text/html" in accept and os.path.exists(index_html):
        return FileResponse(index_html)

    if full_path in ("", "api", "health"):
        return health_check()

    if os.path.exists(index_html):
        return FileResponse(index_html)

    return JSONResponse(
        status_code=200,
        content={
            "status": "online",
            "message": "AI-Assisted Software Testing Assistant Backend is running.",
            "frontend_instructions": "To run in development mode, run 'npm run dev' inside the frontend folder, or 'npm run build' to bundle.",
            "docs": "/docs"
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting backend server on {host}:{port}...")
    uvicorn.run("main:app", host=host, port=port, reload=True)
