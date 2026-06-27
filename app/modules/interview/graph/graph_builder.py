"""Agent 面试图构建与编译

提供两种图：
1. workflow_graph  — 工作流模式（原硬编码路由，作为 fallback）
2. agent_graph     — Agent 模式（LLM 自主决策）

Agent 图流程：
    START → load_memory → plan_strategy → present_question
        → wait_for_answer(interrupt) → evaluate_answer
        → update_agent_context → agent_route_decision:
            - save_and_advance → present_question (循环)
            - generate_follow_up → present_question (循环)
            - provide_hint → wait_for_answer (重试)
            - generate_report → save_memory → END
"""

import json
import logging

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.modules.interview.graph.state import AgentState

log = logging.getLogger(__name__)


# ========== 工作流模式节点（保留作为 fallback）==========

def present_question(state: AgentState) -> dict:
    """展示题目"""
    idx = state.get("current_index", 0)
    questions = state.get("questions", [])
    if idx >= len(questions):
        return {"action": "done"}
    return {"action": "present", "hint": ""}


def wait_for_answer(state: AgentState) -> dict:
    """等待用户回答（interrupt 暂停点）"""
    from langgraph.types import interrupt
    idx = state.get("current_index", 0)
    questions = state.get("questions", [])
    q = questions[idx] if idx < len(questions) else {}
    user_answer = interrupt({
        "question": q.get("question", ""),
        "question_index": idx,
        "category": q.get("category", ""),
        "is_follow_up": q.get("is_follow_up", False),
        "hint": state.get("hint", ""),
    })
    return {"current_answer": user_answer}


async def evaluate_answer(state: AgentState) -> dict:
    """LLM 评估答案（使用模板化的评估提示词 + 知识库参考材料）"""
    from app.common.llm_client import chat_completion_json
    from app.common.prompt_loader import render_prompt
    from app.modules.interview.knowledge_base import knowledge_base_service

    answer = state.get("current_answer", "")
    if not answer:
        return {"evaluation": {"score": 0, "feedback": "未作答"}, "action": "advance"}

    idx = state.get("current_index", 0)
    questions = state.get("questions", [])
    q = questions[idx] if idx < len(questions) else {}
    question_text = q.get("question", "")
    category = q.get("category", "")

    # 从知识库检索参考资料
    reference_section = ""
    try:
        reference_section = await knowledge_base_service.query_with_context(
            question=question_text,
            skill_id=state.get("skill_id", ""),
            top_k=3,
        )
    except Exception as e:
        log.warning("知识库检索失败，继续评估: %s", e)

    from app.common.llm_client import chat_completion_json
    try:
        user_prompt = render_prompt(
            "agent_evaluate_single.j2",
            category=category,
            difficulty=state.get("difficulty", "medium"),
            question=question_text,
            user_answer=answer,
            reference_section=reference_section,
            resume_text=state.get("resume_text", "")[:500] if state.get("resume_text") else "",
        )
        result = await chat_completion_json(
            system_prompt="你是技术面试评估专家。评估候选人的答案，返回 JSON 格式：{\"score\": 0-10, \"feedback\": \"评语\", \"referenceAnswer\": \"参考答案\", \"keyPoints\": [\"要点\"]}",
            user_prompt=user_prompt,
            temperature=0.3,
        )
        # 确保 score 在合理范围内
        score = result.get("score", 5)
        if not isinstance(score, (int, float)) or score < 0 or score > 10:
            score = 5
        result["score"] = score
        return {"evaluation": result, "action": "evaluate"}
    except Exception as e:
        log.error("评估失败: %s", e)
        return {"evaluation": {"score": 5, "feedback": f"评估异常: {e}"}, "action": "evaluate"}


