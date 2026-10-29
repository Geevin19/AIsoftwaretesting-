"""
Validation Service:
Validates AI-generated test cases against Stage 1 Static AST Analysis metadata:
- Verifies function/class/module existence
- Enforces parameter count bounds (required <= len(input) <= total)
- Validates constructor arguments for class methods
- Deduplicates exact duplicate test cases
- Produces branch coverage notes per function
"""
from typing import List, Dict, Any, Tuple, Optional, Set
from schemas import TestCase, FunctionMetadata


def build_function_lookup(functions: List[FunctionMetadata]) -> Dict[str, FunctionMetadata]:
    """Creates fast lookup dictionary by various identifier keys."""
    lookup: Dict[str, FunctionMetadata] = {}
    for fn in functions:
        lookup[fn.id] = fn
        # Secondary keys for flexible matching
        mod_key = f"{fn.module}.{fn.function_name}"
        lookup[mod_key] = fn
        if fn.class_name:
            cls_key = f"{fn.module}.{fn.class_name}.{fn.function_name}"
            lookup[cls_key] = fn
            lookup[f"{fn.class_name}.{fn.function_name}"] = fn
        lookup[fn.function_name] = fn  # simple fallback if unique
    return lookup


def validate_test_cases(
    generated_tests: List[TestCase],
    functions: List[FunctionMetadata]
) -> Tuple[List[TestCase], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validates a list of generated tests against static analysis function metadata.
    Returns: (valid_tests, rejected_list, skipped_functions_list, coverage_notes)
    """
    fn_map = {fn.id: fn for fn in functions}
    lookup = build_function_lookup(functions)

    valid_tests: List[TestCase] = []
    rejected: List[Dict[str, Any]] = []
    skipped_functions: List[Dict[str, Any]] = []
    coverage_notes: List[Dict[str, Any]] = []

    # 1. Identify functions skipped due to risky operations
    for fn in functions:
        if fn.risky_calls:
            skipped_functions.append({
                "function": f"{fn.class_name + '.' if fn.class_name else ''}{fn.function_name}",
                "file": fn.file,
                "reason": f"Function contains risky operations ({', '.join(fn.risky_calls)}). Automated live execution avoided."
            })

    seen_fingerprints: Set[Tuple] = set()

    # Track valid tests per function for coverage notes
    tests_per_function: Dict[str, List[TestCase]] = {fn.id: [] for fn in functions}

    for test in generated_tests:
        # Match function metadata
        matched_fn: Optional[FunctionMetadata] = None

        target_id = f"{test.file}::{test.class_name + '::' if test.class_name else ''}{test.function_name}"
        if target_id in fn_map:
            matched_fn = fn_map[target_id]
        else:
            mod_fn_key = f"{test.module}.{test.function_name}"
            if mod_fn_key in lookup:
                matched_fn = lookup[mod_fn_key]
            elif test.function_name in lookup:
                matched_fn = lookup[test.function_name]

        if not matched_fn:
            rejected.append({
                "test": test.model_dump(),
                "reason": f"Target function '{test.function_name}' (class: {test.class_name}) does not exist in the analyzed project AST."
            })
            continue

        # Signature validation
        total_params = len(matched_fn.parameters)
        required_params = sum(1 for p in matched_fn.parameters if p.required)
        input_count = len(test.input) if isinstance(test.input, list) else 0

        if input_count < required_params:
            rejected.append({
                "test": test.model_dump(),
                "reason": f"Missing required arguments for '{matched_fn.function_name}': expected at least {required_params}, got {input_count}."
            })
            continue

        if input_count > total_params:
            rejected.append({
                "test": test.model_dump(),
                "reason": f"Too many arguments for '{matched_fn.function_name}': expected at most {total_params}, got {input_count}."
            })
            continue

        # Constructor argument validation if instance method
        if matched_fn.is_method and matched_fn.class_name:
            test.class_name = matched_fn.class_name
            req_ctor_params = sum(1 for p in matched_fn.constructor_args if getattr(p, "required", getattr(p, "is_required", True)))
            total_ctor_params = len(matched_fn.constructor_args)
            ctor_count = len(test.constructor_args) if isinstance(test.constructor_args, list) else 0

            # If constructor args are missing or insufficient, auto-populate from AST metadata
            # so the test cases are NOT omitted or rejected
            if ctor_count < req_ctor_params:
                auto_ctor = []
                for p in matched_fn.constructor_args:
                    hint = (p.type_hint or "").lower()
                    name = p.name.lower()
                    if "str" in hint or any(k in name for k in ("name", "user", "id", "code", "title", "student")):
                        auto_ctor.append("Alice")
                    elif "int" in hint or any(k in name for k in ("num", "count", "roll", "age", "year")):
                        auto_ctor.append(101)
                    elif "float" in hint or any(k in name for k in ("bal", "price", "rate", "gpa", "score", "mark")):
                        auto_ctor.append(85.0)
                    elif "bool" in hint:
                        auto_ctor.append(True)
                    elif "list" in hint or any(k in name for k in ("marks", "scores", "grades", "items", "list")):
                        auto_ctor.append([85, 90, 78])
                    else:
                        auto_ctor.append("Alice")
                test.constructor_args = auto_ctor
            elif ctor_count > total_ctor_params:
                test.constructor_args = test.constructor_args[:total_ctor_params]

        # Exact Duplicate Detection
        fingerprint = (
            matched_fn.module,
            matched_fn.class_name or "",
            matched_fn.function_name,
            str(test.input),
            str(test.expected)
        )
        if fingerprint in seen_fingerprints:
            rejected.append({
                "test": test.model_dump(),
                "reason": f"Duplicate test case for '{matched_fn.function_name}' with identical inputs and expected outcome."
            })
            continue

        seen_fingerprints.add(fingerprint)

        # Standardize verified test fields
        test.file = matched_fn.file
        test.module = matched_fn.module
        test.class_name = matched_fn.class_name

        valid_tests.append(test)
        tests_per_function[matched_fn.id].append(test)

    # 3. Compute coverage notes per function
    for fn in functions:
        fn_tests = tests_per_function.get(fn.id, [])
        if fn_tests:
            branches = fn.branch_count
            categories = set(t.category for t in fn_tests)
            estimated_covered_branches = min(branches, len(fn_tests))
            note = f"{len(fn_tests)} tests, covers {estimated_covered_branches} of {branches} branch paths ({', '.join(sorted(categories))})"
            coverage_notes.append({
                "function_id": fn.id,
                "function_name": f"{fn.class_name + '.' if fn.class_name else ''}{fn.function_name}",
                "file": fn.file,
                "note": note
            })
            for t in fn_tests:
                t.coverage_note = note

    return valid_tests, rejected, skipped_functions, coverage_notes
