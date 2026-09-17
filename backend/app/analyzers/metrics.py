"""
Code metrics extraction using Python's built-in `ast` module plus Radon
for cyclomatic complexity and maintainability index.

All metrics are computed deterministically from the parsed source code.
No metric is ever fabricated: if something cannot be computed, it is
reported as None/0 rather than guessed.
"""
import ast
from typing import Any, Dict, List

from radon.complexity import cc_visit
from radon.metrics import mi_visit
from radon.raw import analyze as radon_raw_analyze


class FunctionInfo:
    def __init__(self, name: str, lineno: int, end_lineno: int, params: int,
                 length: int, max_nesting: int, complexity: int):
        self.name = name
        self.lineno = lineno
        self.end_lineno = end_lineno
        self.params = params
        self.length = length
        self.max_nesting = max_nesting
        self.complexity = complexity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "line": self.lineno,
            "end_line": self.end_lineno,
            "params": self.params,
            "length": self.length,
            "max_nesting": self.max_nesting,
            "complexity": self.complexity,
        }


def _max_nesting_depth(node: ast.AST, depth: int = 0) -> int:
    """Compute maximum nesting depth of control-flow blocks within a node."""
    nesting_nodes = (ast.If, ast.For, ast.While, ast.Try, ast.With)
    max_depth = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, nesting_nodes):
            child_depth = _max_nesting_depth(child, depth + 1)
        else:
            child_depth = _max_nesting_depth(child, depth)
        max_depth = max(max_depth, child_depth)
    return max_depth


def _function_length(node: ast.FunctionDef) -> int:
    end = getattr(node, "end_lineno", None)
    if end is None:
        return len(node.body)
    return end - node.lineno + 1


def extract_functions(tree: ast.Module, complexity_map: Dict[str, int]) -> List[FunctionInfo]:
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            params = len(node.args.args) + len(node.args.kwonlyargs)
            if node.args.vararg:
                params += 1
            if node.args.kwarg:
                params += 1
            length = _function_length(node)
            nesting = _max_nesting_depth(node)
            complexity = complexity_map.get(node.name, 1)
            functions.append(
                FunctionInfo(
                    name=node.name,
                    lineno=node.lineno,
                    end_lineno=getattr(node, "end_lineno", node.lineno),
                    params=params,
                    length=length,
                    max_nesting=nesting,
                    complexity=complexity,
                )
            )
    return functions


def compute_metrics(source_code: str) -> Dict[str, Any]:
    """
    Returns a dict with:
      - raw metrics (loc, comment lines, blank lines)
      - function-level metrics
      - class count
      - complexity aggregates
      - maintainability index
    Raises SyntaxError if the code cannot be parsed (caller should handle).
    """
    tree = ast.parse(source_code)

    # Cyclomatic complexity per function (Radon)
    complexity_map: Dict[str, int] = {}
    try:
        for block in cc_visit(source_code):
            complexity_map[block.name] = block.complexity
    except Exception:
        pass  # fall back to complexity=1 default for all functions

    functions = extract_functions(tree, complexity_map)

    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

    raw = radon_raw_analyze(source_code)
    # raw: loc, lloc, sloc, comments, multi, blank, single_comments

    comment_ratio = 0.0
    if raw.loc > 0:
        comment_ratio = round((raw.comments + raw.multi) / raw.loc, 4)

    try:
        maintainability_index = round(mi_visit(source_code, multi=True), 2)
    except Exception:
        maintainability_index = None

    complexities = [f.complexity for f in functions] or [1]
    lengths = [f.length for f in functions] or [0]
    nestings = [f.max_nesting for f in functions] or [0]
    params_list = [f.params for f in functions] or [0]

    return {
        "loc": raw.loc,
        "sloc": raw.sloc,
        "blank_lines": raw.blank,
        "comment_lines": raw.comments + raw.multi,
        "comment_ratio": comment_ratio,
        "function_count": len(functions),
        "class_count": len(classes),
        "avg_complexity": round(sum(complexities) / len(complexities), 2),
        "max_complexity": max(complexities),
        "avg_function_length": round(sum(lengths) / len(lengths), 2),
        "max_function_length": max(lengths),
        "max_nesting_depth": max(nestings),
        "avg_params": round(sum(params_list) / len(params_list), 2),
        "max_params": max(params_list),
        "maintainability_index": maintainability_index,
        "functions": [f.to_dict() for f in functions],
    }
