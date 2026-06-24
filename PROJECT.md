# Agent Meet — 项目架构文档

> 基于 LangGraph 的 AI 模拟面试 Agent 系统

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 语言 | Python 3.12+ | 全异步 |
| Web 框架 | FastAPI + Uvicorn | REST API |
| Agent 框架 | LangGraph | 状态图 + interrupt/resume 人机交互 |
| LLM | DeepSeek (OpenAI 兼容) | 对话 / JSON / Function Calling / Embedding |
| 数据库 | PostgreSQL + asyncpg | 异步驱动 |
| ORM | SQLAlchemy 2.0 | 异步 DeclarativeBase |
| 向量存储 | pgvector | 余弦相似度 RAG 检索 |
| 模板引擎 | Jinja2 | Prompt 模板 (8 个 .j2 文件) |
| 配置管理 | Pydantic Settings | 环境变量驱动 |
| 前端 | 原生 HTML + Tailwind CSS + JS | 无构建工具 |
| 容器化 | Docker | Python 3.12-slim 镜像 |

---

## 目录结构

```
agent-meet/
├── app/                              # 后端应用
│   ├── main.py                       # FastAPI 入口，路由注册，静态文件挂载
│   ├── config.py                     # Pydantic Settings 配置（环境变量驱动）
│   │
│   ├── common/                       # 公共基础模块
│   │   ├── llm_client.py             # LLM 统一客户端（4 种调用模式 + Embedding）
│   │   └── prompt_loader.py          # Jinja2 模板加载器
│   │
│   ├── database/
│   │   └── engine.py                 # SQLAlchemy 异步引擎 + Session 工厂
│   │
│   ├── models/                       # ORM 数据模型
│   │   ├── interview.py              # InterviewSessionEntity（面试会话）
│   │   └── memory.py                 # CandidateMemoryEntity（候选人记忆）
│   │
│   └── modules/
│       └── interview/                # 面试业务模块
│           ├── router.py             # API 路由（2 个接口）
│           ├── knowledge_base.py     # pgvector RAG 知识库检索
│           │
│           ├── graph/                # LangGraph 核心
│           │   ├── state.py          # AgentState / InterviewState 状态定义
│           │   ├── tools.py          # 工具注册系统（8 个内置工具）
│           │   ├── agent.py          # ReAct 循环 + Agent 决策
│           │   ├── planner.py        # 面试前策略规划
│           │   ├── memory.py         # 长期记忆 加载/持久化
│           │   ├── graph_builder.py  # 图构建 + 编译（Agent 图 + 工作流图）
│           │   └── service.py        # HTTP ↔ LangGraph 桥接服务
│           │
│           └── prompts/              # Prompt 模板
│               └── templates/
│                   ├── agent_system.j2           # Agent 系统提示词
│                   ├── agent_planner.j2          # 面试策略规划
│                   ├── agent_decision_context.j2 # Agent 决策上下文
│                   ├── agent_evaluate_single.j2  # 单题评估
│                   ├── agent_follow_up.j2        # 追问生成
│                   ├── agent_hint.j2             # 提示生成
│                   ├── agent_resume_analysis.j2  # 简历分析
│                   └── agent_memory_summary.j2   # 记忆摘要
│
├── frontend/                         # 前端（静态文件）
│   ├── index.html                    # 主页面（Tailwind 深色主题）
│   └── js/
│       ├── api.js                    # API 客户端封装
│       └── app.js                    # 交互逻辑 + UI 渲染
│
├── tests/                            # 测试
│   ├── conftest.py                   # 测试配置
│   ├── test_tools.py                 # 工具单元测试
│   └── test_agent_integration.py     # Agent 集成测试
│
├── .env.example                      # 环境变量模板
├── pyproject.toml                    # 项目元数据 + 依赖声明
├── Dockerfile                        # 容器构建
├── .dockerignore
├── ARCHITECTURE_GUIDE.md             # 详细架构文档
├── CONTINUE_PROMPT.md                # Claude 续写引导
└── PROJECT.md                        # 本文档
```

