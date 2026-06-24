"""面试相关 ORM 模型"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.engine import Base


class InterviewSessionEntity(Base):
    """面试会话"""
    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    skill_id: Mapped[str] = mapped_column(String(100))
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="IN_PROGRESS")
    current_question_index: Mapped[int] = mapped_column(Integer, default=0)
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    questions_json: Mapped[str | None] = mapped_column(Text, nullable=True, comment="原始题目列表 JSON")
    graph_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    agent_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths_json: Mapped[str | None] = mapped_column(Text, nullable=True, comment="强项 JSON")
    improvements_json: Mapped[str | None] = mapped_column(Text, nullable=True, comment="弱项/改进 JSON")
    reference_answers_json: Mapped[str | None] = mapped_column(Text, nullable=True, comment="参考答案 JSON")
    report_json: Mapped[str | None] = mapped_column(Text, nullable=True, comment="完整报告 JSON")
    evaluate_status: Mapped[str] = mapped_column(String(20), default="PENDING", comment="PENDING / EVALUATED / ERROR")
    evaluate_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    answers: Mapped[list["InterviewAnswerEntity"]] = relationship(
        back_populates="session", cascade="all, delete-orphan",
    )


class InterviewAnswerEntity(Base):
    """单题答案记录"""
    __tablename__ = "interview_answers"
    __table_args__ = (UniqueConstraint("session_id", "question_index", name="uq_session_question"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), index=True,
    )
    question_index: Mapped[int] = mapped_column(Integer)
    question: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(100), default="")
    is_follow_up: Mapped[bool] = mapped_column(Boolean, default=False)
    user_answer: Mapped[str] = mapped_column(Text, default="")
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_answer: Mapped[str | None] = mapped_column(Text, nullable=True, comment="LLM 生成的参考答案")
    key_points_json: Mapped[str | None] = mapped_column(Text, nullable=True, comment="关键点 JSON")
    answered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    session: Mapped["InterviewSessionEntity"] = relationship(back_populates="answers")
