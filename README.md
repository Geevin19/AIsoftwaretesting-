# AI-Assisted Software Testing Assistant 🧪🤖

An end-to-end, full-stack software engineering micro project designed to automate unit test case generation, test execution in isolated subprocesses, and AI-driven bug root cause analysis and code repair.

---

## 📌 Project Overview

In modern software quality assurance (QA), writing comprehensive unit tests—especially boundary edge-cases and invalid inputs—is time-consuming and often prone to developer blind spots. 

**AI-Assisted Software Testing Assistant** provides:
1. **Multi-File & Project Upload Support**: Upload individual `.py` files, an entire project folder (`webkitdirectory`), or a `.zip` archive. Alternatively, type/paste code directly or choose from pre-configured buggy samples.
2. **Interactive File Tree Explorer**: 240px collapsible sidebar (VS Code / GitHub style) with include/exclude checkboxes, syntax error badges, file counts, and total project size.
3. **AST Syntax Checking**: Instant non-executing AST parse flags files with syntax errors (red indicators with line numbers) and excludes them by default.
4. **AI Unit Test Generation**: Utilizes Google's Gemini LLM to synthesize structured test cases across all included project modules, categorizing them into:
   - **Normal Cases**: Standard expected application flows.
   - **Boundary Cases**: Edge conditions (e.g., zero divisions, min/max limits, empty strings).
   - **Invalid Cases**: Malformed inputs, wrong types, and expected exceptions.
5. **Subprocess Test Execution**: Spawns isolated Python subprocesses with a **strict 5-second timeout** per test inside a temporary project directory, importing the corresponding module and function.
6. **AI Bug Explanation & File-Specific Code Repair**: When a test fails, Gemini diagnoses the root cause, explains the defect, and provides the corrected source code. Clicking "Apply Fix" updates that specific file in memory.
7. **Visual QA Dashboard & Pytest Export**: View real-time pass/fail distribution, category breakdown charts, download filtered CSV reports, or export the complete project with a ready-to-run pytest test suite (`pytest_project_suite.zip`).

> **Note on Architecture:** The application is completely **stateless** with **zero database dependencies**. All session state (files, active file, generated tests, execution results, and bug analyses) is managed on the client side using **React Context** (`AppContext.jsx`).

---

## 🏗️ Architecture Diagram (Text Form)

```
+-----------------------------------------------------------------------------------+
|                                FRONTEND (React + Vite)                            |
|                                                                                   |
|   +------------------------------------+   +-------------------+   +----------+   |
|   | 1. Code Editor & Project Explorer  |   | 2. Test Suite     |   | 3. Sub-  |   |
|   | - FileUploader (Files, Folder, Zip)|-->| - Multi-File Tests|-->|    process|   |
|   | - FileTree (240px VS Code style)   |   |   (Normal, Bound, |   |    Run   |   |
|   | - Monaco Editor (Active file tab)  |   |    Invalid)       |   |    Results|  |
|   +------------------------------------+   +-------------------+   +----------+   |
|                     |                                                    |        |
|                     |                                                    v        |
|                     |      +---------------------+          +-----------------+   |
|                     |      | 5. Reports & Export |          | 4. QA Dashboard |   |
|                     |      | - CSV Download      |<---------| - Pie/Bar Charts|   |
|                     |      | - Pytest Suite Zip  |          | - Metric Cards  |   |
|                     |      +---------------------+          +-----------------+   |
|                     |                                                             |
|                     +-----------------------------------+                         |
|                                                         |                         |
|                             React Context (AppContext.jsx)                        |
|              [In-Memory Session: files, activeFile, tests, results, fixes]        |
+---------------------------------------------------------+-------------------------+
                                                          |
                                               HTTP REST API (JSON / Multipart)
                                                          |
+---------------------------------------------------------v-------------------------+
|                                  BACKEND (FastAPI)                                |
|                                                                                   |
|  [Routers]                                                                        |
|   ├── /api/upload          -> Multi-file, directory, and .zip archive processor   |
|   ├── /api/samples         -> List & load pre-configured buggy samples            |
|   ├── /api/generate-tests  -> AST validation & LLM multi-file test synthesis      |
|   ├── /api/run-tests       -> Multi-file subprocess execution harness (5s timeout)|
|   ├── /api/analyze         -> File-targeted bug diagnosis & code fix              |
|   ├── /api/report/csv      -> CSV report generation with file tracking            |
|   └── /api/export/pytest   -> Downloadable zip containing project + pytest suite  |
|                                                                                   |
|  [Services]                                                                       |
|   ├── llm_client.py        -> Isolated Gemini SDK provider client                 |
|   ├── test_generator.py    -> Multi-file prompt builder & 9-test synthesizer      |
|   ├── test_runner.py       -> Isolated directory harness & module test execution  |
|   └── bug_analyzer.py      -> Targeted file patch & root-cause generator          |
+-------------------------------------+---------------------------------------------+
                                      |
                      +---------------+---------------+
                      |                               |
                      v                               v
          +-----------------------+       +-----------------------+
          |   Google Gemini LLM   |       |  Isolated Subprocess  |
          |  (Official Python SDK)|       |  Execution Harness    |
          +-----------------------+       +-----------------------+
```

---

## 🛠️ Tech Stack

