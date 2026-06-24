"""Agent 工具系统

提供工具注册、执行和 OpenAI function calling schema 生成。
工具通过 @interview_tool 装饰器注册，Agent 通过 tool calling 自主调用。

设计原则：
- 工具是原子操作，每个工具完成一个明确的任务
- 工具内部自带 try-except 降级，不向上抛异常
- 工具通过修改 state 或返回字符串来影响面试流程
"""

import inspect
import json
import logging
from typing import Callable

from app.common.llm_client import chat_completion, chat_completion_json
from app.common.prompt_loader import render_prompt

log = logging.getLogger(__name__)

# ========== 全局工具注册表 ==========

_tool_registry: dict[str, dict] = {}


def interview_tool(name: str, description: str):
    """面试工具装饰器

    用法：
        @interview_tool("adjust_difficulty", "调整面试难度")
        async def adjust_difficulty(state: dict, direction: str = "up") -> str:
            ...
    """
    def decorator(func: Callable):
        sig = inspect.signature(func)
        parameters = _build_parameters_schema(sig, skip_params={"state"})
        _tool_registry[name] = {
            "name": name,
            "description": description,
            "function": func,
            "parameters": parameters,
        }
        log.info("注册工具: %s", name)
        return func
    return decorator


def _build_parameters_schema(sig: inspect.Signature, skip_params: set[str] = None) -> dict:
    """从函数签名生成 OpenAI function calling parameters schema"""
    skip_params = skip_params or set()
    properties = {}
    required = []
    type_map = {"str": "string", "int": "integer", "float": "number", "bool": "boolean"}

    for name, param in sig.parameters.items():
        if name in skip_params:
            continue
        type_name = param.annotation.__name__ if param.annotation != inspect.Parameter.empty else "string"
        properties[name] = {
            "type": type_map.get(type_name, "string"),
            "description": f"参数: {name}",
        }
        if param.default is inspect.Parameter.empty:
            required.append(name)

    return {"type": "object", "properties": properties, "required": required}


# ========== Schema 获取 ==========

def get_tools_schema(tool_names: list[str] | None = None) -> list[dict]:
    """生成 OpenAI function calling 格式的 tools schema"""
    names = tool_names or list(_tool_registry.keys())
    return [
        {
            "type": "function",
            "function": {
                "name": _tool_registry[n]["name"],
                "description": _tool_registry[n]["description"],
                "parameters": _tool_registry[n]["parameters"],
            }
        }
        for n in names if n in _tool_registry
    ]


def get_available_tools() -> list[str]:
    """返回所有已注册的工具名"""
    return list(_tool_registry.keys())


# ========== 工具执行 ==========

async def execute_tool(name: str, arguments: dict, state: dict) -> str:
    """执行工具并返回结果字符串

    工具内部异常被捕获并返回错误信息，不会中断图执行。
    """
    tool = _tool_registry.get(name)
    if not tool:
        return f"Error: 未知工具 '{name}'"
    try:
        result = await tool["function"](state=state, **arguments)
        log.info("工具执行: %s, 结果长度=%d", name, len(str(result)))
        return str(result)
    except Exception as e:
        log.error("工具执行失败: %s, error=%s", name, e, exc_info=True)
        return f"Error: 工具 '{name}' 执行失败 - {str(e)}"


# ========== 内置工具 ==========

@interview_tool("adjust_difficulty", "根据候选人表现调整后续题目难度")
async def adjust_difficulty(state: dict, direction: str = "up", reason: str = "") -> str:
    """direction: "up" 提高难度, "down" 降低难度"""
    current = state.get("difficulty_adjustment", 1.0)
    if direction == "up":
        new_adj = min(current * 1.3, 2.0)
    else:
        new_adj = max(current * 0.7, 0.5)
    state["difficulty_adjustment"] = new_adj
    log.info("难度调整: %.2f -> %.2f (%s)", current, new_adj, direction)
    return f"难度已{'提高' if direction == 'up' else '降低'}，调整因子: {new_adj:.2f}"


@interview_tool("skip_question", "跳过当前题目，进入下一题")
async def skip_question(state: dict, reason: str = "") -> str:
    idx = state.get("current_index", 0)
    questions = state.get("questions", [])
    if idx < len(questions):
        state["current_index"] = idx + 1
        return f"已跳过题目 {idx + 1}，原因: {reason}"
    return "已经是最后一题，无法跳过"


@interview_tool("end_interview", "提前结束面试，进入报告生成阶段")
async def end_interview(state: dict, reason: str = "") -> str:
    state["done"] = True
    state["action"] = "done"
    return f"面试已提前结束，原因: {reason}"


@interview_tool("update_strategy", "更新面试策略，调整后续题目方向和重点")
async def update_strategy(state: dict, focus_topics: str = "", skip_topics: str = "",
                          difficulty_direction: str = "", notes: str = "") -> str:
    """focus_topics / skip_topics: 逗号分隔的关键词"""
    strategy = state.get("interview_strategy", {})
    if focus_topics:
        strategy["focus_topics"] = [t.strip() for t in focus_topics.split(",")]
    if skip_topics:
        strategy["skip_topics"] = [t.strip() for t in skip_topics.split(",")]
    if difficulty_direction:
        strategy["difficulty_direction"] = difficulty_direction
    if notes:
        strategy["notes"] = notes
    state["interview_strategy"] = strategy
    return f"策略已更新: {json.dumps(strategy, ensure_ascii=False)}"


