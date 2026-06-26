"""Agent 节点 —— ReAct 循环核心

替代原工作流中的硬编码 route_decision，
让 LLM 根据面试上下文自主选择下一步动作。

ReAct 循环：Thought → Action → Observation → Thought → ...
Agent 在每一步可以：
  1. 直接决定路由（save_and_advance / generate_follow_up / provide_hint）
  2. 调用工具获取更多信息，再做决策
"""

import json
import logging

from openai.types.chat import ChatCompletionMessageFunctionToolCall

from app.common.llm_client import chat_completion_with_tools
from app.common.prompt_loader import render_prompt
from app.modules.interview.graph.state import AgentState
from app.modules.interview.graph.tools import (
    execute_tool,
    get_available_tools,
    get_tools_schema,
)

log = logging.getLogger(__name__)

# ========== Agent 系统提示词 ==========

def _get_agent_system_prompt(tools_description: str) -> str:
    """从模板加载 Agent 系统提示词"""
    return render_prompt("agent_system.j2", tools_description=tools_description)

# 路由映射：工具名 → 图路由名
_ACTION_TO_ROUTE = {
    "generate_follow_up": "generate_follow_up",
    "generate_hint": "provide_hint",
    "skip_question": "save_and_advance",
    "end_interview": "generate_report",
    "adjust_difficulty": "save_and_advance",
    "update_strategy": "save_and_advance",
    "query_knowledge_base": None,       # 中间工具，不直接路由
    "analyze_resume": None,             # 中间工具，不直接路由
}

# 不需要路由的工具（执行后继续推理）
_INTERMEDIATE_TOOLS = {"query_knowledge_base", "analyze_resume"}


# ========== Agent 决策节点 ==========

async def agent_route_decision(state: AgentState) -> str:
    """Agent 自主决策路由

    替代原工作流中的 route_decision(state) -> str。
    LLM 根据完整上下文选择下一步动作。

    返回值：图路由名（save_and_advance / generate_follow_up / provide_hint / generate_report）
    """
    eval_result = state.get("evaluation", {})
    score = eval_result.get("score", 5)
    idx = state.get("current_index", 0)
    questions = state.get("questions", [])

    #如果所有题目完成，直接生成报告
    if idx >= len(questions):
        return "generate_report"

     # q = questions[idx]：获取当前题目
     # max_steps = state.get("max_reasoning_steps", 3)：获取 ReAct 循环的最大步数（默认 3）
     # history = state.get("agent_history", [])：获取 Agent 的推理历史
    q = questions[idx]
    max_steps = state.get("max_reasoning_steps", 3)
    history = state.get("agent_history", [])

    # 构建决策上下文
    context = _build_decision_context(state)

    # 获取工具 schema（排除不适合决策阶段的工具）
    decision_tools = [t for t in get_available_tools() if t not in {"query_knowledge_base", "analyze_resume"}]
    tools_schema = get_tools_schema(decision_tools)

    # 工具描述（给 system prompt 用）
    tools_desc = "\n".join(
        f"- `{t}`: {_tool_registry_desc(t)}"
        for t in decision_tools
    )

    # ReAct 循环
    for step in range(max_steps):
        log.info("Agent 决策 step %d/%d, 题目 %d, 分数 %s", step + 1, max_steps, idx, score)

        system_prompt = _get_agent_system_prompt(tools_desc)
        response = await chat_completion_with_tools(
            system_prompt=system_prompt,
            user_prompt=f"当前面试状态：\n{context}\n\n请决定下一步行动。",
            tools=tools_schema if tools_schema else None,
            tool_choice="auto" if step < max_steps - 1 else "none",  # 最后一步强制决策
        )

        # 无 tool call → Agent 决定直接通过
        if not response.tool_calls:
            thought = response.content or "直接进入下一题"
            _record_reasoning(state, thought, "direct_pass", {}, "无需额外操作")
            log.info("Agent 决策: 直接通过, thought=%s", thought[:100])
            return "save_and_advance"

        # 有 tool call → 执行工具
        tool_call: ChatCompletionMessageFunctionToolCall = response.tool_calls[0]  # 类型注解，IDE 可以正确推断
        action: str = tool_call.function.name  # 工具名称（如 "generate_follow_up"）
        arguments: dict = json.loads(tool_call.function.arguments)  # 工具参数（JSON 字符串转字典）
        thought: str = response.content or f"调用 {action}"  # LLM 的思考内容

        log.info("Agent 选择工具: %s, 参数: %s", action, json.dumps(arguments, ensure_ascii=False))

        # 执行工具
        observation = await execute_tool(action, arguments, state)
        _record_reasoning(state, thought, action, arguments, observation)

        # 中间工具 → 继续推理
        if action in _INTERMEDIATE_TOOLS:
            context += f"\n\n[{action} 结果]: {observation}"
            continue

        # 终端工具 → 返回路由
        route = _ACTION_TO_ROUTE.get(action)
        if route:
            log.info("Agent 路由: %s -> %s", action, route)
            return route

        # 未知工具 → fallback
        log.warning("Agent 未知工具: %s, fallback 到 save_and_advance", action)
        return "save_and_advance"

    # 循环耗尽 → fallback
    log.warning("Agent 决策步数耗尽 (%d), fallback 到 save_and_advance", max_steps)
    return "save_and_advance"


