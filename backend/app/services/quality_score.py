"""
Deterministic Code Quality Score (0-100).

Pure function of metrics + findings — same input always produces the same
score. No randomness, no ML involved here (the ML model only drives the
Defect Risk prediction, kept separate per project design).
"""
from typing import Any, Dict, List

SEVERITY_PENALTY = {"LOW": 1, "MEDIUM": 3, "HIGH": 6, "CRITICAL": 12}


def _clamp(v: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, v))


def _complexity_score(metrics: Dict[str, Any]) -> float:
    avg_c = metrics.get("avg_complexity", 1)
    max_c = metrics.get("max_complexity", 1)
    # 100 at complexity 1, 0 at complexity >= 30 (weighted toward avg)
    penalty = (avg_c - 1) * 3.5 + (max_c - 1) * 1.0
    return round(_clamp(100 - penalty), 1)


def _structure_score(metrics: Dict[str, Any]) -> float:
    nesting = metrics.get("max_nesting_depth", 0)
    avg_len = metrics.get("avg_function_length", 0)
    max_len = metrics.get("max_function_length", 0)
    avg_params = metrics.get("avg_params", 0)
    penalty = nesting * 6 + max(0, avg_len - 20) * 0.5 + max(0, max_len - 40) * 0.3 + max(0, avg_params - 4) * 3
    return round(_clamp(100 - penalty), 1)


def _readability_score(metrics: Dict[str, Any], smells: List[Dict[str, Any]]) -> float:
    naming_issues = sum(1 for s in smells if s["category"] == "readability")
    comment_ratio = metrics.get("comment_ratio", 0)
    penalty = naming_issues * 5
    # Very low comment ratio on a large file is a mild readability penalty
    if metrics.get("loc", 0) > 60 and comment_ratio < 0.03:
        penalty += 5
    return round(_clamp(100 - penalty), 1)


def _security_score(security_findings: List[Dict[str, Any]]) -> float:
    penalty = sum(SEVERITY_PENALTY.get(f["severity"], 1) * 3 for f in security_findings)
    return round(_clamp(100 - penalty), 1)


def _maintainability_score(metrics: Dict[str, Any], smells: List[Dict[str, Any]]) -> float:
    mi = metrics.get("maintainability_index")
    smell_penalty = sum(SEVERITY_PENALTY.get(s["severity"], 1) for s in smells)
    if mi is not None:
        # Radon MI is already 0-100
        base = mi
    else:
        base = 100
    return round(_clamp(base - smell_penalty), 1)


def compute_quality_score(
    metrics: Dict[str, Any],
    smells: List[Dict[str, Any]],
    security_findings: List[Dict[str, Any]],
) -> Dict[str, Any]:
    sub_scores = {
        "maintainability": _maintainability_score(metrics, smells),
        "complexity": _complexity_score(metrics),
        "security": _security_score(security_findings),
        "readability": _readability_score(metrics, smells),
        "structure": _structure_score(metrics),
    }

    # Weighted overall score — weights documented and fixed.
    weights = {
        "maintainability": 0.25,
        "complexity": 0.25,
        "security": 0.20,
        "readability": 0.15,
        "structure": 0.15,
    }
    overall = sum(sub_scores[k] * w for k, w in weights.items())
    overall = round(_clamp(overall), 1)

    return {"overall": overall, "sub_scores": sub_scores}
