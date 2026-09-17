import datetime
import uuid

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.database import Base


def gen_id():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    analyses = relationship("Analysis", back_populates="user")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String, default="pasted_code.py")
    language = Column(String, default="python")
    code_hash = Column(String, index=True, nullable=False)
    status = Column(String, default="QUEUED")  # QUEUED, RUNNING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)

    quality_score = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)  # LOW, MEDIUM, HIGH, CRITICAL
    risk_score = Column(Float, nullable=True)

    metrics = Column(JSON, nullable=True)
    findings = Column(JSON, nullable=True)          # code smells
    security_findings = Column(JSON, nullable=True)
    function_risk = Column(JSON, nullable=True)
    sub_scores = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    ai_explanation = Column(Text, nullable=True)
    from_cache = Column(Integer, default=0)  # 0/1 bool

    source_code = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="analyses")


class AnalysisCache(Base):
    __tablename__ = "analysis_cache"

    id = Column(String, primary_key=True, default=gen_id)
    code_hash = Column(String, unique=True, index=True, nullable=False)
    result = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