async def save_and_advance(state: AgentState) -> dict:
    """保存答案到数据库并前进到下一题"""
    import json

    idx = state.get("current_index", 0)
    questions = state.get("questions", [])
    q = questions[idx] if idx < len(questions) else {}
    eval_result = state.get("evaluation", {})
    session_id = state.get("session_id", "")

    # 持久化答案到 InterviewAnswerEntity
    if session_id:
        try:
            from app.database.engine import async_session
            from app.models.interview import InterviewAnswerEntity, InterviewSessionEntity
            from sqlalchemy import select

            async with async_session() as db:
                # 写入单题答案记录
                answer_entity = InterviewAnswerEntity(
                    session_id=session_id,
                    question_index=idx,
                    question=q.get("question", ""),
                    category=q.get("category", ""),
                    is_follow_up=q.get("is_follow_up", False),
                    user_answer=state.get("current_answer", ""),
                    score=eval_result.get("score"),
                    feedback=eval_result.get("feedback"),
                    reference_answer=eval_result.get("referenceAnswer"),
                    key_points_json=json.dumps(eval_result.get("keyPoints", []), ensure_ascii=False),
                )
                db.add(answer_entity)

                # 更新 session 的 current_question_index
                stmt = select(InterviewSessionEntity).where(InterviewSessionEntity.id == session_id)
                result = await db.execute(stmt)
                session_obj = result.scalar_one_or_none()
                if session_obj:
                    session_obj.current_question_index = idx + 1

                await db.commit()
                log.info("答案已持久化: session=%s, question=%d", session_id, idx)
        except Exception as e:
            log.error("答案持久化失败: %s", e)

    return {"current_index": idx + 1}


async def generate_follow_up(state: AgentState) -> dict:
    """生成追问并插入题目列表"""
    from app.modules.interview.graph.tools import generate_follow_up_tool
    follow_up_text = await generate_follow_up_tool(state)
    idx = state.get("current_index", 0)
    questions = state.get("questions", [])

    new_q = {
        "question": follow_up_text,
        "category": questions[idx].get("category", "") if idx < len(questions) else "",
        "is_follow_up": True,
        "parent_question_index": idx,
    }
    questions.insert(idx + 1, new_q)

    follow_up_counts = state.get("follow_up_counts", {})
    follow_up_counts[str(idx)] = follow_up_counts.get(str(idx), 0) + 1

    return {
        "questions": questions,
        "current_index": idx + 1,
        "follow_up_counts": follow_up_counts,
        "evaluation": {},
        "current_answer": "",
    }


async def provide_hint(state: AgentState) -> dict:
    """生成提示"""
    from app.modules.interview.graph.tools import generate_hint_tool
    hint_text = await generate_hint_tool(state)
    return {"hint": hint_text, "current_answer": "", "evaluation": {}}


