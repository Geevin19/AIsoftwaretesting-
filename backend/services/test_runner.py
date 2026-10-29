"""
Automated Test Runner Service.
Executes unit tests against single-file and multi-file projects in an isolated
temporary workspace using subprocesses with a 5-second timeout.
Supports top-level functions as well as instantiated class methods.

NOTE FOR PRODUCTION DEPLOYMENT:
In a production cloud environment, user-submitted code must never run directly on the host.
It must be executed inside a sandboxed microVM (e.g., Firecracker), a container runtime
with secure isolation (e.g., gVisor, Docker with seccomp/apparmor profiles, CPU/memory limits,
and disabled network access), or an ephemeral AWS Lambda / Google Cloud Run sandbox.
"""
import sys
import os
import json
import time
import uuid
import shutil
import tempfile
import subprocess
from typing import List, Dict, Any, Tuple
from schemas import TestCase, TestResultItem, TestRunMetrics, RunTestsResponse, SourceFile

HARNESS_TEMPLATE = """
import sys
import json
import time
import importlib
import traceback

def run_harness():
    module_name = {module_name_repr}
    class_name = {class_name_repr}
    ctor_args = {ctor_args_repr}
    func_name = {func_name_repr}
    args = {args_repr}
    expected = {expected_repr}

    result_payload = {{
        "success": False,
        "actual": None,
        "is_exception": False,
        "exception_type": None,
        "error_msg": None,
        "elapsed_ms": 0.0
    }}

    # 1. Dynamic module import from project directory
    try:
        mod = importlib.import_module(module_name)
    except Exception as imp_exc:
        result_payload["is_exception"] = True
        result_payload["exception_type"] = type(imp_exc).__name__
        result_payload["error_msg"] = f"Failed to import module '{{module_name}}': {{str(imp_exc)}}"
        print(json.dumps(result_payload))
        return

    # 2. Lookup target function or class method
    try:
        if class_name:
            cls_obj = getattr(mod, class_name, None)
            if not cls_obj or not callable(cls_obj):
                result_payload["is_exception"] = True
                result_payload["exception_type"] = "AttributeError"
                result_payload["error_msg"] = f"Class '{{class_name}}' not found or not callable in module '{{module_name}}'"
                print(json.dumps(result_payload))
                return
            
            # Construct class instance
            instance = cls_obj(*ctor_args)
            target_func = getattr(instance, func_name, None)
        else:
            target_func = getattr(mod, func_name, None)

        if not target_func or not callable(target_func):
            result_payload["is_exception"] = True
            result_payload["exception_type"] = "AttributeError"
            result_payload["error_msg"] = f"Function '{{func_name}}' not found or not callable in module '{{module_name}}'"
            print(json.dumps(result_payload))
            return
    except Exception as lookup_exc:
        result_payload["is_exception"] = True
        result_payload["exception_type"] = type(lookup_exc).__name__
        result_payload["error_msg"] = f"Initialization error: {{str(lookup_exc)}}"
        print(json.dumps(result_payload))
        return

    # 3. Time and execute target callable
    start_time = time.perf_counter()
    try:
        val = target_func(*args)
        elapsed = (time.perf_counter() - start_time) * 1000.0
        result_payload["success"] = True
        result_payload["actual"] = val
        result_payload["elapsed_ms"] = round(elapsed, 2)
    except Exception as exc:
        elapsed = (time.perf_counter() - start_time) * 1000.0
        result_payload["is_exception"] = True
        result_payload["exception_type"] = type(exc).__name__
        result_payload["error_msg"] = str(exc)
        result_payload["actual"] = f"{{type(exc).__name__}}: {{str(exc)}}"
        result_payload["elapsed_ms"] = round(elapsed, 2)

    # 4. Serialize output to stdout
    try:
        print(json.dumps(result_payload))
    except (TypeError, ValueError):
        result_payload["actual"] = str(result_payload["actual"])
        print(json.dumps(result_payload))

if __name__ == '__main__':
    run_harness()
"""


