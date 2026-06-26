"""Agent Meet MCP Server

将面试系统的核心能力通过 MCP 协议暴露给外部 AI 客户端。

暴露的工具：
  - list_skills              列出所有面试方向
  - generate_questions       LLM 生成面试题
  - query_knowledge_base     RAG 混合检索知识库
  - analyze_resume_text      分析简历
  - generate_follow_up       生成追问
  - generate_hint            生成提示

运行方式：
  python -m app.mcp.server                              # stdio（Claude Desktop 默认）
  python -m app.mcp.server --transport streamable-http  # HTTP 远程
"""

import argparse
import json
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# 确保项目根目录在 sys.path 中（standalone 运行时需要）
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from mcp.server.fastmcp import FastMCP

log = logging.getLogger(__name__)

# ========== Lifespan：初始化数据库和依赖 ==========


@asynccontextmanager
async def lifespan(server: FastMCP):
    """MCP Server 生命周期：启动时初始化 DB，关闭时清理"""
    from app.database.engine import engine

    log.info("MCP Server 启动，初始化数据库连接...")
    # engine 在模块导入时已创建，这里只做确认
    yield
    log.info("MCP Server 关闭")
    await engine.dispose()


# ========== 创建 MCP Server ==========

mcp = FastMCP(
    "Agent Meet Interview Tools",
    instructions="AI 模拟面试系统的工具集：出题、检索知识库、分析简历、生成追问和提示",
    lifespan=lifespan,
)


# ========== 工具：列出面试方向 ==========


@mcp.tool()
async def list_skills() -> str:
    """列出所有可用的面试技能方向（如 Java 后端、Python、前端、系统设计等）。

    返回 JSON 数组，每项包含 id、name、description。
    在出题前调用此工具获取可用的 skill_id。
    """
    from app.modules.interview.skill_service import skill_service

    skills = skill_service.list_skills()
    return json.dumps(skills, ensure_ascii=False, indent=2)


# ========== 工具：生成面试题 ==========


@mcp.tool()
async def generate_questions(
    skill_id: str,
    difficulty: str = "medium",
    question_count: int = 5,
    resume_text: str = "",
) -> str:
    """根据技能方向和难度，使用 LLM 生成面试题目。

    Args:
        skill_id: 技能方向 ID（如 "java-backend"、"python-backend"），通过 list_skills 获取
        difficulty: 难度 — "easy"（初级）、"medium"（中级）、"hard"（高级）
        question_count: 生成题目数量，默认 5
        resume_text: 候选人简历文本（可选），传入后会结合简历出题

    Returns:
        JSON 数组，每项包含 question、category、type、topicSummary
    """
    from app.modules.interview.question_service import generate_questions as _gen

    questions = await _gen(
        skill_id=skill_id,
        difficulty=difficulty,
        question_count=question_count,
        resume_text=resume_text,
    )
    return json.dumps(questions, ensure_ascii=False, indent=2)


# ========== 工具：知识库检索 ==========


@mcp.tool()
async def query_knowledge_base(
    query: str,
    kb_ids: list[int] | None = None,
    top_k: int = 5,
) -> str:
    """从知识库中检索与查询相关的参考资料（向量 + BM25 混合检索）。

    适用于：查找面试题的参考答案、检索技术文档、验证候选人回答的正确性。

    Args:
        query: 查询文本（如 "ConcurrentHashMap 原理"）
        kb_ids: 知识库 ID 列表（为空时检索全部）
        top_k: 返回结果数量，默认 5

    Returns:
        JSON 对象，包含 results 数组（每项有 content 和 score）和 formatted 文本
    """
    from app.modules.knowledgebase.vector_service import VectorService

    docs = await VectorService().similarity_search(
        query=query,
        kb_ids=kb_ids,
        top_k=top_k,
    )

    if not docs:
        return json.dumps({"results": [], "formatted": "知识库中未找到相关资料"}, ensure_ascii=False)

    formatted_parts = []
    for i, doc in enumerate(docs, 1):
        formatted_parts.append(f"[来源{i}] (相关度: {doc['score']:.2f})\n{doc['content']}")

    return json.dumps(
        {
            "results": docs,
            "formatted": "\n\n".join(formatted_parts),
        },
        ensure_ascii=False,
        indent=2,
    )


