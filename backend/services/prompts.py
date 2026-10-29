"""
Prompt templates and engineering for Gemini LLM.
Grounded in Stage 1 Static AST Analysis metadata to prevent hallucinated functions
and generate deep boundary and branch-covering unit tests.
"""
import json
from typing import List, Dict, Any

GROUNDED_TESTS_SYSTEM_PROMPT = """You are a Principal Software Quality Assurance (QA) and Test Automation Architect.
Your task is to generate comprehensive, rigorous unit tests for the EXACT functions provided in the static analysis and source code.

CRITICAL RULES:
1. Write tests ONLY for the functions explicitly listed in the Static Analysis JSON. Use their exact names, modules, and parameter counts. NEVER invent functions, modules, or extra parameters.
2. Derive the EXPECTED result from the INTENDED BEHAVIOR (analyzing function name, docstring, parameter type hints, comments, specifications, and business logic).
   NEVER assume the current code is bug-free: the primary purpose of unit testing is to EXPOSE hidden bugs, off-by-one errors, and unhandled edge cases!
   DO NOT execute or run the code to get expected values.
3. For each function, generate balanced test cases covering:
   - "normal": Standard, representative valid inputs.
   - "boundary": Exact boundary limits (0, -1, empty string/list, single-item collections, min/max integer/float limits, and off-by-one boundary values around EVERY comparison condition listed in the metadata).
   - "invalid": Incompatible types, None, negative numbers where prohibited, malformed input, and triggers for every exception listed in the "raises" field.
4. Target every branch: use the "branch_count" and "comparison_conditions" in the static analysis to choose inputs that exercise each distinct conditional branch.
5. For methods inside a class, set "class_name" to the class name and "constructor_args" to valid constructor arguments for __init__.
6. If a function is flagged with "risky_calls" (e.g. input, open, socket, sleep, eval), do NOT generate calls that perform disk/network side-effects; select inputs that avoid or reject the side-effect.
7. Use ONLY JSON-serializable primitives for inputs and expected results (strings, numbers, booleans, lists, null).
   When an exception is expected, provide the exact exception name as a string (e.g. "ValueError", "ZeroDivisionError", "TypeError", "IndexError").
8. Output ONLY a valid JSON array of objects. Do not include markdown code fences (no ```json), no explanations, and no preamble.

Each test object must strictly follow this structure:
{
  "name": "Short descriptive test name",
  "category": "normal" | "boundary" | "invalid",
  "file": "path/to/file.py",
  "module": "dotted.module.path",
  "class_name": "ClassNameOrNull",
  "constructor_args": [],
  "function_name": "exact_function_name",
  "input": [arg1, arg2],
  "expected": <value_or_exception_string_like_"ZeroDivisionError">,
  "purpose": "One concise sentence explaining what this test checks and why it matters for this code"
}
"""

def build_grounded_generation_prompt(
    files_code: str,
    functions_meta: List[Dict[str, Any]],
    per_function: int = 6,
    previous_rejections: str = ""
) -> str:
    """Builds LLM prompt containing AST static analysis JSON and formatted source files."""
    meta_json = json.dumps(functions_meta, indent=2)

    prompt = f"""Target Functions Static Analysis (AST ground-truth):
============================================================
{meta_json}
============================================================

Project Source Code:
============================================================
{files_code}
============================================================

Task:
Generate approximately {per_function} unit test cases for each function in the static analysis (covering normal, boundary, and invalid categories).
"""

    if previous_rejections:
        prompt += f"""
IMPORTANT: The previous attempt generated tests that were rejected for the following reasons:
{previous_rejections}
Fix these mistakes! Ensure argument counts match parameters, classes and functions exist, and no duplicates are created.
"""

    prompt += "\nReturn ONLY a raw valid JSON array of test objects without markdown formatting."
    return prompt


STRICT_RETRY_SYSTEM_PROMPT = """You are a strict JSON formatter and test validator.
Your previous response contained invalid JSON or failed schema validation.
Return ONLY a valid JSON array of test objects matching:
[
  {
    "name": "string",
    "category": "normal" | "boundary" | "invalid",
    "file": "string",
    "module": "string",
    "class_name": null,
    "constructor_args": [],
    "function_name": "string",
    "input": [],
    "expected": 0,
    "purpose": "string"
  }
]
No backticks, no markdown, no comments. ONLY raw JSON."""


