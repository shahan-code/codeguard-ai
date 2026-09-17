import ast
import datetime

from sqlalchemy.orm import Session

from app.analyzers.metrics import compute_metrics
from app.analyzers.smells import detect_smells
from app.analyzers.security import detect_security_issues
from app.ml.risk_model import get_risk_model
from app.services.quality_score import compute_quality_score
from app.services.recommendations import build_recommendations
from app.services.llm_service import generate_explanation
from app.services.cache_service import store_cached_result
from app.models import Analysis


def run_analysis_pipeline(code: str) -> dict:
    """
    Pure function: source code -> full analysis result dict.
    Never executes the given code — static analysis only (ast.parse).
    """
    try:
        ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"Code could not be parsed: {e.msg} (line {e.lineno})")

    metrics = compute_metrics(code)
    smells = detect_smells(code, metrics)
    security_findings = detect_security_issues(code)

    quality = compute_quality_score(metrics, smells, security_findings)
    risk_model = get_risk_model()
    risk = risk_model.predict(metrics, smells, security_findings)

    # Function-level risk table
    function_risk = []
    for fn in metrics["functions"]:
        if fn["complexity"] >= 10 or fn["length"] >= 40 or fn["max_nesting"] >= 4:
            level = "HIGH" if (fn["complexity"] >= 15 or fn["length"] >= 80) else "MEDIUM"
        elif fn["complexity"] >= 6:
            level = "MEDIUM"
        else:
            level = "LOW"
        function_risk.append({
            "name": fn["name"],
            "line": fn["line"],
            "complexity": fn["complexity"],
            "length": fn["length"],
            "risk": level,
        })
    function_risk.sort(key=lambda f: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[f["risk"]])

    recommendations = build_recommendations(smells, security_findings)

    explanation = generate_explanation(
        quality["overall"], risk.risk_level, metrics, smells, security_findings
    )

    return {
        "metrics": metrics,
        "findings": smells,
        "security_findings": security_findings,
        "function_risk": function_risk,
        "quality_score": quality["overall"],
        "sub_scores": quality["sub_scores"],
        "risk_level": risk.risk_level,
        "risk_score": risk.risk_score,
        "risk_contributions": [c for c in risk.contributions],
        "recommendations": recommendations,
        "ai_explanation": explanation["text"],
        "ai_explanation_source": explanation["source"],
    }


def execute_analysis_job(analysis_id: str, code: str, db_session_factory) -> None:
    """
    Runs in a background thread. Creates its own DB session since the
    request-scoped session is closed by the time this executes.
    """
    db: Session = db_session_factory()
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            return
        analysis.status = "RUNNING"
        db.commit()

        try:
            result = run_analysis_pipeline(code)
        except ValueError as e:
            analysis.status = "FAILED"
            analysis.error_message = str(e)
            db.commit()
            return

        analysis.status = "COMPLETED"
        analysis.metrics = result["metrics"]
        analysis.findings = result["findings"]
        analysis.security_findings = result["security_findings"]
        analysis.function_risk = result["function_risk"]
        analysis.quality_score = result["quality_score"]
        analysis.sub_scores = result["sub_scores"]
        analysis.risk_level = result["risk_level"]
        analysis.risk_score = result["risk_score"]
        analysis.recommendations = result["recommendations"]
        analysis.ai_explanation = result["ai_explanation"]
        analysis.completed_at = datetime.datetime.utcnow()
        db.commit()

        store_cached_result(db, analysis.code_hash, {
            "metrics": result["metrics"],
            "findings": result["findings"],
            "security_findings": result["security_findings"],
            "function_risk": result["function_risk"],
            "quality_score": result["quality_score"],
            "sub_scores": result["sub_scores"],
            "risk_level": result["risk_level"],
            "risk_score": result["risk_score"],
            "recommendations": result["recommendations"],
            "ai_explanation": result["ai_explanation"],
        })
    except Exception as e:  # never let the background thread crash silently
        try:
            analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
            if analysis:
                analysis.status = "FAILED"
                analysis.error_message = f"Internal error: {e}"
                db.commit()
        finally:
            pass
    finally:
        db.close()
