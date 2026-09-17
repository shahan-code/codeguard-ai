from typing import Any, Dict, List

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
PRIORITY_LABELS = {0: "Priority 1 — Critical", 1: "Priority 2 — High", 2: "Priority 3 — Medium", 3: "Priority 4 — Low"}


def build_recommendations(
    smells: List[Dict[str, Any]],
    security_findings: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    items = []
    for f in security_findings:
        items.append({
            "severity": f["severity"],
            "title": f["issue"],
            "recommendation": f["recommendation"],
            "line": f.get("line"),
        })
    for s in smells:
        items.append({
            "severity": s["severity"],
            "title": s["title"],
            "recommendation": s["recommendation"],
            "line": s.get("line"),
        })

    items.sort(key=lambda x: SEVERITY_ORDER.get(x["severity"], 3))

    recommendations = []
    for idx, item in enumerate(items[:10], start=1):
        recommendations.append({
            "rank": idx,
            "priority_label": PRIORITY_LABELS.get(SEVERITY_ORDER.get(item["severity"], 3)),
            "title": item["title"],
            "recommendation": item["recommendation"],
            "line": item["line"],
        })
    return recommendations