---

## 系统架构

### 核心流程

```
HTTP 请求
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│  FastAPI Router                                           │
│  POST /api/interview/start          → service.start()     │
│  POST /api/interview/sessions/{id}/answer → service.submit│
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  InterviewGraphService (HTTP ↔ LangGraph 桥接)            │
│  agent_mode=True  → agent_graph (Agent 模式)              │
│  agent_mode=False → workflow_graph (工作流模式，降级方案)    │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  LangGraph StateGraph (Agent 模式)                        │
│                                                           │
│  START                                                    │
│    │                                                      │
│    ▼                                                      │
│  load_memory ──→ plan_strategy ──→ present_question       │
│    (长期记忆)      (LLM 规划)         (展示题目)            │
│                                          │                │
│                                          ▼                │
│                                    wait_for_answer        │
│                                     (interrupt 暂停)       │
│                                          │                │
│                              ┌───────────┘                │
│                              │ (用户提交答案)               │
│                              ▼                            │
│                           evaluate_answer                  │
│                            (LLM 评估)                      │
│                              │                            │
│                              ▼                            │
│                        update_agent_context                │
│                        (更新短期记忆)                       │
│                              │                            │
│                              ▼                            │
│                       agent_route_decision                 │
│                       (ReAct 循环，工具调用)                │
│                         │    │    │    │                   │
│                         ▼    ▼    ▼    ▼                   │
│                      follow  hint skip  save               │
│                      _up          _question _and_advance   │
│                         │    │    │    │                   │
│                         └────┴────┴────┘                   │
│                              │                            │
│                              ▼                            │
│                       generate_report                      │
│                              │                            │
│                              ▼                            │
│                         save_memory                        │
│                        (持久化记忆)                        │
│                              │                            │
│                              ▼                            │
│                             END                           │
└─────────────────────────────────────────────────────────┘
```

### 双模式设计

| | Agent 模式 | 工作流模式 |
|---|---|---|
| 路由决策 | LLM 通过 Function Calling 自主选择工具 | 硬编码 `if score >= 7` 规则 |
| 灵活性 | 高（可动态调整策略） | 低（固定流程） |
| 可靠性 | 依赖 LLM 推理质量 | 确定性执行 |
| 适用场景 | 正式使用 | 降级兜底 |

---

## API 接口

### 1. 启动面试

```
POST /api/interview/start
```

**请求体：**
```json
{
  "session_id": "uuid-string",
  "skill_id": "java",
  "difficulty": "medium",
  "questions": [
    {"question": "请解释 Java 垃圾回收机制", "category": "JVM"},
    {"question": "什么是 Spring IOC？", "category": "Spring"}
  ],
  "resume_text": "可选简历文本",
  "agent_mode": true
}
```

**响应：**
```json
{
  "code": 0,
  "data": {
    "done": false,
    "question": "请解释 Java 垃圾回收机制",
    "question_index": 0,
    "category": "JVM",
    "is_follow_up": false,
    "hint": "",
    "interview_strategy": {
      "focus_topics": ["JVM", "并发"],
      "skip_topics": ["基础语法"],
      "difficulty_direction": "up",
      "estimated_remaining": 5,
      "reasoning": "候选人简历显示 JVM 经验较少..."
    }
  }
}
```

### 2. 提交答案

```
POST /api/interview/sessions/{session_id}/answer?agent_mode=true
```

**请求体：**
```json
{
  "answer": "GC 主要通过标记-清除、复制、标记-整理三种算法..."
}
```

**响应（继续）：**
```json
{
  "code": 0,
  "data": {
    "done": false,
    "evaluation": {
      "score": 7,
      "feedback": "回答涵盖了主要 GC 算法...",
      "strengths": "对基本概念理解清晰",
      "weaknesses": "未提及 G1/ZGC 等现代收集器"
    },
    "question": "什么是 Spring IOC？",
    "question_index": 1,
    "category": "Spring",
    "is_follow_up": false,
    "hint": "",
    "agent_reasoning": {
      "thought": "候选人 JVM 基础尚可，继续下一题",
      "action": "save_and_advance"
    }
  }
}
```

