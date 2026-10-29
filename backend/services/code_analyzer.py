"""
Stage 1: Static AST Code Analyzer (No AI).
Parses user Python files using the standard library ast module to extract
structural metadata for every public function, class, and method:
- Module and file paths
- Parameter signatures with type hints and defaults
- Constructor arguments for class methods
- Return annotations and docstrings
- Exceptions explicitly raised (ast.Raise)
- Decision branches count (if, for, while, try, boolean ops)
- Comparison conditions in source code (ast.Compare)
- Risky operation detection (e.g. open, eval, exec, network, sleep)
"""
import ast
import os
from typing import List, Dict, Any, Optional, Tuple, Set
from schemas import SourceFile, FunctionMetadata, ParameterMeta, SyntaxErrorItem, AnalysisSummary

# Risky functions / methods that should not execute directly in automated testing
RISKY_NAMES = {
    "input", "open", "eval", "exec", "system", "popen",
    "remove", "unlink", "rmdir", "rmtree",
    "socket", "connect", "urlopen", "get", "post", "put", "delete",
    "sleep"
}

RISKY_MODULES = {"os", "sys", "subprocess", "shutil", "requests", "urllib", "socket", "http", "time"}


def file_path_to_module(path: str) -> str:
    """Converts relative path 'pkg/sub/mod.py' to dotted module 'pkg.sub.mod'."""
    clean = path.replace("\\", "/").strip().lstrip("/")
    if clean.endswith(".py"):
        clean = clean[:-3]
    parts = [p for p in clean.split("/") if p and p != "."]
    return ".".join(parts) if parts else "main"


def safe_unparse(node: Optional[ast.AST]) -> Optional[str]:
    """Converts an AST node to source string safely."""
    if node is None:
        return None
    try:
        return ast.unparse(node).strip()
    except Exception:
        return None


def extract_parameters(args_node: ast.arguments, is_method: bool = False) -> List[ParameterMeta]:
    """Extracts typed parameter metadata from function arguments AST."""
    parameters: List[ParameterMeta] = []
    
    # Calculate offset for default values
    # In Python AST, defaults corresponds to the last len(defaults) positional args
    pos_args = args_node.args
    defaults = args_node.defaults
    defaults_offset = len(pos_args) - len(defaults)

    for i, arg in enumerate(pos_args):
        # Skip self / cls for methods
        if is_method and i == 0 and arg.arg in ("self", "cls"):
            continue

        param_name = arg.arg
        type_hint = safe_unparse(arg.annotation)

        default_val = None
        is_required = True
        default_index = i - defaults_offset
        if default_index >= 0 and default_index < len(defaults):
            default_val = safe_unparse(defaults[default_index])
            is_required = False

        parameters.append(ParameterMeta(
            name=param_name,
            type_hint=type_hint,
            default=default_val,
            required=is_required
        ))

    # Keyword-only arguments
    kw_defaults = args_node.kw_defaults
    for arg, def_node in zip(args_node.kwonlyargs, kw_defaults):
        type_hint = safe_unparse(arg.annotation)
        default_val = safe_unparse(def_node)
        parameters.append(ParameterMeta(
            name=arg.arg,
            type_hint=type_hint,
            default=default_val,
            required=(default_val is None)
        ))

    return parameters


def analyze_function_body(fn_node: ast.AST) -> Tuple[List[str], int, List[str], List[str]]:
    """
    Analyzes body of a function node:
    Returns (raises, branch_count, comparison_conditions, risky_calls)
    """
    raises: List[str] = []
    branch_count = 1  # Base sequential path
    comparisons: List[str] = []
    risky_calls: List[str] = []

    for node in ast.walk(fn_node):
        # 1. Detected raised exceptions
        if isinstance(node, ast.Raise):
            if node.exc:
                if isinstance(node.exc, ast.Name):
                    if node.exc.id not in raises:
                        raises.append(node.exc.id)
                elif isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                    if node.exc.func.id not in raises:
                        raises.append(node.exc.func.id)
                elif isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Attribute):
                    if node.exc.func.attr not in raises:
                        raises.append(node.exc.func.attr)

        # 2. Decision branches (Cyclomatic Complexity)
        if isinstance(node, ast.If):
            branch_count += 1
            if node.orelse:
                branch_count += 1
        elif isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            branch_count += 1
        elif isinstance(node, ast.Try):
            branch_count += len(node.handlers)
        elif isinstance(node, ast.IfExp):  # ternary a if cond else b
            branch_count += 1
        elif isinstance(node, ast.BoolOp):  # a and b, a or b
            branch_count += max(1, len(node.values) - 1)

        # 3. Comparisons in conditions
        if isinstance(node, ast.Compare):
            cmp_str = safe_unparse(node)
            if cmp_str and cmp_str not in comparisons:
                comparisons.append(cmp_str)

        # 4. Detect risky calls
        if isinstance(node, ast.Call):
            call_name = ""
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
                # Check module attribute e.g. os.system, time.sleep
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id in RISKY_MODULES and call_name in RISKY_NAMES:
                        risky_calls.append(f"{node.func.value.id}.{call_name}")
                        continue

            if call_name in RISKY_NAMES and call_name not in risky_calls:
                risky_calls.append(call_name)

    return raises, branch_count, comparisons, list(set(risky_calls))