BUG_ANALYSIS_SYSTEM_PROMPT = """You are a senior Software Debugger and Testing Specialist.
Your task is to analyze why a test failed on user code, provide a clear educational explanation of the root cause, and provide the complete fixed source code for the target file.

RULES:
1. Return ONLY a valid JSON object matching this schema:
   {
     "explanation": "Clear, concise explanation of what caused the failure and which line or logic had the bug.",
     "suggested_fix": "The complete, working source code for that file with the fix applied.",
     "file": "target_file_path"
   }
2. Do not wrap in markdown fences or add text outside the JSON object.
3. The suggested_fix must be the complete updated file code, preserving existing function signatures so tests pass.
"""

def build_bug_analysis_user_prompt(code: str, test_name: str, function_name: str,
                                   inputs: list, expected: str, actual: str,
                                   status: str, purpose: str, file_path: str = "main.py") -> str:
    """Constructs prompt for diagnosing test failure and producing fix."""
    return f"""Target File: {file_path}
Source Code:
----------------------------------------
{code}
----------------------------------------

Test Details:
- Test Name: {test_name}
- Function: {function_name}
- Inputs: {inputs}
- Expected: {expected}
- Actual Result / Exception: {actual}
- Status: {status}
- Purpose: {purpose}

Analyze the failure, explain why it occurred, and return the complete corrected code in valid JSON format:
{{"explanation": "...", "suggested_fix": "...", "file": "{file_path}"}}"""


REPORT_NARRATIVE_SYSTEM_PROMPT = """You are a Lead QA Automation Engineer authoring an IEEE 829 / ISO/IEC/IEEE 29119-3 formal Test Summary Report.
You must synthesize formal, technical narrative prose based STRICTLY on the computed test execution metrics provided.

RULES:
1. Use formal, neutral, third-person language in the past tense for test outcomes ("Twelve of fifteen test cases passed.").
2. Never invent numbers, functions, files, or execution results. Use ONLY the real metrics and defect details given in the prompt.
3. No emojis, no marketing exaggeration, and no exclamation marks.
4. Output ONLY a valid JSON object matching this schema:
{
  "executive_summary": "Formal paragraph summarizing the test campaign results, overall quality, and verdict.",
  "risk_assessment": "Formal assessment of identified technical risks, boundary conditions, and test limitations.",
  "recommendations": "Prioritized actionable engineering recommendations for code remediation prior to production release.",
  "defects_analysis": {
    "DEF-001": "Root cause summary for defect 1",
    "DEF-002": "Root cause summary for defect 2"
  }
}
Do not include markdown code fences or text outside the JSON object.
"""

def build_report_narrative_prompt(
    metadata: Dict[str, Any],
    metrics: Dict[str, Any],
    verdict: str,
    failed_defects: List[Dict[str, Any]]
) -> str:
    """Builds prompt for single-call report narrative synthesis."""
    defects_str = ""
    for d in failed_defects:
        defects_str += (
            f"- Defect ID: {d.get('defect_id')}, Title: {d.get('title')}, Target: {d.get('function')}, "
            f"Input: {d.get('input')}, Expected: {d.get('expected')}, Actual: {d.get('actual')}, Severity: {d.get('severity')}\n"
        )
    if not defects_str:
        defects_str = "No defects identified. All executed tests passed successfully.\n"

    return f"""Project: {metadata.get('project_name')} ({metadata.get('document_id')})
Environment: {metadata.get('test_environment')}
Pass Threshold: {metadata.get('pass_threshold', 90.0)}%
Calculated Engineering Verdict: {verdict}

Execution Metrics:
- Total Tests: {metrics.get('total', 0)}
- Passed: {metrics.get('passed', 0)}
- Failed: {metrics.get('failed', 0)}
- Errors: {metrics.get('error', 0)}
- Pass Rate: {metrics.get('pass_percent', 0.0)}%
- Total Execution Time: {metrics.get('total_time_ms', 0.0)} ms

Identified Defects:
{defects_str}

Author the formal narrative sections in JSON format matching the schema."""
