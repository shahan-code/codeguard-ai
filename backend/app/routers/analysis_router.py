import datetime
import threading
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models import Analysis, User
from app.schemas import AnalysisCreateRequest, AnalysisSummary, AnalysisDetail
from app.auth import get_current_user
from app.services.cache_service import compute_code_hash, get_cached_result
from app.services.analysis_service import execute_analysis_job
from app.services.pdf_service import generate_pdf_report

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# --- Basic in-memory rate limiting (per user) ---
_RATE_LIMIT_WINDOW_SECONDS = 60
_RATE_LIMIT_MAX_REQUESTS = 20
_rate_buckets: dict[str, deque] = defaultdict(deque)
_rate_lock = threading.Lock()


def _check_rate_limit(user_id: str) -> None:
    now = time.time()
    with _rate_lock:
        bucket = _rate_buckets[user_id]
        while bucket and now - bucket[0] > _RATE_LIMIT_WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= _RATE_LIMIT_MAX_REQUESTS:
            raise HTTPException(status_code=429, detail="Too many analysis requests. Please slow down.")
        bucket.append(now)


def _to_summary(a: Analysis) -> AnalysisSummary:
    return AnalysisSummary(
        id=a.id, filename=a.filename, language=a.language, status=a.status,
        quality_score=a.quality_score, risk_level=a.risk_level,
        from_cache=bool(a.from_cache), created_at=a.created_at.isoformat(),
    )


def _to_detail(a: Analysis) -> AnalysisDetail:
    return AnalysisDetail(
        id=a.id, filename=a.filename, language=a.language, status=a.status,
        error_message=a.error_message, quality_score=a.quality_score,
        risk_level=a.risk_level, risk_score=a.risk_score, metrics=a.metrics,
        findings=a.findings, security_findings=a.security_findings,
        function_risk=a.function_risk, sub_scores=a.sub_scores,
        recommendations=a.recommendations, ai_explanation=a.ai_explanation,
        from_cache=bool(a.from_cache), source_code=a.source_code,
        created_at=a.created_at.isoformat(),
    )


@router.post("", response_model=AnalysisDetail, status_code=status.HTTP_202_ACCEPTED)
def create_analysis(
    payload: AnalysisCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_rate_limit(current_user.id)

    code_hash = compute_code_hash(payload.code, payload.language)
    cached = get_cached_result(db, code_hash)

    analysis = Analysis(
        user_id=current_user.id,
        filename=payload.filename or "pasted_code.py",
        language=payload.language,
        code_hash=code_hash,
        source_code=payload.code,
    )

    if cached:
        analysis.status = "COMPLETED"
        analysis.from_cache = 1
        analysis.metrics = cached["metrics"]
        analysis.findings = cached["findings"]
        analysis.security_findings = cached["security_findings"]
        analysis.function_risk = cached["function_risk"]
        analysis.quality_score = cached["quality_score"]
        analysis.sub_scores = cached["sub_scores"]
        analysis.risk_level = cached["risk_level"]
        analysis.risk_score = cached["risk_score"]
        analysis.recommendations = cached["recommendations"]
        analysis.ai_explanation = cached["ai_explanation"]
        analysis.completed_at = datetime.datetime.utcnow()
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return _to_detail(analysis)

    analysis.status = "QUEUED"
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # Background job: analyze without blocking the request.
    thread = threading.Thread(
        target=execute_analysis_job,
        args=(analysis.id, payload.code, SessionLocal),
        daemon=True,
    )
    thread.start()

    return _to_detail(analysis)


@router.get("", response_model=list[AnalysisSummary])
def list_analyses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    analyses = (
        db.query(Analysis)
        .filter(Analysis.user_id == current_user.id)
        .order_by(Analysis.created_at.desc())
        .all()
    )
    return [_to_summary(a) for a in analyses]


@router.get("/{analysis_id}", response_model=AnalysisDetail)
def get_analysis(analysis_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _to_detail(analysis)


@router.get("/{analysis_id}/status")
def get_analysis_status(analysis_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {"id": analysis.id, "status": analysis.status, "error_message": analysis.error_message}


@router.get("/{analysis_id}/report")
def download_report(analysis_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if analysis.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Analysis is not completed yet")

    pdf_bytes = generate_pdf_report(_to_detail(analysis).model_dump())
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="codeguard-report-{analysis.id}.pdf"'},
    )