**响应（结束）：**
```json
{
  "code": 0,
  "data": {
    "done": true,
    "report": {
      "total_score": 7.2,
      "summary": "候选人整体表现良好...",
      "scores": [
        {"category": "JVM", "score": 7},
        {"category": "Spring", "score": 8}
      ],
      "strengths": ["Spring 框架", "集合框架"],
      "weaknesses": ["并发编程", "JVM 调优"]
    },
    "candidate_profile": {
      "avg_score": 7.2,
      "strong_topics": ["Spring IOC"],
      "weak_topics": ["并发编程"],
      "interview_count": 3
    },
    "topic_performance": {
      "JVM": [7.0],
      "Spring": [8.0]
    }
  }
}
```

### 3. 健康检查

```
GET /health → {"status": "ok", "mode": "agent"}
```

---

## Agent 工具系统

Agent 通过 ReAct 循环（Thought → Action → Observation）自主决策，最多 3 步推理。

| 工具 | 类型 | 说明 |
|------|------|------|
| `adjust_difficulty` | 终端 | 调整难度因子 (0.5~2.0) |
| `skip_question` | 终端 | 跳过当前题 |
| `end_interview` | 终端 | 提前结束面试 |
| `update_strategy` | 终端 | 更新面试策略（重点/跳过主题、难度方向） |
| `generate_follow_up` | 终端 | 基于回答生成追问 |
| `generate_hint` | 终端 | 为当前题生成提示 |
| `query_knowledge_base` | 中间 | RAG 检索知识库（循环继续） |
| `analyze_resume` | 中间 | LLM 分析简历（循环继续） |

- **终端工具**：执行后立即返回路由，退出 ReAct 循环
- **中间工具**：执行后将结果追加到上下文，继续下一轮推理

---

## 数据模型

### interview_sessions

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | String | 用户标识 |
| skill_id | String | 技能方向 |
| difficulty | String | 难度 |
| status | String | 状态 |
| current_question_index | Integer | 当前题号 |
| graph_mode | String | 图模式 |
| agent_mode | Boolean | 是否 Agent 模式 |
| overall_score | Float | 综合评分 |
| report_json | JSON | 报告数据 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### candidate_memories

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | String | 用户标识（索引） |
| memory_type | String | 类型：profile / interview_summary / skill_progress |
| content | JSON | 记忆内容 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### vector_store (pgvector)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| content | Text | 文本内容 |
| metadata | JSON | 元数据 |
| embedding | Vector(1024) | 向量（余弦相似度检索） |

---

## 环境变量

```bash
# 应用
APP_NAME=Agent Meet
DEBUG=false

# 数据库
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agent_meet

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM (DeepSeek / OpenAI 兼容)
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-xxx
LLM_MODEL=deepseek-chat

# Embedding
EMBEDDING_BASE_URL=https://api.deepseek.com/v1
EMBEDDING_API_KEY=sk-xxx
EMBEDDING_MODEL=deepseek-embedding
EMBEDDING_DIMENSIONS=1024

# Agent 模式
AGENT_MODE_ENABLED=true
AGENT_MAX_REASONING_STEPS=3
AGENT_MEMORY_ENABLED=true
AGENT_PLANNING_ENABLED=true

# 面试参数
INTERVIEW_FOLLOW_UP_MAX=2
INTERVIEW_HINT_ENABLED=true
INTERVIEW_PASS_SCORE=7
INTERVIEW_FOLLOW_UP_SCORE=4
```

---

## 快速启动

```bash
# 1. 安装依赖
pip install -e .

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 LLM API Key 和数据库地址

# 3. 启动 PostgreSQL（需要 pgvector 扩展）

# 4. 启动服务
uvicorn app.main:app --reload

# 5. 访问
# 前端页面: http://localhost:8000/
# Swagger:  http://localhost:8000/docs
# 健康检查: http://localhost:8000/health
```