# ========== 辅助函数 ==========

def _build_decision_context(state: AgentState) -> str:
    """构建给 LLM 的决策上下文（从模板渲染）"""
    idx = state.get("current_index", 0)
    questions = state.get("questions", [])
    q = questions[idx] if idx < len(questions) else {}
    eval_result = state.get("evaluation", {})
    answer = state.get("current_answer", "")

    # 候选人画像
    profile = state.get("candidate_profile", {})
    profile_str = json.dumps(profile, ensure_ascii=False) if profile else "暂无"

    # 策略
    strategy = state.get("interview_strategy", {})
    strategy_str = json.dumps(strategy, ensure_ascii=False) if strategy else "暂无"

    # 最近分数
    recent = state.get("recent_scores", [])
    recent_str = ", ".join(f"{s:.1f}" for s in recent[-5:]) if recent else "暂无"

    # 追问次数
    follow_ups = state.get("follow_up_counts", {})
    follow_up_count = follow_ups.get(str(idx), 0)

    # 难度调整
    difficulty_adj = state.get("difficulty_adjustment", 1.0)

    return render_prompt(
        "agent_decision_context.j2",
        question_index=idx,
        total_questions=len(questions),
        question=q.get("question", "N/A"),
        category=q.get("category", "N/A"),
        is_follow_up=q.get("is_follow_up", False),
        answer=answer[:300],
        score=eval_result.get("score", "N/A"),
        feedback=eval_result.get("feedback", "")[:200],
        follow_up_count=follow_up_count,
        recent_scores=recent_str,
        difficulty_adj=f"{difficulty_adj:.2f}",
        consecutive_high=state.get("consecutive_high", 0),
        consecutive_low=state.get("consecutive_low", 0),
        profile_str=profile_str,
        strategy_str=strategy_str,
    )


def _record_reasoning(state: AgentState, thought: str, action: str,
                      action_input: dict, observation: str):
    """记录 Agent 推理步骤"""
    history = state.get("agent_history", [])
    history.append({
        "thought": thought,
        "action": action,
        "action_input": action_input,
        "observation": observation,
    })
    state["agent_history"] = history


def _tool_registry_desc(tool_name: str) -> str:
    """获取工具描述（从注册表）"""
    from app.modules.interview.graph.tools import _tool_registry
    tool = _tool_registry.get(tool_name)
    return tool["description"] if tool else "未知工具"


# ========== 评估后上下文更新节点 ==========

async def update_agent_context(state: AgentState) -> dict:
    """评估完成后更新 Agent 上下文（短期记忆）

    在 evaluate_answer 之后、agent_route_decision 之前调用，
    更新候选人画像、主题表现、连续分数等。
    """
    eval_result = state.get("evaluation", {})
    score = eval_result.get("score", 0)
    idx = state.get("current_index", 0)
    questions = state.get("questions", [])
    q = questions[idx] if idx < len(questions) else {}
    category = q.get("category", "unknown")

    # 更新主题表现
    topic_perf = state.get("topic_performance", {})
    if category not in topic_perf:
        topic_perf[category] = []
    topic_perf[category].append(score)
    state["topic_performance"] = topic_perf

    # 更新最近分数
    recent = state.get("recent_scores", [])
    recent.append(score)
    state["recent_scores"] = recent[-5:]  # 保留最近 5 题

    # 更新连续高/低分
    if score >= 7:
        state["consecutive_high"] = state.get("consecutive_high", 0) + 1
        state["consecutive_low"] = 0
    elif score < 4:
        state["consecutive_low"] = state.get("consecutive_low", 0) + 1
        state["consecutive_high"] = 0
    else:
        state["consecutive_high"] = 0
        state["consecutive_low"] = 0

    # 更新候选人画像
    all_scores = [s for scores in topic_perf.values() for s in scores]
    profile = state.get("candidate_profile", {})
    profile["avg_score"] = sum(all_scores) / len(all_scores) if all_scores else 0
    profile["strong_topics"] = [t for t, s in topic_perf.items() if sum(s) / len(s) >= 7]
    profile["weak_topics"] = [t for t, s in topic_perf.items() if sum(s) / len(s) < 5]
    profile["total_answered"] = len(all_scores)
    state["candidate_profile"] = profile

    log.info("Agent 上下文更新: score=%.1f, category=%s, profile=%s",
             score, category, json.dumps(profile, ensure_ascii=False))

    return {}