def compare_results(expected: Any, harness_output: Dict[str, Any]) -> Tuple[str, Any, str]:
    """
    Compares test harness execution output with expected result.
    Returns: (status: PASS|FAIL|ERROR, actual_val, error_message)
    """
    is_exc = harness_output.get("is_exception", False)
    exc_type = harness_output.get("exception_type")
    actual_val = harness_output.get("actual")
    error_msg = harness_output.get("error_msg")

    known_exceptions = {
        "ZeroDivisionError", "ValueError", "TypeError", "IndexError",
        "KeyError", "AttributeError", "Exception", "AssertionError",
        "FileNotFoundError", "PermissionError", "RuntimeError", "StopIteration"
    }

    expected_is_exception = (
        isinstance(expected, str) and
        (expected in known_exceptions or expected.endswith("Error") or expected.endswith("Exception"))
    )

    if expected_is_exception:
        if is_exc:
            if exc_type == expected or expected == "Exception":
                return "PASS", exc_type, ""
            else:
                return "FAIL", exc_type, f"Expected exception {expected}, but received {exc_type}: {error_msg}"
        else:
            return "FAIL", actual_val, f"Expected exception {expected}, but function returned normally with value: {actual_val}"

    if is_exc:
        return "FAIL", f"{exc_type}: {error_msg}", f"Unexpected exception raised: {exc_type}"

    try:
        if isinstance(expected, bool) or isinstance(actual_val, bool):
            if expected is actual_val:
                return "PASS", actual_val, ""
            else:
                return "FAIL", actual_val, f"Expected {expected} ({type(expected).__name__}), got {actual_val} ({type(actual_val).__name__})"

        if isinstance(expected, (int, float)) and isinstance(actual_val, (int, float)):
            if abs(float(expected) - float(actual_val)) < 1e-6:
                return "PASS", actual_val, ""
            else:
                return "FAIL", actual_val, f"Expected {expected}, got {actual_val}"

        if expected == actual_val:
            return "PASS", actual_val, ""
        else:
            return "FAIL", actual_val, f"Expected {expected!r}, got {actual_val!r}"
    except Exception as comp_err:
        return "ERROR", str(actual_val), f"Comparison error: {comp_err}"


def write_project_to_temp_dir(files: List[SourceFile], temp_dir: str):
    """
    Writes all project source files into temp_dir, creating subdirectories
    and ensuring __init__.py files are present for package imports.
    """
    for sfile in files:
        rel_path = sfile.path.replace("\\", "/").strip().lstrip("/")
        abs_dest = os.path.join(temp_dir, rel_path)
        os.makedirs(os.path.dirname(abs_dest), exist_ok=True)
        with open(abs_dest, "w", encoding="utf-8") as f:
            f.write(sfile.content)

    # Ensure __init__.py exists in every directory containing python files
    for root, dirs, _ in os.walk(temp_dir):
        if root != temp_dir:
            init_file = os.path.join(root, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, "w", encoding="utf-8") as f:
                    f.write("# Package marker\n")