### Frontend
- **Framework:** React 18 with Vite
- **Theme:** Clean, modern Light Theme (neutral borders, compact spacing, no gradients)
- **Code Editor:** `@monaco-editor/react` (VS Code Light mode)
- **Charts & Data Viz:** Recharts (Responsive Pie & Bar charts)
- **Routing:** React Router v6
- **Icons:** `lucide-react`
- **HTTP Client:** Axios
- **State Management:** React Context API (`AppContext.jsx`)

### Backend
- **Language:** Python 3.10+ (compatible with Python 3.9+)
- **Web Framework:** FastAPI (async REST API with automatic OpenAPI docs)
- **Server:** Uvicorn (ASGI server)
- **Validation:** Pydantic v2 schemas
- **Multipart Handling:** `python-multipart`
- **Subprocess Runner:** Python standard library `subprocess`, `tempfile`, `shutil`, `zipfile`, `ast`

---

## 📁 Project Directory Structure

```
ai-test-assistant/
├── backend/
│   ├── main.py                # FastAPI app entry point, CORS, router registrations
│   ├── schemas.py             # Pydantic models (SourceFile, TestCase, UploadResponse)
│   ├── requirements.txt       # Backend dependencies
│   ├── .env.example           # Environment template (GEMINI_API_KEY)
│   ├── routers/
│   │   ├── upload.py          # POST /api/upload (files, folders, .zip archives)
│   │   ├── samples.py         # GET /api/samples and GET /api/samples/{name}
│   │   ├── tests.py           # POST /api/generate-tests and POST /api/run-tests
│   │   ├── analysis.py        # POST /api/analyze (targeted file bug diagnosis)
│   │   └── reports.py         # POST /api/report/csv and POST /api/export/pytest
│   ├── services/
│   │   ├── llm_client.py      # Isolated Gemini SDK client
│   │   ├── prompts.py         # Prompt templates for test gen & bug fixes
│   │   ├── test_generator.py  # AST parser, multi-file prompt builder, test synthesizer
│   │   ├── test_runner.py     # Multi-file subprocess workspace harness (5s timeout)
│   │   └── bug_analyzer.py    # Targeted failure diagnosis and code patch synthesis
│   └── samples/
│       ├── calculator.py      # Arithmetic module with deliberate division-by-zero bug
│       └── login_validator.py # Auth validator with password length boundary bug
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── package.json
│   └── src/
│       ├── main.jsx
│       ├── App.jsx            # Top-level routing & layout
│       ├── index.css          # Tailwind base & light scrollbars
│       ├── api/
│       │   └── client.js      # Axios client with centralized endpoints
│       ├── context/
│       │   └── AppContext.jsx # Global session state (multi-file state)
│       ├── components/
│       │   ├── Navbar.jsx     # Navigation bar with step indicators & badges
│       │   ├── FileUploader.jsx # Drag-and-drop zone with 3 upload buttons
│       │   ├── FileTree.jsx   # 240px VS Code style collapsible file tree
│       │   ├── CodeEditor.jsx # Monaco Editor with active file breadcrumb
│       │   ├── TestTable.jsx  # Interactive tests table with File/Module tracking
│       │   ├── StatusBadge.jsx# Color-coded badges (PASS, FAIL, ERROR, Category)
│       │   ├── FixReview.jsx  # AI explanation & file-specific fix modal
│       │   ├── MetricCard.jsx # Elevated statistical cards
│       │   └── Loader.jsx     # Animated spinner overlay with status updates
│       └── pages/
│           ├── EditorPage.jsx # Step 1: FileTree, FileUploader, Monaco Editor
│           ├── TestsPage.jsx  # Step 2: Multi-file test suite inspection
│           ├── ResultsPage.jsx# Step 3: Subprocess run results & AI Explain CTA
│           ├── DashboardPage.jsx # Step 4: Visual analytics (Pie & Bar charts)
│           └── ReportsPage.jsx# Step 5: Filterable results, CSV & Pytest export
└── README.md
```

---

## 🔒 Security & Upload Validation Rules

- **Zero Upload-Time Execution**: Uploaded files are NEVER executed at upload time; files are purely decoded as UTF-8, parsed via `ast.parse` to check syntax, and stored in browser session state.
- **Python-Only**: Only `.py` files and `.zip` archives are accepted.
- **Ignored Directories**: Files within `.git`, `venv`, `.venv`, `env`, `__pycache__`, `node_modules`, `.idea`, `.vscode`, `dist`, `build`, and `site-packages` are automatically ignored.
- **Upload Constraints**:
  - Max 25 files per project
  - Max 200 KB per file
  - Max 1 MB total uncompressed project size
  - Max 5 MB `.zip` archive limit
  - Max 10 MB total uncompressed zip extraction limit (zip bomb protection)
- **Path Traversal Defense**: Zip entries with absolute paths or `..` path traversal are strictly rejected.
- **Top-Level Prefix Stripping**: If all files in a zip or folder share a single top-level directory (e.g. `my-project-main/`), the common wrapper directory is automatically stripped.

---

## 🚀 Setup & Execution

### 1. Start the Backend
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
> **Backend URL:** `http://127.0.0.1:8000`  
> *(Navigating to `http://127.0.0.1:8000` directly in your browser also serves the interactive React frontend!)*

### 2. Start the Frontend (Optional for Development)
```powershell
cd frontend
npm run dev
```
> **Frontend URL:** `http://localhost:5173`

---

## 📄 License
Developed for educational purposes as an academic Software Engineering Micro Project. MIT License.