async def generate_report(state: AgentState) -> dict:
    """生成面试报告并持久化到数据库"""
    from app.common.prompt_loader import render_prompt

    profile = state.get("candidate_profile", {})
    topic_perf = state.get("topic_performance", {})

    all_scores = [s for scores in topic_perf.values() for s in scores]
    overall = sum(all_scores) / len(all_scores) if all_scores else 0

    # 构建 QA 摘要
    questions = state.get("questions", [])
    qa_summary_parts = []
    for i, q in enumerate(questions[:10]):
        qa_summary_parts.append(f"题目{i+1}: {q.get('question', '')[:50]}...")
    qa_summary = "\n".join(qa_summary_parts) if qa_summary_parts else "无"

    # 尝试使用 LLM 生成更详细的报告
    try:
        from app.common.llm_client import chat_completion_json
        user_prompt = render_prompt(
            "agent_memory_summary.j2",
            skill_id=state.get("skill_id", ""),
            difficulty=state.get("difficulty", "medium"),
            total_questions=len(all_scores),
            overall_score=round(overall, 1),
            topic_scores=json.dumps({t: round(sum(s) / len(s), 1) for t, s in topic_perf.items()}, ensure_ascii=False),
            strong_topics=", ".join(profile.get("strong_topics", [])) or "暂无",
            weak_topics=", ".join(profile.get("weak_topics", [])) or "暂无",
            qa_summary=qa_summary,
        )
        llm_report = await chat_completion_json(
            system_prompt="你是面试记录分析师，负责总结面试表现。返回 JSON 格式。",
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=2048,
        )
        report = {
            "overall_score": round(overall, 1),
            "strong_topics": profile.get("strong_topics", []),
            "weak_topics": profile.get("weak_topics", []),
            "total_questions": len(all_scores),
            "topic_scores": {t: round(sum(s) / len(s), 1) for t, s in topic_perf.items()},
            "llm_summary": llm_report,
        }
    except Exception as e:
        log.warning("LLM 报告生成失败，使用基础报告: %s", e)
        report = {
            "overall_score": round(overall, 1),
            "strong_topics": profile.get("strong_topics", []),
            "weak_topics": profile.get("weak_topics", []),
            "total_questions": len(all_scores),
            "topic_scores": {t: round(sum(s) / len(s), 1) for t, s in topic_perf.items()},
        }

    # 持久化报告到 session 表
    session_id = state.get("session_id", "")
    if session_id:
        try:
            from datetime import datetime, timezone

            from app.database.engine import async_session
            from app.models.interview import InterviewSessionEntity
            from sqlalchemy import select

            async with async_session() as db:
                stmt = select(InterviewSessionEntity).where(InterviewSessionEntity.id == session_id)
                result = await db.execute(stmt)
                session_obj = result.scalar_one_or_none()
                if session_obj:
                    session_obj.status = "EVALUATED"
                    session_obj.evaluate_status = "EVALUATED"
                    session_obj.overall_score = round(overall, 1)
                    session_obj.overall_feedback = report.get("llm_summary", {}).get("summary", "") if isinstance(report.get("llm_summary"), dict) else ""
                    session_obj.strengths_json = json.dumps(report.get("strong_topics", []), ensure_ascii=False)
                    session_obj.improvements_json = json.dumps(report.get("weak_topics", []), ensure_ascii=False)
                    session_obj.report_json = json.dumps(report, ensure_ascii=False)
                    session_obj.completed_at = datetime.now(timezone.utc)
                    await db.commit()
                    log.info("面试报告已持久化: session=%s, score=%.1f", session_id, overall)
        except Exception as e:
            log.error("报告持久化失败: %s", e)

    return {"report": report, "done": True}


# ========== 工作流模式路由 ==========

def workflow_route_decision(state: AgentState) -> str:
    """硬编码路由（原工作流模式）"""
    eval_result = state.get("evaluation", {})
    score = eval_result.get("score", 5)
    idx = state.get("current_index", 0)
    follow_up_counts = state.get("follow_up_counts", {})
    follow_up_count = follow_up_counts.get(str(idx), 0)

    if score >= 7:
        return "save_and_advance"
    elif score >= 4 and follow_up_count < 2:
        return "generate_follow_up"
    else:
        return "provide_hint"


# ========== 图构建 ==========

def build_workflow_graph() -> StateGraph:
    """构建工作流模式图（原硬编码路由，作为 fallback）"""
    graph = StateGraph(AgentState)

    graph.add_node("present_question", present_question)
    graph.add_node("wait_for_answer", wait_for_answer)
    graph.add_node("evaluate_answer", evaluate_answer)
    graph.add_node("save_and_advance", save_and_advance)
    graph.add_node("generate_follow_up", generate_follow_up)
    graph.add_node("provide_hint", provide_hint)
    graph.add_node("generate_report", generate_report)

    graph.add_edge(START, "present_question")
    graph.add_conditional_edges(
        "present_question",
        #条件判断与路由映射
        lambda s: "generate_report" if s.get("action") == "done" else "wait_for_answer",
        {"wait_for_answer": "wait_for_answer", "generate_report": "generate_report"},
    )
    #直接边，第一步直走出题-答题-打分
    graph.add_edge("wait_for_answer", "evaluate_answer")
    #条件边
    graph.add_conditional_edges("evaluate_answer", workflow_route_decision, {
        "save_and_advance": "save_and_advance",
        "generate_follow_up": "generate_follow_up",
        "provide_hint": "provide_hint",
    })
    graph.add_edge("save_and_advance", "present_question")
    graph.add_edge("generate_follow_up", "present_question")
    graph.add_edge("provide_hint", "wait_for_answer")
    graph.add_edge("generate_report", END)

    return graph


