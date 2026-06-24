# Agent Meet 项目 —— 新窗口提示词

以下内容直接复制到新的 Claude 窗口即可。

---

## 提示词正文

我正在开发一个 AI 模拟面试 Agent 系统（agent-meet），基于 FastAPI + LangGraph + DeepSeek LLM。项目位于 `D:\vscode\project\agent-meet\`。

### 当前项目状态

框架已搭建完成，共 28 个文件，约 1782 行代码。核心模块已就绪：

**已完成的模块：**

1. **状态定义** (`app/modules/interview/graph/state.py`)
   - `InterviewState`：工作流兼容层（原项目字段）
   - `AgentState`：继承 InterviewState，新增 agent_history、candidate_profile、interview_strategy、difficulty_adjustment 等字段

2. **工具系统** (`app/modules/interview/graph/tools.py`)
   - `@interview_tool` 装饰器注册工具，自动生成 OpenAI function calling schema
   - 8 个内置工具：adjust_difficulty、skip_question、end_interview、update_strategy、query_knowledge_base、analyze_resume、generate_follow_up、generate_hint
   - `execute_tool()` 执行工具，内部 try-except 降级
   - `get_tools_schema()` 生成 OpenAI function calling 格式

3. **Agent 路由** (`app/modules/interview/graph/agent.py`)
   - `agent_route_decision(state) -> str`：替代硬编码路由，LLM 自主决策
   - ReAct 循环：最多 max_reasoning_steps 步，中间工具（query_knowledge_base、analyze_resume）执行后继续推理，终端工具返回路由
   - `update_agent_context()`：评估后更新短期记忆（candidate_profile、topic_performance、recent_scores、consecutive_high/low）

4. **动态规划** (`app/modules/interview/graph/planner.py`)
   - `plan_interview_strategy()`：面试前 LLM 制定策略
   - 策略结构：focus_topics、skip_topics、difficulty_direction、estimated_questions、reasoning

5. **记忆系统** (`app/modules/interview/graph/memory.py`)
   - `load_memory()`：面试开始时加载 CandidateMemoryEntity
   - `save_memory()`：面试结束时保存候选人画像和面试总结
   - ORM 模型：`app/models/memory.py` 的 CandidateMemoryEntity

6. **图构建** (`app/modules/interview/graph/graph_builder.py`)
   - `build_workflow_graph()`：工作流模式（硬编码路由，作为 fallback）
   - `build_agent_graph()`：Agent 模式（LLM 自主决策）
   - 全局单例：workflow_graph 和 agent_graph

7. **服务层** (`app/modules/interview/graph/service.py`)
   - `InterviewGraphService(agent_mode=True/False)`：双模式选择
   - `start_interview()`：构建初始状态，启动图
   - `submit_answer()`：Command(resume=answer) 恢复图

8. **LLM 客户端** (`app/common/llm_client.py`)
   - `chat_completion()`：普通聊天
   - `chat_completion_json()`：JSON 响应解析
   - `chat_completion_with_tools()`：function calling（Agent 核心）
   - `chat_completion_stream()`：流式聊天

9. **API 路由** (`app/modules/interview/router.py`)
   - POST `/api/interview/start`：启动面试
   - POST `/api/interview/sessions/{session_id}/answer`：提交答案

### 技术栈

- Python 3.12+ / FastAPI / SQLAlchemy 2.0 (async)
- LangGraph (StateGraph + interrupt/resume)
- DeepSeek LLM (OpenAI 兼容 API)
- PostgreSQL + pgvector / Redis
- Jinja2 prompt 模板

### 待完成的工作

1. **Prompt 模板文件**：`app/modules/interview/prompts/templates/` 目录下需要创建：
   - `agent_system.j2`：Agent 系统提示词
   - `agent_planner.j2`：面试策略规划提示词
   - `agent_decision_context.j2`：路由决策上下文模板
   - `agent_resume_analysis.j2`：简历分析提示词
   - `agent_memory_summary.j2`：面试总结（长期记忆）

2. **对接原项目模块**：从 interview-guide-python 迁移：
   - 知识库模块（RAG）：对接 query_knowledge_base 工具
   - 简历模块：对接 analyze_resume 工具
   - 评估服务：完善 evaluate_answer 节点
   - 题目生成：对接 generate_question 节点

3. **测试**：
   - 单元测试：每个工具独立测试
   - 集成测试：Agent 模式完整面试流程
   - 对比测试：工作流模式 vs Agent 模式

4. **前端适配**：
   - Agent 推理过程展示（agent_reasoning 字段）
   - 策略展示（interview_strategy 字段）

5. **数据库**：
   - PostgreSQL 连接配置
   - pgvector 扩展（知识库向量检索）

### 原项目参考

原工作流模式项目在 `D:\vscode\project\interview-guide-python\`，可参考：
- `app/modules/interview/graph/nodes.py`：7 个节点函数的完整实现
- `app/modules/interview/graph/service.py`：InterviewGraphService
- `app/modules/interview/evaluation_service.py`：评估服务
- `app/modules/interview/skill_service.py`：技能服务
- `app/modules/knowledgebase/vector_service.py`：向量检索服务
- `prompts/templates/`：所有 Jinja2 prompt 模板

### 要求

1. 先阅读 agent-meet 项目的完整代码，理解当前架构
2. 继续完善项目，优先级：Prompt 模板 > 对接知识库/评估 > 测试
3. 保持现有代码风格和架构设计
4. 代码注释使用中文，保持与原项目一致
