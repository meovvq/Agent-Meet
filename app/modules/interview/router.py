"""面试模块 API 路由"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.result import Result
from app.database.engine import get_db
from app.modules.interview.graph.service import InterviewGraphService
from app.modules.interview.session_service import InterviewSessionService
from app.schemas.interview import StartInterviewRequest, SubmitAnswerRequest

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/interview", tags=["interview"])


# ========== 面试流程 ==========

@router.post("/start")
async def start_interview(req: StartInterviewRequest):
    """启动面试（Agent 模式或工作流模式）

    questions 为可选：不传时自动调用出题引擎根据 skill_id 生成。
    """
    #传入题目，则直接用
    questions = req.questions

    # 如果没有传入题目，自动调用出题引擎
    if not questions:
        from app.modules.interview.question_service import generate_questions
        questions = await generate_questions(
            skill_id=req.skill_id,
            difficulty=req.difficulty,
            question_count=req.question_count,
            resume_text=req.resume_text,
        )

    service = InterviewGraphService(agent_mode=req.agent_mode)
    result = await service.start_interview(
        session_id=req.session_id,
        skill_id=req.skill_id,
        difficulty=req.difficulty,
        questions=questions,
        resume_text=req.resume_text,
    )
    return Result.success(data=result)


@router.post("/sessions/{session_id}/answer")
async def submit_answer(session_id: str, req: SubmitAnswerRequest, agent_mode: bool = True):
    """提交答案"""
    service = InterviewGraphService(agent_mode=agent_mode)
    result = await service.submit_answer(session_id, req.answer)
    return Result.success(data=result)


# ========== 技能列表 ==========

@router.get("/skills")
async def list_skills():
    """获取技能列表（从 skills/ 目录加载）"""
    from app.modules.interview.skill_service import skill_service
    skills = skill_service.list_skills()
    return Result.success(data=skills)


# ========== 会话管理 ==========

@router.get("/sessions")
async def list_sessions(db: AsyncSession = Depends(get_db)):
    """获取面试会话列表"""
    service = InterviewSessionService(db)
    data = await service.list_sessions()
    return Result.success(data=data)


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """获取会话详情（含答题记录）"""
    service = InterviewSessionService(db)
    data = await service.get_session_with_answers(session_id)
    return Result.success(data=data)


@router.get("/sessions/{session_id}/report")
async def get_report(session_id: str, db: AsyncSession = Depends(get_db)):
    """获取评估报告"""
    service = InterviewSessionService(db)
    data = await service.get_report(session_id)
    return Result.success(data=data)


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """删除会话"""
    service = InterviewSessionService(db)
    await service.delete_session(session_id)
    return Result.success()