def analyze_source_files(files: List[SourceFile]) -> Tuple[List[FunctionMetadata], List[SyntaxErrorItem], AnalysisSummary]:
    """
    Scans and analyzes all included source files:
    Extracts complete function and method metadata for public APIs.
    """
    functions: List[FunctionMetadata] = []
    syntax_errors: List[SyntaxErrorItem] = []
    total_classes = 0

    for sfile in files:
        if not sfile.included:
            continue

        file_path = sfile.path.replace("\\", "/").strip().lstrip("/")
        module_path = file_path_to_module(file_path)

        try:
            tree = ast.parse(sfile.content, filename=file_path)
        except SyntaxError as syn_err:
            line_no = syn_err.lineno or 1
            msg = syn_err.msg or "Syntax error"
            syntax_errors.append(SyntaxErrorItem(
                file=file_path,
                line=line_no,
                message=msg
            ))
            continue

        # Top-level functions & class methods
        for item in tree.body:
            # 1. Top-level functions
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn_name = item.name
                if fn_name.startswith("_"):
                    continue

                params = extract_parameters(item.args, is_method=False)
                ret_ann = safe_unparse(item.returns)
                docstring = ast.get_docstring(item)
                raises, branches, comparisons, risky = analyze_function_body(item)

                fn_id = f"{file_path}::{fn_name}"
                functions.append(FunctionMetadata(
                    id=fn_id,
                    file=file_path,
                    module=module_path,
                    class_name=None,
                    function_name=fn_name,
                    is_method=False,
                    is_async=isinstance(item, ast.AsyncFunctionDef),
                    parameters=params,
                    constructor_args=[],
                    return_annotation=ret_ann,
                    docstring=docstring,
                    raises=raises,
                    branch_count=branches,
                    comparison_conditions=comparisons,
                    risky_calls=risky
                ))

            # 2. Classes and their methods
            elif isinstance(item, ast.ClassDef):
                cls_name = item.name
                if cls_name.startswith("_"):
                    continue

                total_classes += 1

                # Extract __init__ constructor arguments if present
                constructor_args: List[ParameterMeta] = []
                for class_child in item.body:
                    if isinstance(class_child, (ast.FunctionDef, ast.AsyncFunctionDef)) and class_child.name == "__init__":
                        constructor_args = extract_parameters(class_child.args, is_method=True)
                        break

                # Extract public methods
                for class_child in item.body:
                    if isinstance(class_child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_name = class_child.name
                        if method_name.startswith("_"):
                            continue

                        params = extract_parameters(class_child.args, is_method=True)
                        ret_ann = safe_unparse(class_child.returns)
                        docstring = ast.get_docstring(class_child)
                        raises, branches, comparisons, risky = analyze_function_body(class_child)

                        fn_id = f"{file_path}::{cls_name}::{method_name}"
                        functions.append(FunctionMetadata(
                            id=fn_id,
                            file=file_path,
                            module=module_path,
                            class_name=cls_name,
                            function_name=method_name,
                            is_method=True,
                            is_async=isinstance(class_child, ast.AsyncFunctionDef),
                            parameters=params,
                            constructor_args=constructor_args,
                            return_annotation=ret_ann,
                            docstring=docstring,
                            raises=raises,
                            branch_count=branches,
                            comparison_conditions=comparisons,
                            risky_calls=risky
                        ))

    risky_count = sum(1 for f in functions if f.risky_calls)

    summary = AnalysisSummary(
        total_files=len(files),
        total_functions=len(functions),
        total_classes=total_classes,
        risky_functions_count=risky_count
    )

    return functions, syntax_errors, summary
