"""记忆管理节点

短期记忆：通过 AgentState 中的 candidate_profile / topic_performance 等字段实现，
         在 update_agent_context 节点中累积更新。
长期记忆：通过 CandidateMemoryEntity ORM 持久化到数据库，
         在面试开始时加载、面试结束时保存。
"""

import json
import logging
from datetime import datetime

from app.modules.interview.graph.state import AgentState

log = logging.getLogger(__name__)


# ========== 长期记忆加载 ==========

async def load_memory(state: AgentState) -> dict:
    """面试开始时加载候选人长期记忆

    从 CandidateMemoryEntity 中读取该用户的历史画像和面试总结，
    合并到 state.candidate_profile 中供 Agent 决策参考。
    """
    # 延迟导入避免循环依赖
    try:
        from app.models.memory import CandidateMemoryEntity
        from app.database.engine import async_session
        from sqlalchemy import select
    except ImportError:
        log.warning("记忆模型未就绪，跳过长期记忆加载")
        return {}

    # 通过 session_id 查找 user_id（需要 InterviewSessionEntity）
    try:
        from app.models.interview import InterviewSessionEntity
        async with async_session() as db:
            session_result = await db.execute(
                select(InterviewSessionEntity).where(
                    InterviewSessionEntity.id == state.get("session_id", "")
                )
            )
            session_entity = session_result.scalar_one_or_none()
            if not session_entity:
                log.info("未找到面试会话，跳过长期记忆加载")
                return {}
            user_id = session_entity.user_id
    except Exception as e:
        log.warning("获取 user_id 失败: %s", e)
        return {}

    if not user_id:
        return {}

    # 加载长期记忆
    try:
        async with async_session() as db:
            result = await db.execute(
                select(CandidateMemoryEntity).where(
                    CandidateMemoryEntity.user_id == user_id
                ).order_by(CandidateMemoryEntity.updated_at.desc())
            )
            memories = result.scalars().all()

        if not memories:
            log.info("用户 %s 无长期记忆", user_id)
            return {}

        # 合并记忆到候选人画像
        profile = state.get("candidate_profile", {})
        for mem in memories:
            content = mem.content if isinstance(mem.content, dict) else json.loads(mem.content)
            if mem.memory_type == "profile":
                profile.update(content)
            elif mem.memory_type == "interview_summary":
                # 最近一次面试总结
                profile["last_interview_summary"] = content
            elif mem.memory_type == "skill_progress":
                profile["skill_progress"] = content

        profile["interview_count"] = len([m for m in memories if m.memory_type == "interview_summary"])
        log.info("长期记忆已加载: user=%s, memories=%d", user_id, len(memories))
        return {"candidate_profile": profile}

    except Exception as e:
        log.error("加载长期记忆失败: %s", e, exc_info=True)
        return {}


# ========== 长期记忆保存 ==========

async def save_memory(state: AgentState) -> dict:
    """面试结束时保存长期记忆

    将本次面试的候选人画像和面试总结持久化到数据库，
    供下次面试时加载。
    """
    try:
        from app.models.memory import CandidateMemoryEntity
        from app.database.engine import async_session
        from sqlalchemy import select
    except ImportError:
        log.warning("记忆模型未就绪，跳过长期记忆保存")
        return {}

    session_id = state.get("session_id", "")
    if not session_id:
        return {}

    # 获取 user_id
    try:
        from app.models.interview import InterviewSessionEntity
        async with async_session() as db:
            result = await db.execute(
                select(InterviewSessionEntity).where(InterviewSessionEntity.id == session_id)
            )
            session_entity = result.scalar_one_or_none()
            if not session_entity:
                return {}
            user_id = session_entity.user_id
    except Exception as e:
        log.warning("获取 user_id 失败: %s", e)
        return {}

    if not user_id:
        return {}

    # 保存候选人画像
    profile = state.get("candidate_profile", {})
    report = state.get("report", {})

    try:
        async with async_session() as db:
            # 保存/更新画像
            existing = await db.execute(
                select(CandidateMemoryEntity).where(
                    CandidateMemoryEntity.user_id == user_id,
                    CandidateMemoryEntity.memory_type == "profile",
                )
            )
            profile_mem = existing.scalar_one_or_none()

            if profile_mem:
                profile_mem.content = profile
                profile_mem.updated_at = datetime.utcnow()
            else:
                db.add(CandidateMemoryEntity(
                    user_id=user_id,
                    memory_type="profile",
                    content=profile,
                ))

            # 保存面试总结
            summary = {
                "session_id": session_id,
                "overall_score": report.get("overall_score", 0),
                "skill_id": state.get("skill_id", ""),
                "difficulty": state.get("difficulty", ""),
                "strong_topics": profile.get("strong_topics", []),
                "weak_topics": profile.get("weak_topics", []),
                "total_questions": len(state.get("questions", [])),
                "completed_at": datetime.utcnow().isoformat(),
            }
            db.add(CandidateMemoryEntity(
                user_id=user_id,
                memory_type="interview_summary",
                content=summary,
            ))

            await db.commit()
            log.info("长期记忆已保存: user=%s", user_id)

    except Exception as e:
        log.error("保存长期记忆失败: %s", e, exc_info=True)

    return {}
