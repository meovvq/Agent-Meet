"""Agent 模式集成测试

测试 Agent 模式的完整面试流程，包括：
- 图构建
- 状态流转
- Agent 决策
- 记忆系统
- 策略规划
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.interview.graph.graph_builder import (
    build_agent_graph,
    build_workflow_graph,
    present_question,
    workflow_route_decision,
)
from app.modules.interview.graph.state import AgentState, AgentReasoning, InterviewState


# ========== 状态测试 ==========

class TestState:
    """测试状态定义"""

    def test_interview_state_fields(self):
        """验证 InterviewState 包含必要字段"""
        state: InterviewState = {
            "session_id": "test",
            "skill_id": "java",
            "difficulty": "medium",
            "questions": [],
            "current_index": 0,
            "done": False,
        }
        assert state["session_id"] == "test"
        assert state["done"] is False

    def test_agent_state_inherits_interview_state(self):
        """验证 AgentState 继承 InterviewState"""
        state: AgentState = {
            "session_id": "test",
            "agent_mode": True,
            "agent_history": [],
            "candidate_profile": {},
            "interview_strategy": {},
        }
        assert state["agent_mode"] is True
        assert "session_id" in state  # 继承自 InterviewState

    def test_agent_reasoning_structure(self):
        """验证 AgentReasoning 结构"""
        reasoning: AgentReasoning = {
            "thought": "候选人回答良好",
            "action": "save_and_advance",
            "action_input": {},
            "observation": "已保存",
        }
        assert reasoning["thought"] == "候选人回答良好"


# ========== 图构建测试 ==========

class TestGraphBuilder:
    """测试图构建"""

    def test_build_workflow_graph(self):
        """测试工作流模式图构建"""
        graph = build_workflow_graph()
        assert graph is not None

    def test_build_agent_graph(self):
        """测试 Agent 模式图构建"""
        graph = build_agent_graph()
        assert graph is not None


# ========== 工作流路由测试 ==========

class TestWorkflowRouteDecision:
    """测试工作流模式路由决策"""

    def test_high_score_advances(self):
        """高分应该进入下一题"""
        state = {"evaluation": {"score": 8}, "current_index": 0, "follow_up_counts": {}}
        assert workflow_route_decision(state) == "save_and_advance"

    def test_medium_score_follows_up(self):
        """中分应该追问"""
        state = {"evaluation": {"score": 5}, "current_index": 0, "follow_up_counts": {}}
        assert workflow_route_decision(state) == "generate_follow_up"

    def test_low_score_gives_hint(self):
        """低分应该给提示"""
        state = {"evaluation": {"score": 2}, "current_index": 0, "follow_up_counts": {}}
        assert workflow_route_decision(state) == "provide_hint"

    def test_max_follow_ups_gives_hint(self):
        """追问次数达到上限应该给提示"""
        state = {"evaluation": {"score": 5}, "current_index": 0, "follow_up_counts": {"0": 2}}
        assert workflow_route_decision(state) == "provide_hint"


# ========== 节点函数测试 ==========

class TestNodeFunctions:
    """测试节点函数"""

    def test_present_question_normal(self):
        """测试正常展示题目"""
        state = {
            "questions": [{"question": "什么是IOC？", "category": "Spring"}],
            "current_index": 0,
        }
        result = present_question(state)
        assert result["action"] == "present"

    def test_present_question_done(self):
        """测试所有题目完成"""
        state = {
            "questions": [{"question": "什么是IOC？"}],
            "current_index": 1,
        }
        result = present_question(state)
        assert result["action"] == "done"


# ========== Agent 决策测试 ==========

class TestAgentDecision:
    """测试 Agent 决策逻辑"""

    @pytest.mark.asyncio
    async def test_agent_decision_no_questions(self):
        """没有题目时应该生成报告"""
        from app.modules.interview.graph.agent import agent_route_decision
        state: AgentState = {
            "questions": [],
            "current_index": 0,
            "evaluation": {},
        }
        result = await agent_route_decision(state)
        assert result == "generate_report"

    @pytest.mark.asyncio
    async def test_update_agent_context(self):
        """测试上下文更新"""
        from app.modules.interview.graph.agent import update_agent_context
        state: AgentState = {
            "evaluation": {"score": 8},
            "current_index": 0,
            "questions": [{"category": "Spring"}],
            "topic_performance": {},
            "recent_scores": [],
            "consecutive_high": 0,
            "consecutive_low": 0,
            "candidate_profile": {},
        }
        await update_agent_context(state)
        assert state["consecutive_high"] == 1
        assert state["consecutive_low"] == 0
        assert 8 in state["topic_performance"].get("Spring", [])

    @pytest.mark.asyncio
    async def test_update_agent_context_low_score(self):
        """测试低分上下文更新"""
        from app.modules.interview.graph.agent import update_agent_context
        state: AgentState = {
            "evaluation": {"score": 2},
            "current_index": 0,
            "questions": [{"category": "Java基础"}],
            "topic_performance": {},
            "recent_scores": [],
            "consecutive_high": 0,
            "consecutive_low": 0,
            "candidate_profile": {},
        }
        await update_agent_context(state)
        assert state["consecutive_high"] == 0
        assert state["consecutive_low"] == 1


# ========== 策略规划测试 ==========

class TestPlanner:
    """测试策略规划"""

    @pytest.mark.asyncio
    async def test_plan_interview_strategy_fallback(self):
        """测试策略规划失败时的降级处理"""
        from app.modules.interview.graph.planner import plan_interview_strategy
        state: AgentState = {
            "skill_id": "java",
            "difficulty": "medium",
            "resume_text": "",
            "candidate_profile": {},
        }
        with patch("app.modules.interview.graph.planner.chat_completion_json",
                    new_callable=AsyncMock, side_effect=Exception("LLM error")):
            result = await plan_interview_strategy(state)
            assert "interview_strategy" in result
            assert result["difficulty_adjustment"] == 1.0


# ========== 记忆系统测试 ==========

class TestMemory:
    """测试记忆系统"""

    @pytest.mark.asyncio
    async def test_load_memory_without_db(self):
        """测试数据库不可用时的记忆加载"""
        from app.modules.interview.graph.memory import load_memory
        state: AgentState = {
            "session_id": "test",
            "candidate_profile": {},
        }
        # 由于没有真实数据库，应该降级处理
        result = await load_memory(state)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_save_memory_without_db(self):
        """测试数据库不可用时的记忆保存"""
        from app.modules.interview.graph.memory import save_memory
        state: AgentState = {
            "session_id": "test",
            "candidate_profile": {"avg_score": 7.0},
            "report": {},
            "skill_id": "java",
            "difficulty": "medium",
            "questions": [],
        }
        # 由于没有真实数据库，应该降级处理
        result = await save_memory(state)
        assert isinstance(result, dict)


# ========== Prompt 模板测试 ==========

class TestPromptTemplates:
    """测试 Prompt 模板加载"""

    def test_render_agent_system(self):
        """测试 Agent 系统提示词模板"""
        from app.common.prompt_loader import render_prompt
        result = render_prompt("agent_system.j2", tools_description="工具列表")
        assert "AI 面试官" in result
        assert "工具列表" in result

    def test_render_planner(self):
        """测试规划提示词模板"""
        from app.common.prompt_loader import render_prompt
        result = render_prompt(
            "agent_planner.j2",
            skill_id="java",
            difficulty="medium",
            resume_section="",
            history_section="",
        )
        assert "java" in result
        assert "medium" in result

    def test_render_decision_context(self):
        """测试决策上下文模板"""
        from app.common.prompt_loader import render_prompt
        result = render_prompt(
            "agent_decision_context.j2",
            question_index=0,
            total_questions=5,
            question="什么是IOC？",
            category="Spring",
            is_follow_up=False,
            answer="控制反转...",
            score=7,
            feedback="回答良好",
            follow_up_count=0,
            recent_scores="7.0, 8.0",
            difficulty_adj="1.00",
            consecutive_high=2,
            consecutive_low=0,
            profile_str="{}",
            strategy_str="{}",
        )
        assert "什么是IOC？" in result
        assert "7/10" in result

    def test_render_evaluate_single(self):
        """测试单题评估模板"""
        from app.common.prompt_loader import render_prompt
        result = render_prompt(
            "agent_evaluate_single.j2",
            category="Spring",
            difficulty="medium",
            question="什么是IOC？",
            user_answer="控制反转...",
            reference_section="",
            resume_text="",
        )
        assert "Spring" in result
        assert "控制反转" in result

    def test_render_follow_up(self):
        """测试追问模板"""
        from app.common.prompt_loader import render_prompt
        result = render_prompt(
            "agent_follow_up.j2",
            category="Spring",
            question="什么是IOC？",
            user_answer="控制反转...",
            score=6,
            feedback="不够深入",
            context="",
        )
        assert "追问" in result

    def test_render_hint(self):
        """测试提示模板"""
        from app.common.prompt_loader import render_prompt
        result = render_prompt(
            "agent_hint.j2",
            category="Spring",
            question="什么是IOC？",
            user_answer="不知道",
            score=2,
            feedback="未作答",
            hint_level="gentle",
        )
        assert "提示" in result or "引导" in result
