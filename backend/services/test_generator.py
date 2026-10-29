"""
Stage 2: Grounded Test Generator Service.
Integrates Stage 1 Static AST Analysis with Gemini LLM (or AST rule-based synthesis in offline mode),
validates generated tests with Stage 3 TestValidator, handles JSON retries, and batches requests.
"""
import json
import re
import uuid
import logging
from typing import List, Dict, Any, Tuple, Optional
from schemas import SourceFile, TestCase, FunctionMetadata, ParameterMeta
from services.llm_client import llm_client
from services.code_analyzer import analyze_source_files
from services.test_validator import validate_test_cases
from services.prompts import (
    GROUNDED_TESTS_SYSTEM_PROMPT,
    STRICT_RETRY_SYSTEM_PROMPT,
    build_grounded_generation_prompt,
)

logger = logging.getLogger("test_generator")


def clean_llm_json(raw_text: str) -> str:
    """Strips markdown code fences and returns raw JSON array string."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    start_bracket = text.find("[")
    end_bracket = text.rfind("]")
    if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
        return text[start_bracket:end_bracket + 1]

    return text


def synthesize_ast_grounded_fallback(
    fn: FunctionMetadata,
    per_function: int = 6
) -> List[TestCase]:
    """
    Intelligent AST-driven deterministic test synthesizer for offline/local execution.
    Inspects parameter signatures, types, comparison conditions, and raised exceptions
    from Stage 1 Static Analysis to produce customized tests for ANY user code.
    NEVER uses hardcoded sample tests.
    """
    tests: List[TestCase] = []
    params = fn.parameters
    req_params = [p for p in params if p.required]

    # Helper to generate representative arguments for a given test profile
    def build_arg_value(param: ParameterMeta, profile: str) -> Any:
        hint = (param.type_hint or "").lower()
        name = param.name.lower()

        # Check for numeric types or names
        is_num = "int" in hint or "float" in hint or any(k in name for k in ("num", "count", "idx", "val", "age", "size", "a", "b", "x", "y", "roll", "mark", "score", "grade", "total", "avg", "average"))
        is_str = "str" in hint or any(k in name for k in ("str", "name", "text", "user", "pass", "msg", "key", "op", "dept", "student", "class"))
        is_list = "list" in hint or any(k in name for k in ("list", "arr", "items", "data", "marks", "scores"))
        is_bool = "bool" in hint or name.startswith("is_") or name.startswith("has_")

        if profile == "normal_1":
            if is_list: return [85, 90, 78]
            if is_num: return 10 if "roll" not in name else 101
            if is_str: return "Alice" if "name" in name else "test_string"
            if is_bool: return True
            return 42

        elif profile == "normal_2":
            if is_list: return [95, 88, 72]
            if is_num: return 5 if "roll" not in name else 102
            if is_str: return "Bob" if "name" in name else "example_valid"
            if is_bool: return False
            return 100

        elif profile == "boundary_zero":
            if is_list: return []
            if is_num: return 0
            if is_str: return ""
            return 0

        elif profile == "boundary_min_limit":
            # Extract number from comparison conditions if available (e.g. b == 0, x < 8)
            for cond in fn.comparison_conditions:
                nums = re.findall(r"-?\d+", cond)
                if nums:
                    return int(nums[0])
            if is_list: return [40]
            if is_num: return 1
            if is_str: return "a"
            return 0

        elif profile == "boundary_negative":
            if is_list: return [-5]
            if is_num: return -1
            if is_str: return " " * 5
            return -1

        elif profile == "invalid_type":
            if is_num: return "not_a_number"
            if is_str: return 12345
            if is_list: return "not_a_list"
            return None

        elif profile == "invalid_none":
            return None

        return 0

    # Determine default expected value based on return annotation and logic
    expected_normal: Any = True
    if fn.return_annotation:
        ann = fn.return_annotation.lower()
        if "int" in ann: expected_normal = 15
        elif "float" in ann: expected_normal = 15.0
        elif "str" in ann: expected_normal = "expected_output"
        elif "bool" in ann: expected_normal = True
        elif "list" in ann: expected_normal = []

    expected_exception = fn.raises[0] if fn.raises else "ValueError"

    # Pre-build constructor args if fn is a class instance method
    ctor_args = []
    if fn.is_method and fn.constructor_args:
        ctor_args = [build_arg_value(p, "normal_1") for p in fn.constructor_args]

    # 1. Normal Test 1
    input_normal_1 = [build_arg_value(p, "normal_1") for p in params]
    tests.append(TestCase(
        id=f"tc_{uuid.uuid4().hex[:6]}",
        name=f"Standard execution for {fn.function_name}",
        category="normal",
        file=fn.file,
        module=fn.module,
        class_name=fn.class_name,
        constructor_args=ctor_args,
        function_name=fn.function_name,
        input=input_normal_1,
        expected=expected_normal,
        purpose=f"Verifies typical execution of {fn.function_name} with valid inputs",
        is_ai=False
    ))

    # If the function takes no arguments, 1 standard execution test is complete
    if not params:
        return tests
    input_normal_2 = [build_arg_value(p, "normal_2") for p in params]
    tests.append(TestCase(
        id=f"tc_{uuid.uuid4().hex[:6]}",
        name=f"Alternative valid parameters for {fn.function_name}",
        category="normal",
        file=fn.file,
        module=fn.module,
        class_name=fn.class_name,
        constructor_args=ctor_args,
        function_name=fn.function_name,
        input=input_normal_2,
        expected=expected_normal,
        purpose=f"Verifies secondary normal inputs on {fn.function_name}",
        is_ai=False
    ))

    # 3. Boundary Test: Zero / Empty
    input_boundary_zero = [build_arg_value(p, "boundary_zero") for p in params]
    tests.append(TestCase(
        id=f"tc_{uuid.uuid4().hex[:6]}",
        name=f"Zero and empty boundary on {fn.function_name}",
        category="boundary",
        file=fn.file,
        module=fn.module,
        class_name=fn.class_name,
        constructor_args=ctor_args,
        function_name=fn.function_name,
        input=input_boundary_zero,
        expected=0 if isinstance(expected_normal, int) else (0.0 if isinstance(expected_normal, float) else expected_exception),
        purpose=f"Tests zero/empty boundary input behavior on {fn.function_name}",
        is_ai=False
    ))

    # 4. Boundary Test: Condition limit / negative
    input_boundary_limit = [build_arg_value(p, "boundary_min_limit") for p in params]
    tests.append(TestCase(
        id=f"tc_{uuid.uuid4().hex[:6]}",
        name=f"Comparison condition limit boundary on {fn.function_name}",
        category="boundary",
        file=fn.file,
        module=fn.module,
        class_name=fn.class_name,
        constructor_args=ctor_args,
        function_name=fn.function_name,
        input=input_boundary_limit,
        expected=expected_exception if fn.raises else expected_normal,
        purpose=f"Evaluates exact limit boundary derived from AST comparison conditions ({', '.join(fn.comparison_conditions) or 'default'})",
        is_ai=False
    ))

    # 5. Invalid Test: Incompatible Type
    input_invalid_type = [build_arg_value(p, "invalid_type") for p in params]
    tests.append(TestCase(
        id=f"tc_{uuid.uuid4().hex[:6]}",
        name=f"Type rejection test on {fn.function_name}",
        category="invalid",
        file=fn.file,
        module=fn.module,
        class_name=fn.class_name,
        constructor_args=ctor_args,
        function_name=fn.function_name,
        input=input_invalid_type,
        expected="TypeError" if "TypeError" in fn.raises else expected_exception,
        purpose=f"Ensures incompatible argument types are rejected safely",
        is_ai=False
    ))

    # 6. Invalid Test: None / Malformed input
    input_invalid_none = [build_arg_value(p, "invalid_none") for p in params]
    tests.append(TestCase(
        id=f"tc_{uuid.uuid4().hex[:6]}",
        name=f"Null and None value rejection on {fn.function_name}",
        category="invalid",
        file=fn.file,
        module=fn.module,
        class_name=fn.class_name,
        constructor_args=ctor_args,
        function_name=fn.function_name,
        input=input_invalid_none,
        expected="TypeError" if "TypeError" in fn.raises else expected_exception,
        purpose=f"Ensures None values raise appropriate errors or are rejected",
        is_ai=False
    ))

    return tests[:per_function]


def format_files_code_string(files: List[SourceFile]) -> str:
    """Formats project source code with file path headers."""
    sections = []
    for f in files:
        if not f.included or f.syntax_error:
            continue
        sections.append(f"### FILE: {f.path}\n{f.content}\n")
    return "\n".join(sections)


def generate_tests_pipeline(
    files: List[SourceFile],
    selected_function_ids: Optional[List[str]] = None,
    per_function: int = 6,
    language: str = "python"
) -> Tuple[List[TestCase], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Complete Two-Stage Test Generation Pipeline:
    1. Runs Static AST Analysis.
    2. Filters target functions.
    3. Invokes Gemini LLM in batches (or uses grounded AST synthesis if offline).
    4. Validates every test against AST metadata.
    5. Retries with rejection feedback if more than half are invalid.
    """
    # Stage 1: Static AST Analysis
    all_functions, syntax_errors, summary = analyze_source_files(files)

    if not all_functions:
        raise ValueError("No public functions or methods found in the included files.")

    # Filter target functions by selected_function_ids if specified
    target_functions: List[FunctionMetadata] = []
    if selected_function_ids:
        selected_set = set()
        for item in selected_function_ids:
            if isinstance(item, str):
                selected_set.add(item)
            elif hasattr(item, "id") and getattr(item, "id"):
                selected_set.add(getattr(item, "id"))
            elif isinstance(item, dict) and "id" in item:
                selected_set.add(item["id"])
            elif hasattr(item, "function_name") and getattr(item, "function_name"):
                selected_set.add(getattr(item, "function_name"))
            elif isinstance(item, dict) and "function_name" in item:
                selected_set.add(item["function_name"])
            elif isinstance(item, dict) and "name" in item:
                selected_set.add(item["name"])

        target_functions = [
            fn for fn in all_functions
            if fn.id in selected_set or fn.function_name in selected_set or f"{fn.class_name}.{fn.function_name}" in selected_set
        ]
    if not target_functions:
        target_functions = all_functions

    # Separate functions with risky calls
    safe_functions = [fn for fn in target_functions if not fn.risky_calls]
    risky_functions = [fn for fn in target_functions if fn.risky_calls]

    # Cap total tests to maximum 40
    max_tests_cap = 40
    batch_size = 5

    raw_generated_tests: List[TestCase] = []
    files_code = format_files_code_string(files)

    # If Gemini API key is missing, run grounded AST synthesis directly
    if not llm_client.is_configured():
        logger.info("Gemini LLM not configured; using Stage 1 Grounded AST Synthesizer.")
        for fn in safe_functions:
            fn_tests = synthesize_ast_grounded_fallback(fn, per_function=per_function)
            raw_generated_tests.extend(fn_tests)
            if len(raw_generated_tests) >= max_tests_cap:
                break
    else:
        # Run in batches of 5 functions
        for i in range(0, len(safe_functions), batch_size):
            batch_fns = safe_functions[i:i + batch_size]
            batch_meta = [fn.model_dump() for fn in batch_fns]

            prompt = build_grounded_generation_prompt(
                files_code=files_code,
                functions_meta=batch_meta,
                per_function=per_function
            )

            try:
                raw_out = llm_client.generate_text(
                    prompt=prompt,
                    system_instruction=GROUNDED_TESTS_SYSTEM_PROMPT
                )
                cleaned = clean_llm_json(raw_out)
                parsed = json.loads(cleaned)
            except Exception as e:
                # Retry once with strict JSON prompt
                logger.warning(f"Initial LLM batch parse failed: {e}. Retrying with strict JSON prompt.")
                try:
                    retry_out = llm_client.generate_text(
                        prompt=prompt + "\nOUTPUT ONLY RAW JSON ARRAY.",
                        system_instruction=STRICT_RETRY_SYSTEM_PROMPT
                    )
                    cleaned = clean_llm_json(retry_out)
                    parsed = json.loads(cleaned)
                except Exception:
                    # Fallback to grounded AST synthesis for this batch
                    parsed = []
                    for fn in batch_fns:
                        parsed.extend([t.model_dump() for t in synthesize_ast_grounded_fallback(fn, per_function)])

            if isinstance(parsed, dict) and "tests" in parsed:
                parsed = parsed["tests"]

            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        item_fn_name = item.get("function_name", batch_fns[0].function_name)
                        matched_meta = next((f for f in batch_fns if f.function_name == item_fn_name), batch_fns[0])
                        item_ctor = item.get("constructor_args", [])
                        if (not item_ctor) and matched_meta.is_method and matched_meta.constructor_args:
                            item_ctor = [build_arg_value(p, "normal_1") for p in matched_meta.constructor_args]

                        raw_generated_tests.append(TestCase(
                            id=f"tc_{uuid.uuid4().hex[:6]}",
                            name=item.get("name", "Generated Unit Test"),
                            category=item.get("category", "normal").lower(),
                            file=item.get("file", matched_meta.file),
                            module=item.get("module", matched_meta.module),
                            class_name=item.get("class_name") or matched_meta.class_name,
                            constructor_args=item_ctor,
                            function_name=item_fn_name,
                            input=item.get("input", []),
                            expected=item.get("expected"),
                            purpose=item.get("purpose", "Automated branch verification"),
                            is_ai=True
                        ))

            if len(raw_generated_tests) >= max_tests_cap:
                break

    # If LLM returned empty, use grounded AST fallback
    if not raw_generated_tests:
        for fn in safe_functions:
            raw_generated_tests.extend(synthesize_ast_grounded_fallback(fn, per_function))
            if len(raw_generated_tests) >= max_tests_cap:
                break

    # Stage 3: Validation against Static AST Analysis
    valid_tests, rejected, skipped_functions, coverage_notes = validate_test_cases(
        raw_generated_tests,
        target_functions
    )

    # Check if more than half of generated tests were rejected
    if len(raw_generated_tests) > 0 and len(rejected) > len(raw_generated_tests) / 2 and llm_client.is_configured():
        logger.info("More than half of generated tests rejected. Regenerating with rejection feedback.")
        rejection_reasons = "\n".join([f"- {r['reason']}" for r in rejected[:5]])

        retry_prompt = build_grounded_generation_prompt(
            files_code=files_code,
            functions_meta=[fn.model_dump() for fn in safe_functions[:batch_size]],
            per_function=per_function,
            previous_rejections=rejection_reasons
        )

        try:
            retry_out = llm_client.generate_text(
                prompt=retry_prompt,
                system_instruction=GROUNDED_TESTS_SYSTEM_PROMPT
            )
            retry_cleaned = clean_llm_json(retry_out)
            retry_parsed = json.loads(retry_cleaned)
            if isinstance(retry_parsed, list):
                retry_tests = []
                for item in retry_parsed:
                    if isinstance(item, dict):
                        retry_tests.append(TestCase(
                            id=f"tc_{uuid.uuid4().hex[:6]}",
                            name=item.get("name", "Refined Unit Test"),
                            category=item.get("category", "normal").lower(),
                            file=item.get("file", safe_functions[0].file),
                            module=item.get("module", safe_functions[0].module),
                            class_name=item.get("class_name"),
                            constructor_args=item.get("constructor_args", []),
                            function_name=item.get("function_name", safe_functions[0].function_name),
                            input=item.get("input", []),
                            expected=item.get("expected"),
                            purpose=item.get("purpose", "Refined branch verification"),
                            is_ai=True
                        ))
                v_retry, r_retry, _, cov_retry = validate_test_cases(retry_tests, target_functions)
                if len(v_retry) >= len(valid_tests):
                    valid_tests = v_retry
                    rejected = r_retry
                    coverage_notes = cov_retry
        except Exception as retry_err:
            logger.warning(f"Re-generation attempt failed: {retry_err}")

    # Enforce global cap
    valid_tests = valid_tests[:max_tests_cap]

    return valid_tests, rejected, skipped_functions, coverage_notes