def build_agent_graph() -> StateGraph:
    """构建 Agent 模式图

    与工作流模式的区别：
    1. 启动时加载长期记忆（load_memory）
    2. 制定面试策略（plan_strategy）
    3. 评估后更新 Agent 上下文（update_agent_context）
    4. 路由由 LLM 自主决策（agent_route_decision）替代硬编码规则
    5. 结束时保存长期记忆（save_memory）

    注意：agent_route 同时充当"节点"和"路由函数"——
    LangGraph 的 add_conditional_edges 接受一个 callable，
    它接收 state 并返回目标节点名的字符串。
    agent_route_decision 正是这样的函数（async, 返回 str）。
    """
    from app.modules.interview.graph.agent import agent_route_decision, update_agent_context
    from app.modules.interview.graph.memory import load_memory, save_memory
    from app.modules.interview.graph.planner import plan_interview_strategy

    graph = StateGraph(AgentState)

    # 注册节点（注意：agent_route 不注册为节点，而是作为路由函数）
    graph.add_node("load_memory", load_memory)
    graph.add_node("plan_strategy", plan_interview_strategy)
    graph.add_node("present_question", present_question)
    graph.add_node("wait_for_answer", wait_for_answer)
    graph.add_node("evaluate_answer", evaluate_answer)
    graph.add_node("update_agent_context", update_agent_context)
    graph.add_node("save_and_advance", save_and_advance)
    graph.add_node("generate_follow_up", generate_follow_up)
    graph.add_node("provide_hint", provide_hint)
    graph.add_node("generate_report", generate_report)
    graph.add_node("save_memory", save_memory)

    # 边定义
    graph.add_edge(START, "load_memory")
    graph.add_edge("load_memory", "plan_strategy")
    graph.add_edge("plan_strategy", "present_question")

    # Agent 图的核心区别：present_question → wait_for_answer → evaluate_answer → update_agent_context → agent_route_decision
    #在这个方法下，只要到了这个节点，就必须按照这个模块内显示声明的路径来走；只要走到了"present_question"，下一步一定是"generate_report"/"wait_for_answer"
    graph.add_conditional_edges(
        "present_question",
        #状态为done则输出报告,否则继续等待回答
        lambda s: "generate_report" if s.get("action") == "done" else "wait_for_answer",
        {"wait_for_answer": "wait_for_answer", "generate_report": "generate_report"},
    )

    graph.add_edge("wait_for_answer", "evaluate_answer")
    graph.add_edge("evaluate_answer", "update_agent_context")

    # Agent 路由：update_agent_context → agent_route_decision（路由函数）→ 目标节点
    # agent_route_decision 是 async 函数，接收 state 返回路由字符串
    graph.add_conditional_edges(
        "update_agent_context",
        agent_route_decision,     # 直接作为路由函数，LLM 自主决策
        {
            "save_and_advance": "save_and_advance",
            "generate_follow_up": "generate_follow_up",
            "provide_hint": "provide_hint",
            "generate_report": "generate_report",
        },
    )

    graph.add_edge("save_and_advance", "present_question")
    graph.add_edge("generate_follow_up", "present_question")
    graph.add_edge("provide_hint", "wait_for_answer")
    graph.add_edge("generate_report", "save_memory")
    graph.add_edge("save_memory", END)

    return graph


# ========== 编译（全局单例）==========

_checkpointer = MemorySaver()

workflow_graph = build_workflow_graph().compile(checkpointer=_checkpointer)
log.info("工作流模式图已编译")

agent_graph = build_agent_graph().compile(checkpointer=_checkpointer)
log.info("Agent 模式图已编译")
