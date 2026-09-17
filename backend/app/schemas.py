from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.config import MAX_CODE_LENGTH_CHARS


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AnalysisCreateRequest(BaseModel):
    code: str
    filename: Optional[str] = "pasted_code.py"
    language: Optional[str] = "python"

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Code cannot be empty")
        if len(v) > MAX_CODE_LENGTH_CHARS:
            raise ValueError(
                f"Code exceeds maximum allowed length of {MAX_CODE_LENGTH_CHARS} characters"
            )
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in ("python",):
            raise ValueError("Only 'python' is currently supported")
        return v


class AnalysisSummary(BaseModel):
    id: str
    filename: str
    language: str
    status: str
    quality_score: Optional[float]
    risk_level: Optional[str]
    from_cache: bool
    created_at: str

    class Config:
        from_attributes = True


class AnalysisDetail(BaseModel):
    id: str
    filename: str
    language: str
    status: str
    error_message: Optional[str]
    quality_score: Optional[float]
    risk_level: Optional[str]
    risk_score: Optional[float]
    metrics: Optional[Dict[str, Any]]
    findings: Optional[List[Dict[str, Any]]]
    security_findings: Optional[List[Dict[str, Any]]]
    function_risk: Optional[List[Dict[str, Any]]]
    sub_scores: Optional[Dict[str, Any]]
    recommendations: Optional[List[Dict[str, Any]]]
    ai_explanation: Optional[str]
    from_cache: bool
    source_code: Optional[str]
    created_at: str

    class Config:
        from_attributes = True
