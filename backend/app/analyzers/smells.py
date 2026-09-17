"""
Rule-based code smell detection.

Every finding is derived from real AST/metric data — no fabricated line
numbers. Thresholds are simple, documented constants (not ML-tuned) so the
results stay fully explainable.
"""
import ast
import hashlib
from typing import Any, Dict, List

# --- Thresholds (documented, deterministic) ---
LONG_FUNCTION_LINES = 40
HIGH_COMPLEXITY = 10
DEEP_NESTING = 4
TOO_MANY_PARAMS = 5
LARGE_CLASS_METHODS = 15


def _finding(title, category, severity, line, description, why, recommendation):
    return {
        "title": title,
        "category": category,
        "severity": severity,
        "line": line,
        "description": description,
        "why_it_matters": why,
        "recommendation": recommendation,
    }


def _is_poor_name(name: str) -> bool:
    if name in ("__init__", "__main__", "__str__", "__repr__"):
        return False
    if len(name) <= 2 and not name.startswith("_"):
        return True
    if name.lower() in ("data", "tmp", "temp", "foo", "bar", "x1", "x2", "val", "obj"):
        return True
    return False


def _duplicate_blocks(tree: ast.Module) -> List[Dict[str, Any]]:
    """
    Lightweight duplicate-logic detector: hashes the normalized dump of each
    function body. Flags functions whose body structure is identical to
    another function's (a strong signal of copy-pasted logic).
    """
    seen: Dict[str, List[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if len(node.body) < 2:
                continue
            try:
                # Hash only the body statements (not the function name/args),
                # so structurally-identical logic in differently-named
                # functions is still detected as duplication.
                dump = "|".join(ast.dump(stmt, annotate_fields=False) for stmt in node.body)
            except Exception:
                continue
            key = hashlib.sha256(dump.encode()).hexdigest()
            seen.setdefault(key, []).append(node.name)

    findings = []
    for key, names in seen.items():
        if len(names) > 1:
            findings.append({"names": names})
    return findings


def detect_smells(source_code: str, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    tree = ast.parse(source_code)
    findings: List[Dict[str, Any]] = []

    for fn in metrics.get("functions", []):
        name = fn["name"]
        line = fn["line"]

        if fn["length"] > LONG_FUNCTION_LINES:
            findings.append(_finding(
                "Long Function", "size", "HIGH" if fn["length"] > 80 else "MEDIUM", line,
                f"Function '{name}' is {fn['length']} lines long (threshold: {LONG_FUNCTION_LINES}).",
                "Long functions are harder to read, test, and maintain, and tend to accumulate more defects.",
                f"Split '{name}' into smaller, single-purpose functions.",
            ))

        if fn["complexity"] > HIGH_COMPLEXITY:
            severity = "CRITICAL" if fn["complexity"] > 20 else "HIGH"
            findings.append(_finding(
                "High Cyclomatic Complexity", "complexity", severity, line,
                f"Function '{name}' has cyclomatic complexity {fn['complexity']} (threshold: {HIGH_COMPLEXITY}).",
                "High complexity increases the number of test cases needed and the likelihood of hidden bugs.",
                f"Refactor '{name}' to reduce branching — extract helper functions or use early returns.",
            ))

        if fn["max_nesting"] > DEEP_NESTING:
            findings.append(_finding(
                "Deep Nesting", "structure", "MEDIUM", line,
                f"Function '{name}' has a nesting depth of {fn['max_nesting']} (threshold: {DEEP_NESTING}).",
                "Deeply nested logic is difficult to follow and error-prone to modify safely.",
                f"Flatten nested conditionals in '{name}' using guard clauses or extracted helpers.",
            ))

        if fn["params"] > TOO_MANY_PARAMS:
            findings.append(_finding(
                "Too Many Parameters", "structure", "LOW", line,
                f"Function '{name}' takes {fn['params']} parameters (threshold: {TOO_MANY_PARAMS}).",
                "Functions with many parameters are hard to call correctly and often signal too many responsibilities.",
                f"Group related parameters of '{name}' into a data class or config object.",
            ))

        if _is_poor_name(name):
            findings.append(_finding(
                "Poor Function Naming", "readability", "LOW", line,
                f"Function name '{name}' is not descriptive.",
                "Unclear names slow down comprehension and code review.",
                f"Rename '{name}' to describe what it actually does.",
            ))

    # Class-level: large class (too many methods)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            if len(methods) > LARGE_CLASS_METHODS:
                findings.append(_finding(
                    "Large Class", "size", "MEDIUM", node.lineno,
                    f"Class '{node.name}' defines {len(methods)} methods (threshold: {LARGE_CLASS_METHODS}).",
                    "Large classes often violate single-responsibility and become hard to maintain.",
                    f"Split '{node.name}' into smaller, focused classes.",
                ))
            # poor variable naming inside class bodies is skipped to avoid noise

    # Poor naming for simple variable assignments at module/function scope
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            if _is_poor_name(node.id) and node.id not in ("_",):
                findings.append(_finding(
                    "Poor Variable Naming", "readability", "LOW", node.lineno,
                    f"Variable '{node.id}' is not descriptive.",
                    "Unclear variable names make code harder to review and maintain.",
                    f"Rename '{node.id}' to something descriptive of its purpose.",
                ))

    # Duplicate logic
    for dup in _duplicate_blocks(tree):
        names = dup["names"]
        # use the line of the first occurrence found in metrics
        line = None
        for fn in metrics.get("functions", []):
            if fn["name"] == names[0]:
                line = fn["line"]
                break
        findings.append(_finding(
            "Duplicate Logic", "duplication", "MEDIUM", line,
            f"Functions {', '.join(names)} contain identical logic structures.",
            "Duplicated logic multiplies maintenance effort — a fix in one copy is easily missed in the other.",
            "Extract the shared logic into a single reusable function.",
        ))

    # Excessive comments (relative to code) can indicate dead/commented-out code
    if metrics.get("comment_ratio", 0) > 0.5 and metrics.get("loc", 0) > 20:
        findings.append(_finding(
            "Excessive Comments", "readability", "LOW", None,
            f"Comment ratio is {metrics['comment_ratio'] * 100:.0f}% of lines.",
            "An unusually high comment ratio can indicate dead/commented-out code left in the file.",
            "Remove stale or commented-out code rather than keeping it in comments.",
        ))

    return findings
