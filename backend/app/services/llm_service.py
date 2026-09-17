"""
Optional AI explanation layer.

IMPORTANT (per design): the LLM never calculates the quality score or
defect risk — those come from the deterministic engine and the ML risk
model. The LLM only explains findings that were already computed, in
plain language. If no API key is configured, or the call fails/times out,
a deterministic template explanation is used instead — the app never
crashes or blocks on the LLM.
"""
import json
from typing import Any, Dict, List, Optional

import httpx

from app.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

REQUEST_TIMEOUT_SECONDS = 8


def _deterministic_explanation(
    quality_score: float,
    risk_level: str,
    smells: List[Dict[str, Any]],
    security_findings: List[Dict[str, Any]],
) -> str:
    top_issues = []
    for f in security_findings[:2]:
        top_issues.append(f["issue"])
    for s in smells[:3]:
        top_issues.append(s["title"])

    if not top_issues:
        return (
            f"This code scored {quality_score}/100 with {risk_level} predicted defect risk. "
            "No significant code smells or security patterns were detected."
        )

    issues_text = "; ".join(top_issues[:4])
    return (
        f"This code scored {quality_score}/100 with {risk_level} predicted defect risk, "
        f"mainly due to: {issues_text}. Addressing the highest-severity items first "
        "will have the largest impact on both quality and predicted risk."
    )


def generate_explanation(
    quality_score: float,
    risk_level: str,
    metrics: Dict[str, Any],
    smells: List[Dict[str, Any]],
    security_findings: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Returns {"text": str, "source": "llm" | "deterministic"}
    Never raises — always returns something usable.
    """
    fallback_text = _deterministic_explanation(quality_score, risk_level, smells, security_findings)

    if not OPENAI_API_KEY:
        return {"text": fallback_text, "source": "deterministic"}

    findings_summary = {
        "quality_score": quality_score,
        "risk_level": risk_level,
        "metrics_summary": {
            "loc": metrics.get("loc"),
            "avg_complexity": metrics.get("avg_complexity"),
            "max_complexity": metrics.get("max_complexity"),
            "max_nesting_depth": metrics.get("max_nesting_depth"),
        },
        "top_smells": [
            {"title": s["title"], "severity": s["severity"]} for s in smells[:5]
        ],
        "top_security_findings": [
            {"issue": f["issue"], "severity": f["severity"]} for f in security_findings[:5]
        ],
    }

    system_prompt = (
        "You are a senior code reviewer. You are given ALREADY-COMPUTED findings "
        "(metrics, code smells, security patterns) for a piece of Python code. "
        "Explain in 2-4 short sentences, in plain developer-friendly language, WHY the "
        "code received this quality score and risk level, using ONLY the findings "
        "provided. Do not invent new issues, line numbers, or metrics. Do not restate "
        "raw numbers robotically — explain the practical impact."
    )

    try:
        response = httpx.post(
            f"{OPENAI_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(findings_summary)},
                ],
                "max_tokens": 300,
                "temperature": 0.3,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        if not text:
            return {"text": fallback_text, "source": "deterministic"}
        return {"text": text, "source": "llm"}
    except Exception:
        # Never let LLM failures break the analysis pipeline.
        return {"text": fallback_text, "source": "deterministic"}
