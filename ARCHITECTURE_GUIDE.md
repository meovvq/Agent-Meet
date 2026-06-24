# Agent Meet 架构指南

## 项目定位

从 [interview-guide-python](../interview-guide-python) 的**工作流模式**演进为 **Agent 模式**。

| 维度 | 工作流模式（原项目） | Agent 模式（本项目） |
|------|---------------------|---------------------|
| 路由 | 硬编码 `if score >= 7` | LLM tool calling 自主决策 |
| 工具 | 无（逻辑写死在节点里） | 注册式工具，Agent 自主调用 |
| 记忆 | 仅会话内 InterviewState | 短期 + 长期（跨会话画像） |
| 规划 | 无 | 面试前策略制定 + 面试中动态调整 |

---

## 核心架构图

```
START
  ↓
load_memory ──── 加载候选人长期记忆（跨会话画像）
  ↓
plan_strategy ── LLM 制定面试策略（focus_topics, difficulty_curve）
  ↓
present_question ──(done?)──→ generate_report → save_memory → END
  ↓
wait_for_answer ←──────────────────────────────────┐ (hint 后重答)
  ↓ (interrupt/resume)
evaluate_answer ── LLM 评估答案
  ↓
update_agent_context ── 更新短期记忆（画像、分数、连续表现）
  ↓
agent_route_decision ── LLM 自主决策（核心改造点）
  ├── "save_and_advance"  → save_and_advance → present_question
  ├── "generate_follow_up" → generate_follow_up → present_question
  ├── "provide_hint"       → provide_hint → wait_for_answer
  └── "generate_report"    → generate_report → save_memory → END
```

---

## 模块详解

### 1. 状态定义 (`state.py`)

```
InterviewState (工作流兼容)
  ├── 基础字段：session_id, skill_id, difficulty, resume_text
  ├── 题目管理：questions[], current_index, follow_up_counts
  ├── 当前轮次：current_answer, evaluation, action, hint
  └── 最终输出：report, done

AgentState (继承 InterviewState)
  ├── Agent 推理：agent_history[], available_tools[], max_reasoning_steps
  ├── 记忆系统：candidate_profile{}, topic_performance{}
  ├── 动态规划：interview_strategy{}, difficulty_adjustment, focus_topics[]
  └── 上下文追踪：recent_scores[], consecutive_high, consecutive_low
```

### 2. 工具系统 (`tools.py`)

```python
@interview_tool("adjust_difficulty", "调整面试难度")
async def adjust_difficulty(state: dict, direction: str = "up") -> str: ...
```

- **注册**：`@interview_tool` 装饰器，自动提取参数 schema
- **执行**：`execute_tool(name, arguments, state)` → str
- **Schema**：`get_tools_schema()` → OpenAI function calling 格式
- **内置工具**：adjust_difficulty, skip_question, end_interview, update_strategy, query_knowledge_base, analyze_resume, generate_follow_up, generate_hint

### 3. Agent 路由 (`agent.py`)

核心函数 `agent_route_decision(state) -> str`：

1. 构建决策上下文（题目、分数、画像、策略、最近表现）
2. 调用 LLM + tools（function calling）
3. 如果 LLM 返回 tool_call → 执行工具 → 中间工具继续推理，终端工具返回路由
4. 如果 LLM 无 tool_call → 直接通过（save_and_advance）
5. 循环最多 max_reasoning_steps 步

### 4. 动态规划 (`planner.py`)

面试前 LLM 制定策略：
```json
{
    "focus_topics": ["并发编程", "JVM调优"],
    "skip_topics": ["基础语法"],
    "difficulty_direction": "up",
    "estimated_questions": 8,
    "reasoning": "候选人简历显示3年经验，但并发描述模糊"
}
```

### 5. 记忆系统 (`memory.py`)

- **短期记忆**：`update_agent_context` 节点，每题评估后更新 candidate_profile
- **长期记忆**：`CandidateMemoryEntity` ORM，load_memory 加载 / save_memory 保存

---

## 双模式对比

```
graph_builder.py 导出两个全局单例：

workflow_graph = build_workflow_graph().compile(...)   # 工作流模式（fallback）
agent_graph    = build_agent_graph().compile(...)      # Agent 模式
```

`InterviewGraphService(agent_mode=True/False)` 选择使用哪个图。

---

## 文件清单

```
app/
├── config.py                          # 配置（含 Agent 开关）
├── common/llm_client.py              # LLM 封装（含 chat_completion_with_tools）
├── database/engine.py                 # async engine + session
├── models/
│   ├── interview.py                   # InterviewSessionEntity
│   └── memory.py                      # CandidateMemoryEntity
└── modules/interview/graph/
    ├── state.py                       # InterviewState + AgentState
    ├── tools.py                       # 工具注册与执行
    ├── agent.py                       # Agent 路由决策（ReAct 循环）
    ├── planner.py                     # 面试策略规划
    ├── memory.py                      # 记忆加载/保存节点
    ├── graph_builder.py               # 图构建与编译
    └── service.py                     # HTTP ↔ Graph 桥接
```
