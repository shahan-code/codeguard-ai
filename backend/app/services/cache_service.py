import hashlib
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.config import ANALYSIS_VERSION
from app.models import AnalysisCache


def compute_code_hash(code: str, language: str) -> str:
    payload = f"{ANALYSIS_VERSION}:{language}:{code}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def get_cached_result(db: Session, code_hash: str) -> Optional[Dict[str, Any]]:
    entry = db.query(AnalysisCache).filter(AnalysisCache.code_hash == code_hash).first()
    return entry.result if entry else None


def store_cached_result(db: Session, code_hash: str, result: Dict[str, Any]) -> None:
    existing = db.query(AnalysisCache).filter(AnalysisCache.code_hash == code_hash).first()
    if existing:
        return
    entry = AnalysisCache(code_hash=code_hash, result=result)
    db.add(entry)
    db.commit()