@interview_tool("query_knowledge_base", "查询技能知识库获取参考资料（支持 kb_id 过滤）")
async def query_knowledge_base(state: dict, query: str, top_k: int = 3, kb_ids: str = "") -> str:
    """通过 RAG 向量检索知识库，用于评估答案或生成追问。

    kb_ids: 逗号分隔的知识库 ID 列表，为空时检索全部。
    """
    log.info("知识库查询: query=%s, top_k=%d, kb_ids=%s", query, top_k, kb_ids)

    try:
        from app.modules.knowledgebase.vector_service import VectorService

        parsed_ids = [int(x.strip()) for x in kb_ids.split(",") if x.strip()] if kb_ids else None
        docs = await VectorService().similarity_search(query=query, kb_ids=parsed_ids, top_k=top_k)

        if not docs:
            return "知识库中未找到相关资料"

        parts = []
        for i, doc in enumerate(docs, 1):
            parts.append(f"[来源{i}] (相关度: {doc['score']:.2f})\n{doc['content']}")
        return "\n\n".join(parts)
    except Exception as e:
        log.warning("知识库查询失败: %s", e)
        return f"知识库查询失败: {e}"


@interview_tool("analyze_resume", "分析候选人简历，提取与当前技能相关的关键信息")
async def analyze_resume(state: dict, focus_area: str = "", resume_id: str = "") -> str:
    """通过 LLM 分析简历，提取与目标技能相关的经验。

    resume_id: 可选，指定简历 ID 从数据库读取；为空时使用 state 中的 resume_text。
    """
    resume_text = state.get("resume_text", "")

    # 如果指定了 resume_id，从数据库读取
    if resume_id:
        try:
            from app.database.engine import async_session
            from app.models.resume import ResumeEntity
            from sqlalchemy import select
            async with async_session() as db:
                result = await db.execute(select(ResumeEntity).where(ResumeEntity.id == int(resume_id)))
                resume = result.scalar_one_or_none()
                if resume and resume.resume_text:
                    resume_text = resume.resume_text
        except Exception as e:
            log.warning("读取简历失败: %s", e)

    if not resume_text:
        return "未提供简历"

    skill_id = state.get("skill_id", "")
    user_prompt = render_prompt(
        "agent_resume_analysis.j2",
        skill_id=skill_id,
        focus_area=focus_area,
        resume_text=resume_text[:2000],
    )
    try:
        result = await chat_completion_json(
            system_prompt="你是技术招聘专家，从简历中提取关键信息。返回 JSON 格式。",
            user_prompt=user_prompt, temperature=0.3, max_tokens=1024,
        )
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return f"简历分析失败: {e}"


@interview_tool("generate_follow_up", "基于候选人答案生成追问")
async def generate_follow_up_tool(state: dict, context: str = "", depth: str = "medium") -> str:
    """基于候选人答案和评估结果，生成追问问题"""
    idx = state.get("current_index", 0)
    questions = state.get("questions", [])
    if idx >= len(questions):
        return "没有当前题目"
    q = questions[idx]
    answer = state.get("current_answer", "")
    eval_result = state.get("evaluation", {})

    user_prompt = render_prompt(
        "agent_follow_up.j2",
        category=q.get("category", ""),
        question=q.get("question", ""),
        user_answer=answer[:500],
        score=eval_result.get("score", 5),
        feedback=eval_result.get("feedback", ""),
        context=context,
    )
    try:
        return await chat_completion(
            system_prompt="你是技术面试官，通过追问深入了解候选人理解程度。直接返回追问文本。",
            user_prompt=user_prompt, temperature=0.7, max_tokens=512,
        )
    except Exception as e:
        return f"追问生成失败: {e}"


@interview_tool("generate_hint", "为候选人生成引导性提示")
async def generate_hint_tool(state: dict, hint_level: str = "gentle") -> str:
    """根据候选人回答情况，生成引导性提示"""
    idx = state.get("current_index", 0)
    questions = state.get("questions", [])
    if idx >= len(questions):
        return "没有当前题目"
    q = questions[idx]
    answer = state.get("current_answer", "")
    eval_result = state.get("evaluation", {})

    user_prompt = render_prompt(
        "agent_hint.j2",
        category=q.get("category", ""),
        question=q.get("question", ""),
        user_answer=answer[:300],
        score=eval_result.get("score", 0),
        feedback=eval_result.get("feedback", ""),
        hint_level=hint_level,
    )
    try:
        return await chat_completion(
            system_prompt="你善于引导候选人展现真实水平。直接返回提示文本。",
            user_prompt=user_prompt, temperature=0.5, max_tokens=256,
        )
    except Exception as e:
        return f"提示生成失败: {e}"


log.info("工具系统已加载，注册 %d 个工具: %s", len(_tool_registry), list(_tool_registry.keys()))
