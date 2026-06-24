"""简历相关 ORM 模型"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.engine import Base


class ResumeEntity(Base):
    """简历文件"""
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="SHA-256")
    original_filename: Mapped[str] = mapped_column(String(500))
    file_size: Mapped[int] = mapped_column(Integer)
    content_type: Mapped[str] = mapped_column(String(200))
    storage_path: Mapped[str] = mapped_column(String(1000))
    resume_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="解析后的纯文本")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    access_count: Mapped[int] = mapped_column(Integer, default=1)
    analyze_status: Mapped[str] = mapped_column(String(20), default="PENDING", comment="PENDING / PROCESSING / COMPLETED / FAILED")
    analyze_error: Mapped[str | None] = mapped_column(String(500), nullable=True)

    analyses: Mapped[list["ResumeAnalysisEntity"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan",
    )


class ResumeAnalysisEntity(Base):
    """简历分析结果"""
    __tablename__ = "resume_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    overall_score: Mapped[int] = mapped_column(Integer, default=0)
    content_score: Mapped[int] = mapped_column(Integer, default=0)
    structure_score: Mapped[int] = mapped_column(Integer, default=0)
    skill_match_score: Mapped[int] = mapped_column(Integer, default=0)
    expression_score: Mapped[int] = mapped_column(Integer, default=0)
    project_score: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths_json: Mapped[str | None] = mapped_column(Text, nullable=True, comment="强项 JSON")
    suggestions_json: Mapped[str | None] = mapped_column(Text, nullable=True, comment="建议 JSON")
    analyzed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    resume: Mapped["ResumeEntity"] = relationship(back_populates="analyses")
