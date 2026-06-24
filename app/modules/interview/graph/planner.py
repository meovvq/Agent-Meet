"""动态规划节点

面试前：LLM 根据简历、技能、历史画像制定面试策略。
面试中：Agent 可通过 update_strategy 工具实时调整。

策略影响：
- generate_question 节点根据 strategy.focus_topics 选题
- agent_route_decision 参考 strategy 做路由决策
- adjust_difficulty 工具参考 strategy.difficulty_direction
"""

import json
import logging

from app.common.llm_client import chat_completion_json
from app.common.prompt_loader import render_prompt
from app.modules.interview.graph.state import AgentState

log = logging.getLogger(__name__)

# ========== 规划提示词（从模板加载）==========

PLANNER_SYSTEM_PROMPT = """你是一位资深技术面试策略规划师。根据候选人的简历、目标技能和历史表现，制定一份面试策略。
严格返回 JSON：{"focus_topics":[],"skip_topics":[],"difficulty_direction":"keep","estimated_questions":8,"reasoning":"策略理由"}"""


# ========== 规划节点 ==========

async def plan_interview_strategy(state: AgentState) -> dict:
    """面试前策略规划

    在图启动后、第一道题之前执行。
    读取 state 中的简历和历史画像，生成面试策略。
    """
    skill_id = state.get("skill_id", "")
    difficulty = state.get("difficulty", "medium")
    resume_text = state.get("resume_text", "")
    candidate_profile = state.get("candidate_profile", {})

    # 构建简历摘要
    resume_section = resume_text[:1000] if resume_text else ""

    # 构建历史表现
    history_section = ""
    if candidate_profile:
        history_section = f"""候选人历史画像:
- 平均分: {candidate_profile.get('avg_score', 'N/A')}
- 擅长主题: {', '.join(candidate_profile.get('strong_topics', [])) or '暂无'}
- 薄弱主题: {', '.join(candidate_profile.get('weak_topics', [])) or '暂无'}
- 面试次数: {candidate_profile.get('interview_count', 0)}"""

    user_prompt = render_prompt(
        "agent_planner.j2",
        skill_id=skill_id,
        difficulty=difficulty,
        resume_section=resume_section,
        history_section=history_section,
    )

    try:
        result = await chat_completion_json(
            system_prompt=PLANNER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=1024,
        )

        # 提取策略字段
        strategy = {
            "focus_topics": result.get("focus_topics", []),
            "skip_topics": result.get("skip_topics", []),
            "difficulty_direction": result.get("difficulty_direction", "keep"),
            "estimated_questions": result.get("estimated_questions", 8),
            "reasoning": result.get("reasoning", ""),
        }

        log.info("面试策略已生成: %s", json.dumps(strategy, ensure_ascii=False))

        # 根据策略设置初始难度调整因子
        diff_dir = strategy.get("difficulty_direction", "keep")
        if diff_dir == "up":
            difficulty_adj = 1.2
        elif diff_dir == "down":
            difficulty_adj = 0.8
        else:
            difficulty_adj = 1.0

        return {
            "interview_strategy": strategy,
            "focus_topics": strategy.get("focus_topics", []),
            "difficulty_adjustment": difficulty_adj,
        }

    except Exception as e:
        log.error("策略规划失败: %s, 使用默认策略", e, exc_info=True)
        return {
            "interview_strategy": {
                "focus_topics": [],
                "skip_topics": [],
                "difficulty_direction": "keep",
                "reasoning": f"策略规划失败({e})，使用默认策略",
            },
            "difficulty_adjustment": 1.0,
        }
