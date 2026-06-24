"""工具系统单元测试

测试各个工具的独立功能，使用 mock 隔离外部依赖。
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.interview.graph.tools import (
    _tool_registry,
    adjust_difficulty,
    end_interview,
    execute_tool,
    generate_follow_up_tool,
    generate_hint_tool,
    get_available_tools,
    get_tools_schema,
    query_knowledge_base,
    skip_question,
    update_strategy,
)


# ========== Fixtures ==========

@pytest.fixture
def sample_state():
    """示例面试状态"""
    return {
        "session_id": "test-session-001",
        "skill_id": "java",
        "difficulty": "medium",
        "resume_text": "5年Java开发经验，熟悉Spring Boot",
        "questions": [
            {"question": "什么是Spring IOC？", "category": "Spring", "is_follow_up": False},
            {"question": "解释Java泛型的作用", "category": "Java基础", "is_follow_up": False},
        ],
        "current_index": 0,
        "current_answer": "Spring IOC 是控制反转...",
        "evaluation": {"score": 6, "feedback": "回答基本正确但不够深入"},
        "follow_up_counts": {},
        "difficulty_adjustment": 1.0,
        "candidate_profile": {},
        "topic_performance": {},
        "recent_scores": [5.0, 6.0],
        "consecutive_high": 0,
        "consecutive_low": 0,
    }


# ========== 注册表测试 ==========

class TestToolRegistry:
    """测试工具注册表"""

    def test_tools_registered(self):
        """验证所有内置工具已注册"""
        tools = get_available_tools()
        expected = [
            "adjust_difficulty", "skip_question", "end_interview",
            "update_strategy", "query_knowledge_base", "analyze_resume",
            "generate_follow_up", "generate_hint",
        ]
        for name in expected:
            assert name in tools, f"工具 {name} 未注册"

    def test_get_tools_schema(self):
        """验证 schema 生成正确"""
        schema = get_tools_schema(["adjust_difficulty", "skip_question"])
        assert len(schema) == 2
        for item in schema:
            assert item["type"] == "function"
            assert "function" in item
            assert "name" in item["function"]
            assert "description" in item["function"]
            assert "parameters" in item["function"]

    def test_get_tools_schema_all(self):
        """验证不传参数时返回所有工具"""
        schema = get_tools_schema()
        assert len(schema) == len(get_available_tools())

    def test_get_tools_schema_unknown_tool(self):
        """验证未知工具被忽略"""
        schema = get_tools_schema(["adjust_difficulty", "nonexistent_tool"])
        assert len(schema) == 1


# ========== adjust_difficulty 测试 ==========

class TestAdjustDifficulty:
    """测试难度调整工具"""

    @pytest.mark.asyncio
    async def test_adjust_up(self, sample_state):
        """测试提高难度"""
        result = await adjust_difficulty(state=sample_state, direction="up")
        assert "提高" in result
        assert sample_state["difficulty_adjustment"] > 1.0

    @pytest.mark.asyncio
    async def test_adjust_down(self, sample_state):
        """测试降低难度"""
        sample_state["difficulty_adjustment"] = 1.0
        result = await adjust_difficulty(state=sample_state, direction="down")
        assert "降低" in result
        assert sample_state["difficulty_adjustment"] < 1.0

    @pytest.mark.asyncio
    async def test_adjust_up_max(self, sample_state):
        """测试难度上限"""
        sample_state["difficulty_adjustment"] = 1.8
        await adjust_difficulty(state=sample_state, direction="up")
        assert sample_state["difficulty_adjustment"] == 2.0

    @pytest.mark.asyncio
    async def test_adjust_down_min(self, sample_state):
        """测试难度下限"""
        sample_state["difficulty_adjustment"] = 0.6
        await adjust_difficulty(state=sample_state, direction="down")
        assert sample_state["difficulty_adjustment"] == 0.5


# ========== skip_question 测试 ==========

class TestSkipQuestion:
    """测试跳过题目工具"""

    @pytest.mark.asyncio
    async def test_skip_success(self, sample_state):
        """测试正常跳过"""
        result = await skip_question(state=sample_state, reason="太简单")
        assert "已跳过" in result
        assert sample_state["current_index"] == 1

    @pytest.mark.asyncio
    async def test_skip_last_question(self, sample_state):
        """测试跳过最后一题"""
        sample_state["current_index"] = 1
        result = await skip_question(state=sample_state)
        assert "已经是最后一题" in result


# ========== end_interview 测试 ==========

class TestEndInterview:
    """测试结束面试工具"""

    @pytest.mark.asyncio
    async def test_end_interview(self, sample_state):
        """测试提前结束面试"""
        result = await end_interview(state=sample_state, reason="时间不够")
        assert "已提前结束" in result
        assert sample_state["done"] is True
        assert sample_state["action"] == "done"


# ========== update_strategy 测试 ==========

class TestUpdateStrategy:
    """测试更新策略工具"""

    @pytest.mark.asyncio
    async def test_update_focus_topics(self, sample_state):
        """测试更新重点主题"""
        result = await update_strategy(
            state=sample_state,
            focus_topics="并发编程,JVM调优",
        )
        assert "并发编程" in result
        assert sample_state["interview_strategy"]["focus_topics"] == ["并发编程", "JVM调优"]

    @pytest.mark.asyncio
    async def test_update_difficulty_direction(self, sample_state):
        """测试更新难度方向"""
        result = await update_strategy(
            state=sample_state,
            difficulty_direction="up",
        )
        assert sample_state["interview_strategy"]["difficulty_direction"] == "up"


# ========== execute_tool 测试 ==========

class TestExecuteTool:
    """测试工具执行器"""

    @pytest.mark.asyncio
    async def test_execute_known_tool(self, sample_state):
        """测试执行已知工具"""
        result = await execute_tool("adjust_difficulty", {"direction": "up"}, sample_state)
        assert "提高" in result

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, sample_state):
        """测试执行未知工具"""
        result = await execute_tool("nonexistent", {}, sample_state)
        assert "Error" in result
        assert "未知工具" in result

    @pytest.mark.asyncio
    async def test_execute_tool_with_error(self, sample_state):
        """测试工具执行异常时的降级处理"""
        # 使用一个会抛异常的工具参数
        with patch("app.modules.interview.graph.tools.generate_follow_up_tool",
                    new_callable=AsyncMock, side_effect=Exception("test error")):
            result = await execute_tool("generate_follow_up", {}, sample_state)
            assert "Error" in result
            assert "执行失败" in result


# ========== query_knowledge_base 测试 ==========

class TestQueryKnowledgeBase:
    """测试知识库查询工具"""

    @pytest.mark.asyncio
    async def test_query_without_pgvector(self, sample_state):
        """测试 pgvector 不可用时的降级"""
        with patch("app.modules.interview.knowledge_base._HAS_PGVECTOR", False):
            result = await query_knowledge_base(state=sample_state, query="Spring IOC", top_k=3)
            # 应该返回失败信息而不是抛异常
            assert isinstance(result, str)
