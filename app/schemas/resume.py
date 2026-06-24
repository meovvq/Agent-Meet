"""简历相关 Schema"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ResumeListItemDTO(BaseModel):
    id: int
    filename: str
    file_size: int
    uploaded_at: datetime
    access_count: int
    latest_score: int | None = None
    analyze_status: str
    analyze_error: str | None = None


class AnalysisHistoryDTO(BaseModel):
    id: int
    overall_score: int
    content_score: int
    structure_score: int
    skill_match_score: int
    expression_score: int
    project_score: int
    summary: str | None = None
    analyzed_at: datetime
    strengths: list[str] = []
    suggestions: list[Any] = []


class ResumeDetailDTO(BaseModel):
    id: int
    filename: str
    file_size: int
    content_type: str
    uploaded_at: datetime
    access_count: int
    resume_text: str | None = None
    analyze_status: str
    analyze_error: str | None = None
    analyses: list[AnalysisHistoryDTO] = []


class ResumeAnalysisResponse(BaseModel):
    overall_score: int = 0
    score_detail: dict = {}
    summary: str = ""
    strengths: list[str] = []
    suggestions: list[Any] = []
