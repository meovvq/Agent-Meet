"""Agent 面试状态定义

基于原 interview-guide-python 的 InterviewState 扩展，
新增 Agent 推理、记忆、动态规划等字段。

兼容性：AgentState 包含原 InterviewState 的所有字段，
工作流模式节点函数可无缝接入。
"""

from typing import TypedDict


class AgentReasoning(TypedDict, total=False):
    """Agent 单步推理记录（ReAct 循环中的一环）"""
    thought: str          # LLM 的推理过程（为什么选择这个动作）
    action: str           # 选择的动作名（工具名 或 "direct_answer"）
    action_input: dict    # 动作参数
    observation: str      # 动作执行结果


class InterviewState(TypedDict, total=False):
    """面试状态 —— 工作流模式兼容层

    包含原项目 InterviewState 的全部字段，
    保证工作流模式的节点函数可以正常工作。
    """
    # ---- 会话基础（面试期间不变）----
    session_id: str
    skill_id: str
    difficulty: str
    resume_text: str

    # ---- 题目管理（动态可变）----
    questions: list[dict]
    current_index: int
    total_original: int
    follow_up_counts: dict[str, int]

    # ---- 当前轮次 ----
    current_answer: str
    evaluation: dict
    action: str
    hint: str

    # ---- 最终输出 ----
    report: dict | None
    done: bool


class AgentState(InterviewState, total=False):
    """Agent 模式扩展状态

    继承 InterviewState 的所有字段，新增 Agent 特有字段。
    """

    # ---- Agent 模式开关 ----
    agent_mode: bool                  # True = Agent 模式, False = 工作流模式

    # ---- Agent 推理（ReAct 循环）----
    agent_history: list[AgentReasoning]   # 推理历史，每步一条
    available_tools: list[str]            # 当前可用的工具名列表
    max_reasoning_steps: int              # 单次决策最大推理步数（防无限循环）

    # ---- 记忆系统 ----
    candidate_profile: dict               # 候选人画像（累积更新）
    #   {
    #     "avg_score": 7.2,
    #     "strong_topics": ["Spring IOC"],
    #     "weak_topics": ["并发编程"],
    #     "interview_count": 3,
    #     "notes": "表达清晰，但底层原理薄弱"
    #   }
    topic_performance: dict[str, list[float]]  # 按主题的成绩追踪
    #   {"并发编程": [4.0, 6.0], "Spring IOC": [8.0]}

    # ---- 动态规划 ----
    interview_strategy: dict              # 当前面试策略
    #   {
    #     "focus_topics": ["并发编程", "JVM调优"],
    #     "skip_topics": ["基础语法"],
    #     "difficulty_direction": "up",
    #     "estimated_remaining": 5,
    #     "reasoning": "候选人并发基础薄弱，需深入考察"
    #   }
    difficulty_adjustment: float          # 难度调整因子 (0.5 ~ 2.0, 1.0 = 原始难度)
    focus_topics: list[str]              # 需要重点考察的主题

    # ---- 面试上下文（供 Agent 决策参考）----
    recent_scores: list[float]           # 最近 N 题的分数
    consecutive_high: int                # 连续高分题数
    consecutive_low: int                 # 连续低分题数
