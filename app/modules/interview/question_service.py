"""面试出题服务

支持两种模式：
1. 无简历：纯方向出题（按 Skill 分类分配）
2. 有简历：60% 简历 + 40% 方向（并发出题）
"""

import asyncio
import json
import logging

from app.common.llm_client import chat_completion_json
from app.common.prompt_loader import render_prompt
from app.modules.interview.skill_service import skill_service

log = logging.getLogger(__name__)

DIFFICULTY_MAP = {
    "easy": "初级（1-2 年经验）",
    "medium": "中级（3-5 年经验）",
    "hard": "高级（5 年以上经验）",
}


async def generate_questions(
    skill_id: str,
    difficulty: str = "medium",
    question_count: int = 5,
    resume_text: str = "",
    follow_up_count: int = 2,
    historical: list[dict] | None = None,
) -> list[dict]:
    """生成面试题目

    Args:
        skill_id: 技能方向 ID
        difficulty: 难度 (easy/medium/hard)
        question_count: 题目数量
        resume_text: 简历文本（可选）
        follow_up_count: 每题追问数
        historical: 历史题目（用于去重）

    Returns:
        题目列表 [{"question": "...", "category": "...", "type": "...", "topicSummary": "..."}]
    """
    log.info("生成面试题目: skill=%s, count=%d, difficulty=%s", skill_id, question_count, difficulty)
    skill = skill_service.get_skill(skill_id)
    persona = skill_service.get_persona(skill_id)

    historical = historical or []

    if resume_text:
        return await _generate_with_resume(
            skill_id, skill, persona, difficulty, question_count,
            resume_text, follow_up_count, historical,
        )
    else:
        return await _generate_without_resume(
            skill_id, skill, persona, difficulty, question_count,
            follow_up_count, historical,
        )


async def _generate_without_resume(
    skill_id: str, skill: dict, persona: str,
    difficulty: str, question_count: int,
    follow_up_count: int, historical: list[dict],
) -> list[dict]:
    """无简历模式出题"""
    allocation = skill_service.calculate_allocation(skill_id, question_count)

    allocation_table = "\n".join(
        f"| {a['label']} | {a['count']} | {'参考 ' + a['ref'] if a.get('ref') else ''} |"
        for a in allocation
    )

    reference_section = _build_reference_section(skill_id, allocation)
    historical_section = _build_historical_section(historical)

    system_prompt = render_prompt("interview_question_skill_system.j2")
    user_prompt = render_prompt(
        "interview_question_skill_user.j2",
        question_count=question_count,
        follow_up_count=follow_up_count,
        difficulty_description=DIFFICULTY_MAP.get(difficulty, "中级"),
        skill_name=skill.get("name", ""),
        skill_description=skill.get("description", ""),
        allocation_table=allocation_table,
        historical_section=historical_section,
        reference_section=reference_section,
    )

    system_prompt = persona + "\n\n" + system_prompt

    result = await chat_completion_json(system_prompt, user_prompt)
    return _parse_questions(result, question_count)


async def _generate_with_resume(
    skill_id: str, skill: dict, persona: str,
    difficulty: str, question_count: int,
    resume_text: str, follow_up_count: int,
    historical: list[dict],
) -> list[dict]:
    """有简历模式出题（60% 简历 + 40% 方向）"""
    resume_count = int(question_count * 0.6)
    skill_count = question_count - resume_count

    historical_section = _build_historical_section(historical)

    async def gen_resume_questions():
        system_prompt = render_prompt("interview_question_resume_system.j2")
        user_prompt = render_prompt(
            "interview_question_resume_user.j2",
            question_count=resume_count,
            follow_up_count=follow_up_count,
            skill_name=skill.get("name", ""),
            skill_description=skill.get("description", ""),
            difficulty_description=DIFFICULTY_MAP.get(difficulty, "中级"),
            resume_text=resume_text,
            historical_section=historical_section,
        )
        result = await chat_completion_json(persona + "\n\n" + system_prompt, user_prompt)
        return _parse_questions(result, resume_count)

    async def gen_skill_questions():
        allocation = skill_service.calculate_allocation(skill_id, skill_count)
        allocation_table = "\n".join(
            f"| {a['label']} | {a['count']} | |" for a in allocation
        )
        reference_section = _build_reference_section(skill_id, allocation)

        system_prompt = render_prompt("interview_question_skill_system.j2")
        user_prompt = render_prompt(
            "interview_question_skill_user.j2",
            question_count=skill_count,
            follow_up_count=follow_up_count,
            difficulty_description=DIFFICULTY_MAP.get(difficulty, "中级"),
            skill_name=skill.get("name", ""),
            skill_description=skill.get("description", ""),
            allocation_table=allocation_table,
            historical_section=historical_section,
            reference_section=reference_section,
        )
        result = await chat_completion_json(persona + "\n\n" + system_prompt, user_prompt)
        return _parse_questions(result, skill_count)

    resume_qs, skill_qs = await asyncio.gather(
        gen_resume_questions(), gen_skill_questions(), return_exceptions=True,
    )

    questions = []
    if isinstance(resume_qs, list):
        questions.extend(resume_qs)
    if isinstance(skill_qs, list):
        questions.extend(skill_qs)

    if not questions:
        log.error("出题全部失败，使用降级题目")
        return _fallback_questions(question_count)

    return questions[:question_count]


def _parse_questions(data: dict, expected_count: int) -> list[dict]:
    """解析 LLM 返回的题目"""
    raw_questions = data.get("questions", [])
    questions = []

    for i, q in enumerate(raw_questions[:expected_count]):
        questions.append({
            "question": q.get("question", ""),
            "type": q.get("type", ""),
            "category": q.get("category", ""),
            "topicSummary": q.get("topicSummary", q.get("topic_summary", "")),
            "followUps": q.get("followUps", []),
        })

    return questions


def _build_reference_section(skill_id: str, allocation: list[dict]) -> str:
    """构建参考资料（总上限 12000 字符）"""
    sections = []
    total_size = 0
    max_total = 12000

    for a in allocation:
        ref_file = a.get("ref")
        if not ref_file:
            continue
        content = skill_service.load_reference(skill_id, ref_file, a.get("shared", False))
        if content and total_size + len(content) < max_total:
            sections.append(f"### {a['label']}\n{content}")
            total_size += len(content)

    return "\n\n".join(sections) if sections else "无"


def _build_historical_section(historical: list[dict]) -> str:
    """构建历史去重文本"""
    if not historical:
        return "无"

    lines = []
    for h in historical:
        lines.append(f"- [{h.get('type', '')}] {h.get('topicSummary', h.get('question', ''))}")
    return "\n".join(lines)


def _fallback_questions(count: int) -> list[dict]:
    """降级题目"""
    topics = ["Java 核心", "数据库设计", "缓存策略", "系统架构", "项目经验"]
    return [
        {
            "question": f"请介绍一下你对 {topic} 的理解？",
            "type": "GENERAL",
            "category": "通用",
            "topicSummary": topic,
            "followUps": [],
        }
        for topic in topics[:count]
    ]
