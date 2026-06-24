"""面试会话管理服务"""

import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.exception import BusinessException, ErrorCode
from app.models.interview import InterviewAnswerEntity, InterviewSessionEntity
from app.schemas.interview import (
    InterviewAnswerDTO,
    InterviewDetailDTO,
    InterviewReportDTO,
    InterviewSessionDTO,
    SessionListItemDTO,
)

log = logging.getLogger(__name__)


class InterviewSessionService:
    """面试会话管理"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_sessions(self) -> list[dict]:
        """获取会话列表"""
        result = await self.db.execute(
            select(InterviewSessionEntity).order_by(InterviewSessionEntity.created_at.desc())
        )
        sessions = result.scalars().all()
        return [
            SessionListItemDTO(
                session_id=s.id,
                skill_id=s.skill_id,
                difficulty=s.difficulty,
                total_questions=s.total_questions,
                status=s.status,
                evaluate_status=s.evaluate_status or "PENDING",
                overall_score=s.overall_score,
                created_at=s.created_at,
                completed_at=s.completed_at,
            ).model_dump()
            for s in sessions
        ]

    async def get_session(self, session_id: str) -> dict:
        """获取会话详情（含题目列表）"""
        session = await self._get_session(session_id)
        questions = json.loads(session.questions_json or "[]")
        return InterviewSessionDTO(
            session_id=session.id,
            skill_id=session.skill_id,
            difficulty=session.difficulty,
            total_questions=session.total_questions,
            current_question_index=session.current_question_index,
            status=session.status,
            agent_mode=session.agent_mode,
            questions=[InterviewQuestionDTO(**q) for q in questions],
            created_at=session.created_at,
            completed_at=session.completed_at,
        ).model_dump()

    async def get_session_with_answers(self, session_id: str) -> dict:
        """获取会话详情（含答题记录）"""
        session = await self._get_session(session_id)
        questions = json.loads(session.questions_json or "[]")

        # 查询所有答案
        result = await self.db.execute(
            select(InterviewAnswerEntity)
            .where(InterviewAnswerEntity.session_id == session_id)
            .order_by(InterviewAnswerEntity.question_index)
        )
        answers_map = {a.question_index: a for a in result.scalars().all()}

        question_details = []
        for i, q in enumerate(questions):
            a = answers_map.get(i)
            question_details.append(InterviewAnswerDTO(
                question_index=i,
                question=q.get("question", ""),
                category=q.get("category", ""),
                is_follow_up=q.get("is_follow_up", False),
                user_answer=a.user_answer if a else "",
                score=a.score if a else None,
                feedback=a.feedback if a else None,
                reference_answer=a.reference_answer if a else None,
                key_points=json.loads(a.key_points_json) if a and a.key_points_json else [],
            ))

        return InterviewDetailDTO(
            session_id=session.id,
            skill_id=session.skill_id,
            difficulty=session.difficulty,
            total_questions=session.total_questions,
            status=session.status,
            evaluate_status=session.evaluate_status or "PENDING",
            overall_score=session.overall_score,
            overall_feedback=session.overall_feedback,
            strengths=json.loads(session.strengths_json) if session.strengths_json else [],
            improvements=json.loads(session.improvements_json) if session.improvements_json else [],
            question_details=question_details,
            created_at=session.created_at,
            completed_at=session.completed_at,
        ).model_dump()

    async def get_report(self, session_id: str) -> dict:
        """获取评估报告"""
        session = await self._get_session(session_id)

        if session.status != "EVALUATED":
            if session.evaluate_status == "PENDING":
                raise BusinessException(ErrorCode.INTERVIEW_EVALUATION_FAILED, "评估尚未开始")
            if session.evaluate_status == "PROCESSING":
                raise BusinessException(ErrorCode.INTERVIEW_EVALUATION_FAILED, "评估进行中，请稍后")
            if session.evaluate_status == "ERROR":
                raise BusinessException(ErrorCode.INTERVIEW_EVALUATION_FAILED, f"评估失败: {session.evaluate_error}")
            raise BusinessException(ErrorCode.INTERVIEW_EVALUATION_FAILED, "面试尚未完成")

        report_data = json.loads(session.report_json) if session.report_json else {}

        return InterviewReportDTO(
            session_id=session.id,
            total_questions=session.total_questions,
            overall_score=session.overall_score or 0,
            overall_feedback=session.overall_feedback or "",
            strengths=json.loads(session.strengths_json) if session.strengths_json else [],
            improvements=json.loads(session.improvements_json) if session.improvements_json else [],
            topic_scores=report_data.get("topic_scores", {}),
        ).model_dump()

    async def delete_session(self, session_id: str) -> None:
        """删除会话"""
        session = await self._get_session(session_id)
        await self.db.delete(session)
        await self.db.commit()
        log.info("会话已删除: %s", session_id)

    async def _get_session(self, session_id: str) -> InterviewSessionEntity:
        """获取会话实体（不存在则抛异常）"""
        result = await self.db.execute(
            select(InterviewSessionEntity).where(InterviewSessionEntity.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise BusinessException(ErrorCode.INTERVIEW_SESSION_NOT_FOUND, f"面试会话不存在: {session_id}")
        return session