def run_single_test_in_workspace(test: TestCase, temp_dir: str, timeout_sec: float = 5.0) -> TestResultItem:
    """Runs a single test inside the temporary workspace directory."""
    harness_code = HARNESS_TEMPLATE.format(
        module_name_repr=repr(test.module or "main"),
        class_name_repr=repr(test.class_name),
        ctor_args_repr=repr(test.constructor_args or []),
        func_name_repr=repr(test.function_name),
        args_repr=repr(test.input),
        expected_repr=repr(test.expected)
    )

    harness_path = os.path.join(temp_dir, f"_harness_{uuid.uuid4().hex[:6]}.py")
    with open(harness_path, "w", encoding="utf-8") as hf:
        hf.write(harness_code)

    py_exec = sys.executable
    start_perf = time.perf_counter()

    try:
        process = subprocess.run(
            [py_exec, harness_path],
            cwd=temp_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_sec
        )
        total_time_ms = round((time.perf_counter() - start_perf) * 1000.0, 2)

        if process.returncode != 0:
            stderr_out = process.stderr.strip() or "Process exited with non-zero status"
            return TestResultItem(
                id=test.id or "unknown",
                name=test.name,
                category=test.category,
                file=test.file,
                module=test.module,
                class_name=test.class_name,
                constructor_args=test.constructor_args,
                function_name=test.function_name,
                input=test.input,
                expected=test.expected,
                actual="Execution Error",
                status="ERROR",
                execution_time_ms=total_time_ms,
                error_message=stderr_out.splitlines()[-1] if stderr_out else "Execution failed",
                purpose=test.purpose,
                is_ai=test.is_ai
            )

        stdout_clean = process.stdout.strip()
        last_line = stdout_clean.splitlines()[-1] if stdout_clean else "{}"
        payload = json.loads(last_line)

        status, actual_val, err_msg = compare_results(test.expected, payload)
        exec_ms = payload.get("elapsed_ms", total_time_ms)

        return TestResultItem(
            id=test.id or "unknown",
            name=test.name,
            category=test.category,
            file=test.file,
            module=test.module,
            class_name=test.class_name,
            constructor_args=test.constructor_args,
            function_name=test.function_name,
            input=test.input,
            expected=test.expected,
            actual=actual_val,
            status=status,
            execution_time_ms=exec_ms,
            error_message=err_msg or None,
            purpose=test.purpose,
            is_ai=test.is_ai
        )

    except subprocess.TimeoutExpired:
        total_time_ms = round((time.perf_counter() - start_perf) * 1000.0, 2)
        return TestResultItem(
            id=test.id or "unknown",
            name=test.name,
            category=test.category,
            file=test.file,
            module=test.module,
            class_name=test.class_name,
            constructor_args=test.constructor_args,
            function_name=test.function_name,
            input=test.input,
            expected=test.expected,
            actual="Timeout",
            status="ERROR",
            execution_time_ms=total_time_ms,
            error_message=f"Test execution exceeded maximum timeout of {timeout_sec} seconds (possible infinite loop)",
            purpose=test.purpose,
            is_ai=test.is_ai
        )
    except Exception as exc:
        total_time_ms = round((time.perf_counter() - start_perf) * 1000.0, 2)
        return TestResultItem(
            id=test.id or "unknown",
            name=test.name,
            category=test.category,
            file=test.file,
            module=test.module,
            class_name=test.class_name,
            constructor_args=test.constructor_args,
            function_name=test.function_name,
            input=test.input,
            expected=test.expected,
            actual="Runtime Error",
            status="ERROR",
            execution_time_ms=total_time_ms,
            error_message=str(exc),
            purpose=test.purpose,
            is_ai=test.is_ai
        )
    finally:
        try:
            if os.path.exists(harness_path):
                os.remove(harness_path)
        except OSError:
            pass


def execute_test_suite_multi(files: List[SourceFile], tests: List[TestCase]) -> RunTestsResponse:
    """
    Creates an isolated temporary directory, writes all project files, executes
    all tests with a 5-second timeout, and aggregates statistics.
    """
    temp_dir = tempfile.mkdtemp(prefix="ai_test_runner_")
    try:
        write_project_to_temp_dir(files, temp_dir)
        results: List[TestResultItem] = []

        for test in tests:
            res = run_single_test_in_workspace(test, temp_dir, timeout_sec=5.0)
            results.append(res)

        total = len(results)
        passed = sum(1 for r in results if r.status == "PASS")
        failed = sum(1 for r in results if r.status == "FAIL")
        error = sum(1 for r in results if r.status == "ERROR")
        pass_percent = round((passed / total * 100.0), 1) if total > 0 else 0.0
        total_time = round(sum(r.execution_time_ms for r in results), 2)

        metrics = TestRunMetrics(
            total=total,
            passed=passed,
            failed=failed,
            error=error,
            pass_percent=pass_percent,
            total_time_ms=total_time
        )

        return RunTestsResponse(results=results, metrics=metrics)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