# ========== 工具：分析简历 ==========


@mcp.tool()
async def analyze_resume_text(
    resume_text: str,
    skill_id: str = "",
    focus_area: str = "",
) -> str:
    """分析候选人简历，提取与目标技能相关的关键信息。

    Args:
        resume_text: 简历全文文本
        skill_id: 目标技能方向（如 "java-backend"），用于聚焦分析
        focus_area: 重点关注领域（如 "项目经验"、"技术栈"）

    Returns:
        JSON 对象，包含提取的关键信息（技能、项目、经验等）
    """
    from app.common.llm_client import chat_completion_json
    from app.common.prompt_loader import render_prompt

    user_prompt = render_prompt(
        "agent_resume_analysis.j2",
        skill_id=skill_id,
        focus_area=focus_area,
        resume_text=resume_text[:2000],
    )

    try:
        result = await chat_completion_json(
            system_prompt="你是技术招聘专家，从简历中提取关键信息。返回 JSON 格式。",
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=1024,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": f"简历分析失败: {e}"}, ensure_ascii=False)


# ========== 工具：生成追问 ==========


@mcp.tool()
async def generate_follow_up_question(
    question: str,
    user_answer: str,
    category: str = "",
    score: float = 5.0,
    feedback: str = "",
) -> str:
    """基于候选人的回答生成追问问题，用于深入了解其理解程度。

    Args:
        question: 原始面试题
        user_answer: 候选人的回答文本
        category: 题目分类（如 "JVM"、"并发"）
        score: 候选人回答的评分（0-10）
        feedback: 对候选人回答的简要评价

    Returns:
        追问问题文本
    """
    from app.common.llm_client import chat_completion
    from app.common.prompt_loader import render_prompt

    user_prompt = render_prompt(
        "agent_follow_up.j2",
        category=category,
        question=question,
        user_answer=user_answer[:500],
        score=score,
        feedback=feedback,
        context="",
    )

    try:
        result = await chat_completion(
            system_prompt="你是技术面试官，通过追问深入了解候选人理解程度。直接返回追问文本。",
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=512,
        )
        return result
    except Exception as e:
        return f"追问生成失败: {e}"


# ========== 工具：生成提示 ==========


@mcp.tool()
async def generate_hint_for_question(
    question: str,
    user_answer: str = "",
    category: str = "",
    score: float = 0.0,
    feedback: str = "",
    hint_level: str = "gentle",
) -> str:
    """为候选人生成引导性提示，帮助其展现真实水平。

    Args:
        question: 当前面试题
        user_answer: 候选人当前回答（可为空）
        category: 题目分类
        score: 当前评分（0-10）
        feedback: 评价
        hint_level: 提示力度 — "gentle"（温和引导）、"direct"（直接点拨）

    Returns:
        提示文本
    """
    from app.common.llm_client import chat_completion
    from app.common.prompt_loader import render_prompt

    user_prompt = render_prompt(
        "agent_hint.j2",
        category=category,
        question=question,
        user_answer=user_answer[:300],
        score=score,
        feedback=feedback,
        hint_level=hint_level,
    )

    try:
        result = await chat_completion(
            system_prompt="你善于引导候选人展现真实水平。直接返回提示文本。",
            user_prompt=user_prompt,
            temperature=0.5,
            max_tokens=256,
        )
        return result
    except Exception as e:
        return f"提示生成失败: {e}"


# ========== 入口 ==========


def main():
    parser = argparse.ArgumentParser(description="Agent Meet MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
        help="传输方式（默认 stdio）",
    )
    parser.add_argument("--host", default="0.0.0.0", help="HTTP 监听地址")
    parser.add_argument("--port", type=int, default=8001, help="HTTP 监听端口")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.transport == "stdio":
        log.info("MCP Server 启动（stdio 模式）")
        mcp.run(transport="stdio")
    else:
        log.info("MCP Server 启动（%s 模式，%s:%d）", args.transport, args.host, args.port)
        mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
