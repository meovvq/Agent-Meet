# Agent Meet

基于 LangGraph 的 AI 模拟面试 Agent 系统。

从 [interview-guide-python](../interview-guide-python) 的工作流模式演进而来，
将"开发者定义流程、LLM 执行任务"改造为"LLM 自主决策、开发者定义边界"。

## 核心特性

- **Agent 自主决策**：LLM 根据上下文自主选择下一步动作，替代硬编码路由
- **工具系统**：注册式工具，Agent 通过 function calling 自主调用
- **记忆系统**：短期记忆（会话内）+ 长期记忆（跨会话候选人画像）
- **动态规划**：面试前 LLM 制定策略，面试中实时调整

## 技术栈

- Python 3.12+ / FastAPI / SQLAlchemy (async)
- LangGraph (StateGraph + interrupt/resume)
- DeepSeek LLM (OpenAI 兼容 API)
- PostgreSQL + pgvector / Redis

## 目录结构

```
agent-meet/
├── app/
│   ├── main.py                  # FastAPI 入口
│   ├── config.py                # 配置管理
│   ├── common/                  # 公共模块
│   │   ├── llm_client.py        # LLM 调用封装（含 tool calling）
│   │   └── prompt_loader.py     # Jinja2 模板加载
│   ├── models/                  # SQLAlchemy ORM
│   │   └── memory.py            # 候选人长期记忆模型
│   ├── database/                # 数据库连接
│   │   └── engine.py            # async engine + session
│   └── modules/
│       └── interview/
│           ├── graph/           # LangGraph Agent 核心
│           │   ├── state.py     # Agent 状态定义
│           │   ├── tools.py     # 工具注册与执行
│           │   ├── agent.py     # Agent 节点（ReAct 循环）
│           │   ├── planner.py   # 动态规划节点
│           │   ├── memory.py    # 记忆管理节点
│           │   ├── graph_builder.py  # 图构建与编译
│           │   └── service.py   # 服务层（HTTP ↔ Graph 桥接）
│           └── prompts/
│               └── templates/   # Jinja2 prompt 模板
└── tests/
```
