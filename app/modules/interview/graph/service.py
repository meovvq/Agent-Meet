"""Interview Agent Service —— HTTP API ↔ LangGraph 桥接

封装图的启动（start_interview）和恢复（submit_answer），
根据 agent_mode 选择使用工作流图或 Agent 图。
"""

import json
import logging
from typing import Any

from langgraph.types import Command

from app.common.metrics import finish_session_trace, get_global_metrics, start_session_trace
from app.modules.interview.graph.graph_builder import agent_graph, workflow_graph
from app.modules.interview.graph.state import AgentState

log = logging.getLogger(__name__)


class InterviewGraphService:
    """面试图服务 —— 桥接 HTTP API 和 LangGraph"""

    def __init__(self, agent_mode: bool = True):
        self.agent_mode = agent_mode
        self.graph = agent_graph if agent_mode else workflow_graph

    async def start_interview(
        self,
        session_id: str,
        skill_id: str,
        difficulty: str,
        questions: list[dict],
        resume_text: str = "",
    ) -> dict[str, Any]:
        """启动面试图

        构建初始状态并调用图，图运行到 wait_for_answer 节点时被 interrupt 暂停。
        返回第一道题的信息。
        """
        # 持久化初始 session 记录
        await self._create_session(session_id, skill_id, difficulty, questions)

        initial_state: AgentState = {
            # 基础字段
            "session_id": session_id,
            "skill_id": skill_id,
            "difficulty": difficulty,
            "resume_text": resume_text,
            "questions": questions,
            "current_index": 0,
            "total_original": len(questions),
            "follow_up_counts": {},
            "current_answer": "",
            "evaluation": {},
            "action": "",
            "hint": "",
            "report": None,
            "done": False,
            # Agent 字段
            "agent_mode": self.agent_mode,
            "agent_history": [],
            "available_tools": [],
            "max_reasoning_steps": 3,
            # 记忆
            "candidate_profile": {},
            "topic_performance": {},
            # 规划
            "interview_strategy": {},
            "difficulty_adjustment": 1.0,
            "focus_topics": [],
            # 上下文
            "recent_scores": [],
            "consecutive_high": 0,
            "consecutive_low": 0,
        }

        # 启动会话 Trace
        start_session_trace(session_id)

        config = {"configurable": {"thread_id": session_id}}
        result = await self.graph.ainvoke(initial_state, config=config)

        # 如果图直接结束（无题目），立即输出 Trace
        if result.get("done"):
            finish_session_trace(session_id)

        return self._extract_question_response(result)

    async def submit_answer(self, session_id: str, answer: str) -> dict[str, Any]:
        """提交答案并恢复图执行

        通过 Command(resume=answer) 恢复被 interrupt 暂停的图。
        """
        config = {"configurable": {"thread_id": session_id}}
        result = await self.graph.ainvoke(Command(resume=answer), config=config)

        # 面试结束时输出 Trace 摘要
        if result.get("done"):
            trace = finish_session_trace(session_id)
            if trace:
                metrics = get_global_metrics()
                log.info("[trace:%s] 全局 LLM 指标: %s", session_id,
                         json.dumps(metrics, ensure_ascii=False))

    #传到前端-第一题
        return self._extract_response(result)

    # ========== 响应提取 ==========

    def _extract_question_response(self, state: dict) -> dict:
        """提取题目信息（首次启动）"""
        idx = state.get("current_index", 0)
        questions = state.get("questions", [])
        if idx >= len(questions):
            return {"done": True, "report": state.get("report")}

        q = questions[idx]
        return {
            "done": False,
            "question": q.get("question", ""),
            "question_index": idx,
            "category": q.get("category", ""),
            "is_follow_up": q.get("is_follow_up", False),
            "hint": state.get("hint", ""),
            # Agent 特有
            "interview_strategy": state.get("interview_strategy", {}),
        }

    def _extract_response(self, state: dict) -> dict:
        """提取评估结果 + 下一题（或报告）"""
        if state.get("done"):
            return self._build_report_response(state)

        idx = state.get("current_index", 0)
        questions = state.get("questions", [])
        eval_result = state.get("evaluation", {})

        response = {
            "done": False,
            "evaluation": eval_result,
            "question_index": idx,
        }

        # 下一题
        if idx < len(questions):
            q = questions[idx]
            response.update({
                "question": q.get("question", ""),
                "category": q.get("category", ""),
                "is_follow_up": q.get("is_follow_up", False),
                "hint": state.get("hint", ""),
            })

        # Agent 推理历史（可选，前端可展示 Agent 思考过程）
        if self.agent_mode and state.get("agent_history"):
            last_reasoning = state["agent_history"][-1]
            response["agent_reasoning"] = {
                "thought": last_reasoning.get("thought", ""),
                "action": last_reasoning.get("action", ""),
            }

        return response

    def _build_report_response(self, state: dict) -> dict:
        """构建最终报告响应"""
        report = state.get("report", {})
        return {
            "done": True,
            "report": report,
            "candidate_profile": state.get("candidate_profile", {}),
            "topic_performance": state.get("topic_performance", {}),
        }

    async def _create_session(
        self, session_id: str, skill_id: str, difficulty: str, questions: list[dict],
    ) -> None:
        """在数据库中创建面试会话记录"""
        try:
            from app.database.engine import async_session
            from app.models.interview import InterviewSessionEntity

            async with async_session() as db:
                session_entity = InterviewSessionEntity(
                    id=session_id,
                    user_id=session_id,  # 暂用 session_id 作为 user_id
                    skill_id=skill_id,
                    difficulty=difficulty,
                    total_questions=len(questions),
                    questions_json=json.dumps(questions, ensure_ascii=False),
                    agent_mode=self.agent_mode,
                )
                db.add(session_entity)
                await db.commit()
                log.info("面试会话已创建: %s", session_id)
        except Exception as e:
            log.error("创建会话记录失败: %s", e)
            raise
