# Agent Meet 项目文档

> **信息来源说明**：本文档中带有 [源码验证] 标记的内容来自对实际源码文件的直接分析，带有 [推断] 标记的内容基于项目结构和代码模式推断，未经直接源码确认。

---

## 1. 项目概述

### 1.1 项目定位

**Agent Meet** 是一个基于 LangGraph 的 AI 模拟面试 Agent 系统。它从传统的工作流面试系统（`interview-guide-python`）演进而来，核心变化是将面试流程的路由决策从硬编码规则改为 LLM 自主决策。[源码验证]

### 1.2 解决的核心问题

传统模拟面试系统使用固定的 `if-else` 规则决定面试流程（高分跳过、低分提示），无法根据候选人的实际表现灵活调整。Agent Meet 让 LLM 作为面试官 Agent，通过 ReAct 循环（Thought → Action → Observation）自主决定：是否追问、是否给提示、是否调整难度、是否跳题、是否提前结束。[源码验证]

### 1.3 核心能力列表

| 能力 | 说明 |
|------|------|
| **双模式面试** | Agent 模式（LLM 自主决策）+ 工作流模式（硬编码路由 fallback） |
| **自适应出题** | 支持纯方向出题和简历+方向混合出题（60% 简历 + 40% 方向） |
| **多轮追问** | Agent 可根据回答深度自主决定是否追问（最多 N 轮） |
| **动态难度调整** | Agent 可根据候选人表现实时调整难度因子（0.5 ~ 2.0） |
| **RAG 知识库** | 支持上传 PDF/DOCX/TXT 文档，pgvector 向量化 + BM25 + RRF 混合检索 |
| **简历分析** | LLM 自动分析简历，提取技能、经验、亮点、短板 |
| **长期记忆** | 跨面试会话的候选人画像持久化（擅长/薄弱主题、历史总结） |
| **面试策略规划** | 面试前 LLM 自动制定策略（重点主题、跳过主题、难度方向） |
| **技能方向管理** | 10 个预置技能方向（Java 后端、Python 后端、前端、算法等），支持自定义 |
| **评估报告** | 面试结束后生成整体评估报告（分数、强项、弱项、主题得分） |

---

## 2. 架构设计

### 2.1 完整目录树

```text
agent-meet/
├── .dockerignore                    # Docker 构建排除规则
├── .env                             # 环境变量（本地开发用，不入 Git）
├── .env.example                     # 环境变量模板
├── ARCHITECTURE_GUIDE.md            # 架构指南文档
├── CONTINUE_PROMPT.md               # 续写提示词
├── Dockerfile                       # Docker 镜像定义（Python 3.12-slim）
├── PROJECT.md                       # 项目说明文档
├── README.md                        # 项目 README
├── docker-compose.yml               # Docker Compose 编排（加入 interview-guide 网络）
├── pyproject.toml                   # Python 项目元数据与依赖
├── start.ps1                        # PowerShell 启动脚本
│
├── app/                             # 后端应用主目录
│   ├── __init__.py
│   ├── config.py                    # 全局配置（pydantic-settings，从 .env 读取）
│   ├── main.py                      # FastAPI 应用入口（lifespan、路由注册、静态文件）
│   │
│   ├── common/                      # 通用基础设施
│   │   ├── __init__.py
│   │   ├── exception.py             # 统一异常处理（ErrorCode、BusinessException）
│   │   ├── llm_client.py            # LLM 客户端封装（chat/embedding/streaming/tools）
│   │   ├── prompt_loader.py         # Jinja2 模板加载器
│   │   └── result.py                # 统一响应封装（Result[T]）
│   │
│   ├── database/                    # 数据库层
│   │   └── engine.py                # SQLAlchemy 异步引擎、会话工厂、init_db
│   │
│   ├── models/                      # ORM 模型
│   │   ├── __init__.py
│   │   ├── interview.py             # InterviewSessionEntity、InterviewAnswerEntity
│   │   ├── knowledge_base.py        # KnowledgeBaseEntity
│   │   ├── memory.py                # CandidateMemoryEntity
│   │   └── resume.py                # ResumeEntity、ResumeAnalysisEntity
│   │
│   ├── schemas/                     # Pydantic 请求/响应模型
│   │   ├── __init__.py
│   │   ├── interview.py             # 面试相关 DTO
│   │   ├── knowledge_base.py        # 知识库相关 DTO
│   │   └── resume.py                # 简历相关 DTO
│   │
│   └── modules/                     # 业务模块
│       ├── __init__.py
│       │
│       ├── interview/               # 面试模块（核心）
│       │   ├── __init__.py
│       │   ├── router.py            # 面试 API 路由（/api/interview/*）
│       │   ├── session_service.py   # 面试会话 CRUD
│       │   ├── question_service.py  # 出题服务（有/无简历两种模式）
│       │   ├── skill_service.py     # 技能方向管理（SKILL.md + skill.meta.yml）
│       │   ├── knowledge_base.py    # 知识库检索服务（代理 VectorService）
│       │   │
│       │   ├── graph/               # LangGraph Agent 核心
│       │   │   ├── __init__.py
│       │   │   ├── state.py         # 状态定义（AgentState、AgentReasoning）
│       │   │   ├── tools.py         # 工具系统（8 个内置工具）
│       │   │   ├── agent.py         # Agent ReAct 循环核心
│       │   │   ├── planner.py       # 面试策略规划节点
│       │   │   ├── memory.py        # 长期记忆管理（加载/保存）
│       │   │   ├── graph_builder.py # 图构建与编译（双图：workflow + agent）
│       │   │   └── service.py       # HTTP API ↔ LangGraph 桥接服务
│       │   │
│       │   └── prompts/             # Prompt 模板
│       │       └── templates/       # Jinja2 模板文件（12 个）
│       │           ├── agent_system.j2
│       │           ├── agent_decision_context.j2
│       │           ├── agent_evaluate_single.j2
│       │           ├── agent_follow_up.j2
│       │           ├── agent_hint.j2
│       │           ├── agent_memory_summary.j2
│       │           ├── agent_planner.j2
│       │           ├── agent_resume_analysis.j2
│       │           ├── interview_question_resume_system.j2
│       │           ├── interview_question_resume_user.j2
│       │           ├── interview_question_skill_system.j2
│       │           └── interview_question_skill_user.j2
│       │
│       ├── knowledgebase/           # 知识库模块
│       │   ├── __init__.py
│       │   ├── router.py            # 知识库 API 路由（/api/knowledgebase/*）
│       │   ├── upload_service.py    # 文件上传、解析、去重
│       │   └── vector_service.py    # 向量化存储、混合检索（pgvector + BM25 + RRF）
│       │
│       └── resume/                  # 简历模块
│           ├── __init__.py
│           ├── router.py            # 简历 API 路由（/api/resumes/*）
│           └── service.py           # 简历上传、解析、LLM 分析
│
├── frontend/                        # 前端（单页应用）
│   ├── index.html                   # 主页面（Tailwind CSS 暗色主题）
│   └── js/
│       ├── api.js                   # HTTP 客户端封装
│       └── app.js                   # 业务逻辑与 UI 渲染
│
├── skills/                          # 技能方向定义
│   ├── _shared/references/          # 共享参考素材（19 个 .md 文件）
│   ├── java-backend/                # Java 后端方向
│   ├── python-backend/              # Python 后端方向
│   ├── frontend/                    # 前端方向
│   ├── algorithm/                   # 算法方向
│   ├── system-design/               # 系统设计方向
│   ├── test-development/            # 测试开发方向
│   ├── java-backend-tencent/        # 腾讯 Java 后端方向
│   ├── ali-backend/                 # 阿里后端方向
│   ├── bytedance-backend/           # 字节后端方向
│   └── ai-agent-dev/                # AI Agent 开发方向
│
├── storage/                         # 上传文件存储目录
└── tests/                           # 测试
    ├── __init__.py
    ├── conftest.py                  # pytest-asyncio 配置
    ├── test_agent_integration.py    # Agent 集成测试
    └── test_tools.py                # 工具系统单元测试
```

### 2.2 模块职责表

| 模块 | 职责 | 关键文件 |
|------|------|----------|
| `app/config` | 全局配置管理（环境变量加载） | [config.py](app/config.py) |
| `app/common/exception` | 统一异常处理与错误码 | [exception.py](app/common/exception.py) |
| `app/common/llm_client` | LLM 调用封装（chat/tools/embedding） | [llm_client.py](app/common/llm_client.py) |
| `app/common/prompt_loader` | Jinja2 模板渲染 | [prompt_loader.py](app/common/prompt_loader.py) |
| `app/common/result` | 统一 API 响应格式 | [result.py](app/common/result.py) |
| `app/database/engine` | 异步数据库引擎与会话管理 | [engine.py](app/database/engine.py) |
| `app/models` | ORM 实体定义 | [interview.py](app/models/interview.py), [knowledge_base.py](app/models/knowledge_base.py), [memory.py](app/models/memory.py), [resume.py](app/models/resume.py) |
| `app/schemas` | Pydantic 请求/响应模型 | [interview.py](app/schemas/interview.py), [knowledge_base.py](app/schemas/knowledge_base.py), [resume.py](app/schemas/resume.py) |
| `interview/router` | 面试 API 端点 | [router.py](app/modules/interview/router.py) |
| `interview/session_service` | 面试会话 CRUD | [session_service.py](app/modules/interview/session_service.py) |
| `interview/question_service` | LLM 出题引擎 | [question_service.py](app/modules/interview/question_service.py) |
| `interview/skill_service` | 技能方向管理与题目分配 | [skill_service.py](app/modules/interview/skill_service.py) |
| `interview/graph/state` | LangGraph 状态定义 | [state.py](app/modules/interview/graph/state.py) |
| `interview/graph/tools` | Agent 工具注册与执行 | [tools.py](app/modules/interview/graph/tools.py) |
| `interview/graph/agent` | Agent ReAct 循环核心 | [agent.py](app/modules/interview/graph/agent.py) |
| `interview/graph/planner` | 面试策略规划 | [planner.py](app/modules/interview/graph/planner.py) |
| `interview/graph/memory` | 长期记忆管理 | [memory.py](app/modules/interview/graph/memory.py) |
| `interview/graph/graph_builder` | LangGraph 图构建与编译 | [graph_builder.py](app/modules/interview/graph/graph_builder.py) |
| `interview/graph/service` | HTTP ↔ LangGraph 桥接 | [service.py](app/modules/interview/graph/service.py) |
| `knowledgebase/router` | 知识库 API 端点 | [router.py](app/modules/knowledgebase/router.py) |
| `knowledgebase/upload_service` | 文件上传与解析 | [upload_service.py](app/modules/knowledgebase/upload_service.py) |
| `knowledgebase/vector_service` | 向量化与混合检索 | [vector_service.py](app/modules/knowledgebase/vector_service.py) |
| `resume/router` | 简历 API 端点 | [router.py](app/modules/resume/router.py) |
| `resume/service` | 简历上传、解析、LLM 分析 | [service.py](app/modules/resume/service.py) |

### 2.3 核心模块调用关系

```mermaid
graph TD
    subgraph HTTP层
        R1[interview/router]
        R2[resume/router]
        R3[knowledgebase/router]
    end

    subgraph 业务服务层
        S1[question_service]
        S2[skill_service]
        S3[session_service]
        S4[resume/service]
        S5[upload_service]
    end

    subgraph Agent核心
        GS[graph/service<br/>HTTP↔LangGraph桥接]
        GB[graph_builder<br/>图构建与编译]
        GA[agent<br/>ReAct循环]
        GP[planner<br/>策略规划]
        GM[memory<br/>长期记忆]
        GT[tools<br/>工具系统]
    end

    subgraph 基础设施
        LLM[llm_client]
        PL[prompt_loader]
        VS[vector_service]
        DB[engine + models]
    end

    R1 --> GS
    R1 --> S3
    R1 --> S1
    R1 --> S2
    R2 --> S4
    R3 --> S5
    R3 --> VS

    GS --> GB
    GB --> GA
    GB --> GP
    GB --> GM
    GA --> GT
    GA --> PL
    GA --> LLM

    S1 --> LLM
    S1 --> S2
    S1 --> PL
    S4 --> LLM
    S5 --> VS
    VS --> LLM
    VS --> DB
    GM --> DB
    GS --> DB
    S3 --> DB
```

### 2.4 请求流转路径

#### 面试启动流程

```text
POST /api/interview/start
  → router: 解析请求
  → question_service.generate_questions()  [如未传入题目]
    → skill_service.calculate_allocation()  [分配各分类题目数]
    → llm_client.chat_completion_json()     [调用 LLM 出题]
  → InterviewGraphService.start_interview()
    → graph_builder: 选择 agent_graph 或 workflow_graph
    → graph.ainvoke(initial_state)
      → load_memory()          [加载长期记忆]
      → plan_strategy()        [LLM 制定面试策略]
      → present_question()     [展示第一题]
      → wait_for_answer()      [interrupt 暂停，等待用户回答]
    → 返回第一题信息
```

#### 答案提交流程

```text
POST /api/interview/sessions/{id}/answer
  → InterviewGraphService.submit_answer()
    → graph.ainvoke(Command(resume=answer))
      → evaluate_answer()        [LLM 评估答案 + 知识库检索参考]
      → update_agent_context()   [更新短期记忆：分数、主题表现]
      → agent_route_decision()   [ReAct 循环：LLM 自主决策]
        → Thought: 分析当前状态
        → Action: 选择工具（如 generate_follow_up）
        → Observation: 工具执行结果
        → 返回路由名
      → 路由到对应节点（save_and_advance / generate_follow_up / provide_hint / generate_report）
      → wait_for_answer()        [再次 interrupt]
    → 返回评估结果 + 下一题/报告
```

---

## 3. 数据模型详解

### 3.1 ORM 基类

[源码验证] 使用 SQLAlchemy 2.0 异步模式，基类定义在 `app/database/engine.py`：

```python
class Base(DeclarativeBase):
    pass
```

数据库引擎配置：`pool_size=20`, `max_overflow=10`, `pool_pre_ping=True`。[源码验证]

### 3.2 实体关系总览

```mermaid
erDiagram
    InterviewSessionEntity ||--o{ InterviewAnswerEntity : "has answers"
    InterviewSessionEntity }o--|| CandidateMemoryEntity : "user_id links"
    ResumeEntity ||--o{ ResumeAnalysisEntity : "has analyses"
    KnowledgeBaseEntity ||--o{ VectorStore : "kb_id in metadata"

    InterviewSessionEntity {
        string id PK "UUID"
        string user_id "indexed"
        string skill_id
        string difficulty
        string status "IN_PROGRESS/EVALUATED"
        int current_question_index
        int total_questions
        text questions_json
        bool agent_mode
        float overall_score
        text report_json
        string evaluate_status "PENDING/EVALUATED/ERROR"
        datetime created_at
        datetime completed_at
    }

    InterviewAnswerEntity {
        int id PK "autoincrement"
        string session_id FK
        int question_index "unique with session_id"
        text question
        string category
        bool is_follow_up
        text user_answer
        float score
        text feedback
        text reference_answer
        text key_points_json
        datetime answered_at
    }

    CandidateMemoryEntity {
        int id PK "autoincrement"
        string user_id "indexed"
        string memory_type "profile/interview_summary/skill_progress"
        json content
        datetime created_at
        datetime updated_at
    }

    KnowledgeBaseEntity {
        int id PK "autoincrement"
        string file_hash "SHA-256 unique"
        string name
        string category
        string original_filename
        int file_size
        string content_type
        string storage_path
        int access_count
        int question_count
        string vector_status "PENDING/PROCESSING/COMPLETED/FAILED"
        string vector_error
        int chunk_count
        datetime created_at
    }

    ResumeEntity {
        int id PK "autoincrement"
        string file_hash "SHA-256 unique"
        string original_filename
        int file_size
        string content_type
        string storage_path
        text resume_text
        int access_count
        string analyze_status "PENDING/PROCESSING/COMPLETED/FAILED"
        string analyze_error
        datetime created_at
    }

    ResumeAnalysisEntity {
        int id PK "autoincrement"
        int resume_id FK
        float overall_score
        float content_score
        float structure_score
        float skill_match_score
        float expression_score
        float project_score
        text summary
        text strengths_json
        text suggestions_json
        datetime created_at
    }
```

### 3.3 级联删除策略

- **InterviewSessionEntity → InterviewAnswerEntity**：`cascade="all, delete-orphan"`，外键 `ondelete="CASCADE"` [源码验证]
- **ResumeEntity → ResumeAnalysisEntity**：`cascade="all, delete-orphan"` [推断，基于 ORM 关系定义模式]
- **KnowledgeBaseEntity → VectorStore**：应用层删除（`VectorService.delete_by_kb_id()`），非数据库级联 [源码验证]

---

## 4. 核心功能详解

### 4.1 面试模块

#### 4.1.1 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/interview/start` | 启动面试（可传入题目或自动生成） |
| `POST` | `/api/interview/sessions/{session_id}/answer` | 提交答案 |
| `GET` | `/api/interview/skills` | 获取技能方向列表 |
| `GET` | `/api/interview/sessions` | 获取面试会话列表 |
| `GET` | `/api/interview/sessions/{session_id}` | 获取会话详情（含答题记录） |
| `GET` | `/api/interview/sessions/{session_id}/report` | 获取评估报告 |
| `DELETE` | `/api/interview/sessions/{session_id}` | 删除会话 |

[源码验证：app/modules/interview/router.py]

#### 4.1.2 出题流程

**无简历模式**：[源码验证]

```text
skill_service.calculate_allocation(skill_id, question_count)
  → Phase 1: ALWAYS_ONE 分类各 1 题
  → Phase 2: 所有分类至少 1 题（CORE 优先）
  → Phase 3: 剩余题目按 CORE 优先轮转
→ 构建分配表 + 参考素材（上限 12000 字符）
→ LLM 出题（interview_question_skill_system.j2 + user.j2）
→ 解析题目列表
```

**有简历模式**：[源码验证]

```text
resume_count = question_count * 0.6
skill_count = question_count - resume_count
→ 并发执行：
  → gen_resume_questions()  [简历相关题目]
  → gen_skill_questions()   [方向相关题目]
→ 合并结果，降级兜底
```

#### 4.1.3 评估流程

每道题的评估流程：[源码验证]

```text
1. 从知识库检索参考资料（knowledge_base_service.query_with_context()）
2. 构建评估提示词（agent_evaluate_single.j2）
   - 4 个维度：准确性 40%、完整性 25%、深度 25%、表达 10%
   - 分数范围：0-10
3. LLM 返回 JSON：{score, feedback, referenceAnswer, keyPoints}
4. 分数校验（确保在 0-10 范围内）
```

### 4.2 知识库模块

#### 4.2.1 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/knowledgebase/list` | 获取知识库列表 |
| `GET` | `/api/knowledgebase/stats` | 获取统计数据 |
| `POST` | `/api/knowledgebase/upload` | 上传文件（PDF/DOCX/TXT） |
| `GET` | `/api/knowledgebase/{kb_id}` | 获取知识库详情 |
| `DELETE` | `/api/knowledgebase/{kb_id}` | 删除知识库及其向量 |
| `POST` | `/api/knowledgebase/{kb_id}/revectorize` | 重新向量化 |
| `POST` | `/api/knowledgebase/query` | RAG 检索 + LLM 回答 |

[源码验证：app/modules/knowledgebase/router.py]

#### 4.2.2 混合检索流程

[源码验证：app/modules/knowledgebase/vector_service.py]

```text
查询 → 并行执行：
  1. 向量检索：query → embedding → pgvector 余弦相似度（top_k * 4 候选）
  2. BM25 检索：query → 分词 → BM25Okapi 评分
→ RRF 融合排序：
  score = 1.5 / (60 + rank_vector) + 1.0 / (60 + rank_bm25) + overlap_bonus
  overlap_bonus = query_terms_in_doc / total_query_terms * 0.005
→ 返回 top_k 结果
```

分块策略：[源码验证]
- chunk_size = 300 tokens（约 1200 字符）
- chunk_overlap = 80 字符
- 优先按 Markdown 标题（`##` / `###`）切分，保留标题与正文不拆散
- 超长 section 按段落二次切分，再超长按标点切分

### 4.3 简历模块

#### 4.3.1 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/resumes/upload` | 上传简历（自动解析 + LLM 分析） |
| `GET` | `/api/resumes/` | 获取简历列表 |
| `GET` | `/api/resumes/{resume_id}/detail` | 获取简历详情（含分析历史） |
| `DELETE` | `/api/resumes/{resume_id}` | 删除简历 |
| `POST` | `/api/resumes/{resume_id}/reanalyze` | 重新分析简历 |

[源码验证：app/modules/resume/router.py]

#### 4.3.2 简历分析

LLM 分析 6 个维度的分数：[源码验证]

| 维度 | 说明 |
|------|------|
| `overall_score` | 综合评分 |
| `content_score` | 内容质量 |
| `structure_score` | 结构清晰度 |
| `skill_match_score` | 技能匹配度 |
| `expression_score` | 表达能力 |
| `project_score` | 项目经验 |

---

## 5. 通用基础设施详解

### 5.1 LLM 客户端封装

[源码验证：app/common/llm_client.py]

模块级单例：
- `chat_client`：聊天 LLM 客户端（默认 DeepSeek）
- `embedding_client`：Embedding 客户端（默认阿里 DashScope）

| 函数 | 用途 | 返回类型 |
|------|------|----------|
| `chat_completion()` | 普通聊天 | `str` |
| `chat_completion_json()` | 聊天 + 自动 JSON 解析 | `dict` |
| `chat_completion_with_tools()` | 聊天 + function calling（Agent 核心） | `ChatCompletionMessage` |
| `chat_completion_stream()` | 流式聊天 | `AsyncGenerator` |
| `get_embedding()` | 单文本嵌入 | `list[float]` |
| `get_embeddings()` | 批量文本嵌入 | `list[list[float]]` |

JSON 提取逻辑：自动去除 `<think>` 标签和 markdown 代码块。[源码验证]

### 5.2 统一响应/异常处理

**统一响应格式**：[源码验证：app/common/result.py]

```json
{
  "code": 0,       // 0=成功，非 0=错误码
  "message": "ok",
  "data": {}       // 业务数据
}
```

**错误码分段**：[源码验证：app/common/exception.py]

| 段 | 范围 | 模块 |
|----|------|------|
| 通用 | 400, 404, 500 | 参数错误、未找到、服务器错误 |
| 面试 | 3xxx | 面试模块错误 |
| 知识库 | 6xxx | 知识库模块错误 |
| AI 服务 | 7xxx | LLM 调用错误 |

**异常处理策略**：所有异常（包括 `BusinessException` 和未捕获异常）均返回 HTTP 200，通过 `code` 字段区分成功与失败。[源码验证]

### 5.3 Prompt 模板系统

模板目录：`app/modules/interview/prompts/templates/`，使用 Jinja2 渲染。[源码验证：app/common/prompt_loader.py]

| 模板文件 | 用途 | 使用场景 |
|----------|------|----------|
| `agent_system.j2` | Agent 系统提示词 | Agent ReAct 循环的 system prompt |
| `agent_decision_context.j2` | 决策上下文 | Agent 每次决策时的状态摘要 |
| `agent_evaluate_single.j2` | 单题评估 | 评估候选人答案 |
| `agent_follow_up.j2` | 追问生成 | 生成追问问题 |
| `agent_hint.j2` | 提示生成 | 生成引导性提示（gentle/direct 两级） |
| `agent_memory_summary.j2` | 面试总结 | 面试结束时生成长期记忆摘要 |
| `agent_planner.j2` | 策略规划 | 面试前制定面试策略 |
| `agent_resume_analysis.j2` | 简历分析 | 从简历中提取关键信息 |
| `interview_question_skill_system.j2` | 方向出题 system | 纯方向出题的系统提示词 |
| `interview_question_skill_user.j2` | 方向出题 user | 纯方向出题的用户提示词 |
| `interview_question_resume_system.j2` | 简历出题 system | 简历相关出题的系统提示词 |
| `interview_question_resume_user.j2` | 简历出题 user | 简历相关出题的用户提示词 |

---

## 6. Agent 系统详解

### 6.1 Agent 架构设计

[源码验证：app/modules/interview/graph/]

Agent 系统基于 LangGraph 的 StateGraph 构建，采用 ReAct（Reasoning + Acting）模式：

```text
Thought（推理）→ Action（动作）→ Observation（观察）→ Thought → ...
```

Agent 在每一步可以：
1. 直接决定路由（save_and_advance / generate_follow_up / provide_hint）
2. 调用中间工具获取更多信息（query_knowledge_base / analyze_resume），然后继续推理

### 6.2 状态定义

[源码验证：app/modules/interview/graph/state.py]

**InterviewState**（基础状态）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `session_id` | `str` | 会话 ID |
| `skill_id` | `str` | 技能方向 ID |
| `difficulty` | `str` | 难度（easy/medium/hard） |
| `resume_text` | `str` | 简历文本 |
| `questions` | `list[dict]` | 题目列表（动态可变，追问会插入） |
| `current_index` | `int` | 当前题目索引 |
| `total_original` | `int` | 原始题目总数 |
| `follow_up_counts` | `dict[str, int]` | 各题追问次数 |
| `current_answer` | `str` | 当前用户答案 |
| `evaluation` | `dict` | 评估结果 |
| `action` | `str` | 当前动作 |
| `hint` | `str` | 提示文本 |
| `report` | `dict \| None` | 最终报告 |
| `done` | `bool` | 面试是否结束 |

**AgentState**（继承 InterviewState，新增字段）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `agent_mode` | `bool` | 是否为 Agent 模式 |
| `agent_history` | `list[AgentReasoning]` | ReAct 推理历史 |
| `available_tools` | `list[str]` | 可用工具名列表 |
| `max_reasoning_steps` | `int` | 单次决策最大推理步数（默认 3） |
| `candidate_profile` | `dict` | 候选人画像（avg_score, strong_topics, weak_topics） |
| `topic_performance` | `dict[str, list[float]]` | 按主题的成绩追踪 |
| `interview_strategy` | `dict` | 当前面试策略 |
| `difficulty_adjustment` | `float` | 难度调整因子（0.5 ~ 2.0） |
| `focus_topics` | `list[str]` | 重点考察主题 |
| `recent_scores` | `list[float]` | 最近 5 题分数 |
| `consecutive_high` | `int` | 连续高分题数（≥7） |
| `consecutive_low` | `int` | 连续低分题数（<4） |

### 6.3 图结构

#### Agent 模式图

[源码验证：app/modules/interview/graph/graph_builder.py]

```mermaid
graph TD
    START --> load_memory
    load_memory --> plan_strategy
    plan_strategy --> present_question
    present_question -->|action=done| generate_report
    present_question -->|action!=done| wait_for_answer
    wait_for_answer --> evaluate_answer
    evaluate_answer --> update_agent_context
    update_agent_context -->|LLM 决策| agent_route_decision{agent_route_decision}
    agent_route_decision -->|save_and_advance| save_and_advance
    agent_route_decision -->|generate_follow_up| generate_follow_up
    agent_route_decision -->|provide_hint| provide_hint
    agent_route_decision -->|generate_report| generate_report
    save_and_advance --> present_question
    generate_follow_up --> present_question
    provide_hint --> wait_for_answer
    generate_report --> save_memory
    save_memory --> END
```

#### 工作流模式图（Fallback）

[源码验证：app/modules/interview/graph/graph_builder.py]

```mermaid
graph TD
    START --> present_question
    present_question -->|action=done| generate_report
    present_question -->|action!=done| wait_for_answer
    wait_for_answer --> evaluate_answer
    evaluate_answer -->|score≥7| save_and_advance
    evaluate_answer -->|4≤score<7 且追问<2| generate_follow_up
    evaluate_answer -->|其他| provide_hint
    save_and_advance --> present_question
    generate_follow_up --> present_question
    provide_hint --> wait_for_answer
    generate_report --> END
```

### 6.4 工具定义与调用机制

[源码验证：app/modules/interview/graph/tools.py]

工具通过 `@interview_tool(name, description)` 装饰器注册，自动从函数签名生成 OpenAI function calling schema。

| 工具名 | 类型 | 说明 |
|--------|------|------|
| `adjust_difficulty` | 终端 | 调整难度因子（×1.3 或 ×0.7，范围 0.5-2.0） |
| `skip_question` | 终端 | 跳过当前题目 |
| `end_interview` | 终端 | 提前结束面试 |
| `update_strategy` | 终端 | 更新面试策略（重点/跳过主题、难度方向） |
| `generate_follow_up` | 终端 | 生成追问问题 |
| `generate_hint` | 终端 | 生成引导性提示 |
| `query_knowledge_base` | 中间 | RAG 向量检索知识库（不直接路由，继续推理） |
| `analyze_resume` | 中间 | LLM 分析简历（不直接路由，继续推理） |

**工具执行流程**：[源码验证]

```text
LLM 返回 tool_call → 解析函数名和参数 → execute_tool() → 工具函数执行
  → 中间工具：结果追加到 context，继续 ReAct 循环
  → 终端工具：映射到图路由名，返回路由
```

**路由映射**：[源码验证]

| 工具名 | 图路由 |
|--------|--------|
| `generate_follow_up` | `generate_follow_up` |
| `generate_hint` | `provide_hint` |
| `skip_question` | `save_and_advance` |
| `end_interview` | `generate_report` |
| `adjust_difficulty` | `save_and_advance` |
| `update_strategy` | `save_and_advance` |

### 6.5 记忆系统

[源码验证：app/modules/interview/graph/memory.py]

#### 短期记忆（面试内）

通过 `AgentState` 中的字段实现，在 `update_agent_context` 节点中每题评估后更新：

- `topic_performance`：按主题追踪所有分数
- `recent_scores`：最近 5 题分数
- `consecutive_high` / `consecutive_low`：连续高/低分计数
- `candidate_profile`：avg_score、strong_topics（≥7）、weak_topics（<5）

#### 长期记忆（跨面试）

通过 `CandidateMemoryEntity` ORM 持久化到数据库：

- **加载**（`load_memory`）：面试开始时从数据库读取该用户的所有记忆，合并到 `candidate_profile`
- **保存**（`save_memory`）：面试结束时将候选人画像（upsert）和面试总结（insert）写入数据库

记忆类型：[源码验证]

| memory_type | 说明 | 更新策略 |
|-------------|------|----------|
| `profile` | 候选人画像 | upsert（存在则更新） |
| `interview_summary` | 单次面试总结 | 每次面试 insert 新记录 |
| `skill_progress` | 技能进度 | [推断] 保留历史版本 |

### 6.6 动态规划逻辑

[源码验证：app/modules/interview/graph/planner.py]

面试前，`plan_interview_strategy` 节点调用 LLM 制定面试策略：

```json
{
  "focus_topics": ["并发编程", "JVM调优"],
  "skip_topics": ["基础语法"],
  "difficulty_direction": "up",
  "estimated_questions": 8,
  "reasoning": "候选人并发基础薄弱，需深入考察"
}
```

策略影响：
- `difficulty_direction: "up"` → 初始 `difficulty_adjustment = 1.2`
- `difficulty_direction: "down"` → 初始 `difficulty_adjustment = 0.8`
- `difficulty_direction: "keep"` → 初始 `difficulty_adjustment = 1.0`
- Agent 可通过 `update_strategy` 工具在面试中实时调整策略

### 6.7 与传统工作流的区别

| 维度 | 工作流模式 | Agent 模式 |
|------|-----------|-----------|
| 路由决策 | 硬编码规则（score ≥ 7 → 跳过） | LLM 自主决策（ReAct 循环） |
| 记忆系统 | 无 | 短期记忆 + 长期记忆 |
| 策略规划 | 无 | LLM 面试前制定策略 |
| 工具调用 | 无 | 8 个工具（含中间工具） |
| 追问逻辑 | 固定追问次数上限 | Agent 根据回答质量自主决定 |
| 难度调整 | 无 | 动态调整因子（0.5-2.0） |
| 提示生成 | 固定逻辑 | Agent 自主决定是否给提示 |
| 图节点 | 7 个 | 11 个（+load_memory, plan_strategy, update_agent_context, save_memory） |

---

## 7. 依赖与环境

### 7.1 核心依赖列表

| 库名 | 版本要求 | 用途 |
|------|---------|------|
| `fastapi` | - | Web 框架 |
| `uvicorn` | - | ASGI 服务器 |
| `langgraph` | ≥0.4.0 | Agent 图框架 |
| `langchain-core` | ≥0.3.0 | LangChain 核心（LangGraph 依赖） |
| `openai` | ≥1.60.0 | OpenAI 兼容 API 客户端 |
| `sqlalchemy[asyncio]` | - | ORM + 异步支持 |
| `asyncpg` | - | PostgreSQL 异步驱动 |
| `pydantic-settings` | - | 配置管理 |
| `jinja2` | - | Prompt 模板渲染 |
| `redis` | - | Redis 客户端 |
| `pgvector` | - | PostgreSQL 向量扩展 |
| `rank_bm25` | - | BM25 关键词检索 |
| `PyPDF2` | - | PDF 文本提取 |
| `python-docx` | - | DOCX 文本提取 |
| `chardet` | - | 文本编码检测 |
| `PyYAML` | - | YAML 解析（skill.meta.yml） |

[源码验证：pyproject.toml]

### 7.2 环境变量表

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/agent_meet` | 数据库连接 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接 |
| `LLM_BASE_URL` | `https://api.deepseek.com/v1` | LLM API 地址 |
| `LLM_API_KEY` | `sk-xxx` | LLM API Key |
| `LLM_MODEL` | `deepseek-chat` | LLM 模型名 |
| `EMBEDDING_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | Embedding API 地址 |
| `EMBEDDING_API_KEY` | `sk-xxx` | Embedding API Key |
| `EMBEDDING_MODEL` | `text-embedding-v3` | Embedding 模型名 |
| `EMBEDDING_DIMENSIONS` | `1024` | 向量维度 |
| `AGENT_MODE_ENABLED` | `True` | 是否启用 Agent 模式 |
| `AGENT_MAX_REASONING_STEPS` | `3` | 单次决策最大推理步数 |
| `AGENT_MEMORY_ENABLED` | `True` | 是否启用长期记忆 |
| `AGENT_PLANNING_ENABLED` | `True` | 是否启用策略规划 |
| `INTERVIEW_FOLLOW_UP_MAX` | `2` | 每题最大追问次数 |
| `INTERVIEW_HINT_ENABLED` | `True` | 是否启用提示功能 |
| `INTERVIEW_PASS_SCORE` | `7` | 及格分数 |
| `INTERVIEW_FOLLOW_UP_SCORE` | `4` | 触发追问的分数阈值 |
| `STORAGE_PATH` | `./storage` | 文件存储路径 |

[源码验证：app/config.py, .env.example]

---

## 8. Prompt 模板系统

### 8.1 模板列表

所有模板位于 `app/modules/interview/prompts/templates/` 目录，使用 `.j2` 扩展名（Jinja2 语法）。[源码验证]

| 模板文件 | 用途 | 使用场景 | 调用位置 |
|----------|------|----------|----------|
| `agent_system.j2` | Agent 系统提示词 | ReAct 循环的 system prompt，定义面试官角色、决策原则表、推理流程、约束条件 | [agent.py](app/modules/interview/graph/agent.py) `_get_agent_system_prompt()` |
| `agent_decision_context.j2` | 决策上下文 | 每次 Agent 决策时注入当前面试状态（题目、分数、画像、策略等） | [agent.py](app/modules/interview/graph/agent.py) `_build_decision_context()` |
| `agent_evaluate_single.j2` | 单题评估 | 评估候选人答案，4 维度评分（准确性 40%、完整性 25%、深度 25%、表达 10%） | [graph_builder.py](app/modules/interview/graph/graph_builder.py) `evaluate_answer()` |
| `agent_follow_up.j2` | 追问生成 | 基于候选人答案生成追问，遵循 5 原则（渐进式、引导性、具体、相关、适度深度） | [tools.py](app/modules/interview/graph/tools.py) `generate_follow_up_tool()` |
| `agent_hint.j2` | 提示生成 | 生成引导性提示，支持 gentle（方向提示）和 direct（关键点提示）两级 | [tools.py](app/modules/interview/graph/tools.py) `generate_hint_tool()` |
| `agent_memory_summary.j2` | 面试总结 | 面试结束时生成长期记忆摘要（6 要素：整体评价、技术等级、强项、弱项、面试行为、建议） | [graph_builder.py](app/modules/interview/graph/graph_builder.py) `generate_report()` |
| `agent_planner.j2` | 策略规划 | 面试前制定策略（5 要素：重点主题、跳过主题、难度方向、预估题数、理由） | [planner.py](app/modules/interview/graph/planner.py) `plan_interview_strategy()` |
| `agent_resume_analysis.j2` | 简历分析 | 从简历中提取关键信息（4 维度：相关技能、经验等级、亮点、短板） | [tools.py](app/modules/interview/graph/tools.py) `analyze_resume()` |
| `interview_question_skill_system.j2` | 方向出题 system | 纯方向出题的系统提示词，定义出题标准（技术链追问、难度分布 30%/50%/20%） | [question_service.py](app/modules/interview/question_service.py) `_generate_without_resume()` |
| `interview_question_skill_user.j2` | 方向出题 user | 纯方向出题的用户提示词，注入分配表、参考素材、历史去重 | [question_service.py](app/modules/interview/question_service.py) `_generate_without_resume()` |
| `interview_question_resume_system.j2` | 简历出题 system | 简历相关出题的系统提示词，严格规则：只问简历中实际存在的项目/技术 | [question_service.py](app/modules/interview/question_service.py) `_generate_with_resume()` |
| `interview_question_resume_user.j2` | 简历出题 user | 简历相关出题的用户提示词，注入简历文本、技能信息、难度描述 | [question_service.py](app/modules/interview/question_service.py) `_generate_with_resume()` |

### 8.2 模板渲染机制

[源码验证：app/common/prompt_loader.py]

```python
# Jinja2 环境初始化
_TEMPLATE_DIR = Path(__file__).parent.parent / "modules" / "interview" / "prompts" / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    trim_blocks=True,      # 去除块标签后的第一个换行
    lstrip_blocks=True,    # 去除块标签前的空白
)

def render_prompt(template_name: str, **kwargs) -> str:
    template = _env.get_template(template_name)
    return template.render(**kwargs)
```

**渲染特性**：
- `trim_blocks=True`：`{% %}` 标签后的换行符被自动去除，避免模板中产生多余空行
- `lstrip_blocks=True`：块标签前的缩进空白被去除，使模板更易读
- 变量通过 `{{ variable }}` 注入，支持过滤器（如 `{{ text[:500] }}` 截断）
- 控制流通过 `{% if %}` / `{% for %}` 实现

**典型调用模式**：

```python
# 简单渲染
prompt = render_prompt("agent_evaluate_single.j2",
    category="Spring IOC",
    difficulty="medium",
    question="请解释 Spring IOC 的原理",
    user_answer="...",
    reference_section="...",
    resume_text="...",
)

# 带条件的模板（agent_decision_context.j2 中使用 {% if %} 判断可选字段）
context = render_prompt("agent_decision_context.j2",
    question_index=idx,
    total_questions=len(questions),
    question=q.get("question", "N/A"),
    # ... 其他字段
)
```

---

## 9. 部署与容器化

### 9.1 Dockerfile 说明

[源码验证：Dockerfile]

```dockerfile
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 安装编译依赖（psycopg2/asyncpg 需要 libpq-dev）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY app ./app
COPY frontend ./frontend

RUN pip install --upgrade pip && pip install -e .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**关键设计**：
- 基础镜像 `python:3.12-slim`：体积小，仅安装必要系统库
- `PYTHONDONTWRITEBYTECODE=1`：不生成 `.pyc` 文件，减少镜像体积
- `PYTHONUNBUFFERED=1`：stdout/stderr 不缓冲，确保日志实时输出
- `pip install -e .`：以开发模式安装，从 `pyproject.toml` 读取依赖
- 健康检查：每 30 秒访问 `/health` 端点，启动宽限期 10 秒
- **注意**：`skills/`、`storage/`、`.env` 未 COPY 到镜像，需通过 volume 挂载或环境变量注入 [推断]

### 9.2 docker-compose 服务编排

[源码验证：docker-compose.yml]

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: agent-meet-app
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:123456@interview-postgres:5432/agent_meet
      REDIS_URL: redis://interview-redis:6379/2
      # ... 所有配置项从 .env 文件透传
    networks:
      - interview-guide_default
    depends_on:
      - external-deps
    restart: unless-stopped

  # 占位服务：确保 agent-meet 加入 interview-guide 的外部网络
  external-deps:
    image: busybox
    container_name: agent-meet-deps-check
    command: echo "Dependencies ready"
    networks:
      - interview-guide_default

networks:
  interview-guide_default:
    external: true
```

**架构说明**：
- **复用外部基础设施**：PostgreSQL 和 Redis 不在本项目部署，而是加入兄弟项目 `interview-guide` 的 Docker 网络，复用其容器
- **网络隔离**：通过 `external: true` 网络实现跨项目容器互通
- **环境变量透传**：所有配置项通过 `${VAR:-default}` 语法从 `.env` 文件读取，未设置时使用默认值
- **自动重启**：`restart: unless-stopped` 确保容器异常退出后自动恢复

---

## 10. 使用方式

### 10.1 启动命令

#### 方式一：PowerShell 脚本（推荐本地开发）

```powershell
# 1. 复制并编辑环境变量
copy .env.example .env
# 编辑 .env，填入 LLM_API_KEY 和 EMBEDDING_API_KEY

# 2. 运行启动脚本（自动检查基础设施、创建虚拟环境、启动服务）
.\start.ps1
```

[源码验证：start.ps1] 脚本自动执行 4 步：
1. 检查/启动 PostgreSQL + Redis 容器（复用 interview-guide 项目）
2. 检查 `.env` 文件存在
3. 创建 Python 虚拟环境（如不存在）并安装依赖
4. 启动 `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

#### 方式二：手动启动

```bash
# 创建虚拟环境
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"

# 启动
.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 方式三：Docker Compose

```bash
docker compose up -d
```

### 10.2 访问地址

| 地址 | 说明 |
|------|------|
| `http://localhost:8000` | 前端页面（自动跳转到 `/static/index.html`） |
| `http://localhost:8000/docs` | FastAPI 自动生成的 Swagger API 文档 |
| `http://localhost:8000/health` | 健康检查端点 |

### 10.3 API 调用示例

#### 启动面试

```bash
curl -X POST http://localhost:8000/api/interview/start \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-001",
    "skill_id": "java-backend",
    "difficulty": "medium",
    "question_count": 5,
    "agent_mode": true
  }'
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "done": false,
    "question": "请解释 Java 中 HashMap 的底层实现原理",
    "question_index": 0,
    "category": "Java 集合",
    "is_follow_up": false,
    "hint": "",
    "interview_strategy": {
      "focus_topics": ["并发编程", "JVM"],
      "skip_topics": ["基础语法"],
      "difficulty_direction": "keep"
    }
  }
}
```

#### 提交答案

```bash
curl -X POST http://localhost:8000/api/interview/sessions/test-001/answer \
  -H "Content-Type: application/json" \
  -d '{"answer": "HashMap 基于数组+链表+红黑树实现..."}'
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "done": false,
    "evaluation": {
      "score": 7.5,
      "feedback": "对 HashMap 基本原理理解正确...",
      "referenceAnswer": "HashMap 在 JDK8+ 采用...",
      "keyPoints": ["数组+链表+红黑树", "负载因子0.75", "扩容机制"]
    },
    "question_index": 1,
    "question": "请说明 ConcurrentHashMap 的锁机制",
    "category": "并发编程",
    "agent_reasoning": {
      "thought": "候选人对 HashMap 理解良好，进入下一题",
      "action": "direct_pass"
    }
  }
}
```

#### 上传知识库文件

```bash
curl -X POST http://localhost:8000/api/knowledgebase/upload \
  -F "file=@./docs/java-guide.pdf" \
  -F "name=Java 面试指南" \
  -F "category=Java"
```

#### RAG 查询

```bash
curl -X POST http://localhost:8000/api/knowledgebase/query \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_base_ids": [1],
    "question": "Spring IOC 的核心原理是什么？"
  }'
```

---

## 11. 扩展点

### 11.1 新增技能方向

1. 在 `skills/` 目录下创建新文件夹（如 `skills/go-backend/`）
2. 创建 `SKILL.md`（YAML front matter + 面试官人设 + 指令）：

```markdown
---
name: Go 后端开发
description: Go 语言后端工程师面试方向
---

你是一位资深 Go 后端工程师...

## 面试要求
...
```

3. 创建 `skill.meta.yml`（显示元数据 + 分类）：

```yaml
displayName: Go 后端
display:
  icon: "🐹"
  gradient: "from-cyan-500 to-blue-600"
  color: "text-cyan-400"
categories:
  - key: "go-basic"
    label: "Go 基础"
    priority: "CORE"
    ref: "go-basic.md"
    shared: false
  - key: "concurrency"
    label: "并发编程"
    priority: "ALWAYS_ONE"
    ref: "concurrency.md"
```

4. （可选）在 `skills/go-backend/references/` 下添加参考素材文件
5. 重启应用，`skill_service` 会自动扫描加载 [源码验证]

### 11.2 新增 Agent 工具

在 `app/modules/interview/graph/tools.py` 中添加：

```python
@interview_tool("my_new_tool", "工具描述")
async def my_new_tool(state: dict, param1: str = "") -> str:
    """工具功能说明"""
    # 实现逻辑
    return "工具执行结果"
```

然后在 `agent.py` 的 `_ACTION_TO_ROUTE` 中添加路由映射：

```python
_ACTION_TO_ROUTE = {
    # ... 已有工具
    "my_new_tool": "save_and_advance",  # 或其他路由
}
```

[源码验证：tools.py 的装饰器自动注册机制]

### 11.3 新增业务模块

1. 在 `app/modules/` 下创建新目录（如 `app/modules/coding/`）
2. 创建 `router.py`（APIRouter）、`service.py`（业务逻辑）
3. 在 `app/main.py` 中注册路由：

```python
from app.modules.coding.router import router as coding_router
app.include_router(coding_router)
```

4. 在 `app/models/` 下添加 ORM 模型（如需要）
5. 在 `app/schemas/` 下添加 Pydantic 模型（如需要）

### 11.4 替换 LLM 提供商

修改 `.env` 中的 LLM 配置即可，无需改代码（基于 OpenAI 兼容 API）：

```bash
# 使用 OpenAI
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-xxx
LLM_MODEL=gpt-4o

# 使用本地 Ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5:14b

# 使用阿里百炼
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=sk-xxx
LLM_MODEL=qwen-max
```

---

## 12. 设计模式总结

| 设计模式 | 应用位置 | 说明 |
|----------|----------|------|
| **单例模式** | `settings`, `skill_service`, `knowledge_base_service`, `chat_client`, `embedding_client`, `workflow_graph`, `agent_graph` | 模块级全局单例，避免重复初始化 |
| **装饰器模式** | `@interview_tool(name, desc)` | 工具注册装饰器，自动从函数签名生成 OpenAI function calling schema |
| **策略模式** | `agent_graph` vs `workflow_graph` | 两种面试路由策略，通过 `agent_mode` 参数切换 |
| **模板方法模式** | LangGraph 图节点 | 固定流程骨架（load → plan → present → wait → evaluate → route → save），具体行为由节点函数实现 |
| **观察者模式** | LangGraph interrupt | `wait_for_answer` 节点通过 `interrupt()` 暂停图执行，等待外部 `Command(resume=)` 恢复 |
| **依赖注入** | FastAPI `Depends(get_db)` | 请求级数据库会话注入，自动管理事务生命周期 |
| **工厂方法模式** | `build_workflow_graph()`, `build_agent_graph()` | 图构建工厂函数，返回编译后的 StateGraph 实例 |
| **中介者模式** | `InterviewGraphService` | HTTP API 与 LangGraph 之间的桥接层，封装状态构建和响应提取 |
| **责任链模式** | ReAct 循环 | Agent 的 Thought → Action → Observation 链式推理，每步可决定终止或继续 |
| **缓存模式** | `_bm25_cache`, `SkillService._skills_cache` | BM25 索引缓存（TTL 300 秒）、技能列表缓存（启动时加载一次） |
| **降级模式** | `_fallback_questions()`, LLM 失败时返回默认值 | 出题/策略/报告生成失败时的兜底方案 |
| **统一响应模式** | `Result.success()` / `Result.error()` | 所有 API 返回统一 `{code, message, data}` 格式 |

---

## 13. 配置管理详解

### 13.1 配置加载机制

[源码验证：app/config.py]

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
```

**加载优先级**（从高到低）：
1. 系统环境变量
2. `.env` 文件
3. 代码中的默认值

### 13.2 配置项分类说明

#### 应用基础配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `app_name` | `Agent Meet` | 应用名称（FastAPI title） |
| `debug` | `False` | 调试模式（开启后 SQLAlchemy 输出 SQL 日志） |

#### 数据库配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `database_url` | `postgresql+asyncpg://postgres:postgres@localhost:5432/agent_meet` | PostgreSQL 连接串，使用 asyncpg 异步驱动 |

#### Redis 配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `redis_url` | `redis://localhost:6379/0` | Redis 连接串 [推断：当前代码中未直接使用，为预留配置] |

#### LLM 配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `llm_base_url` | `https://api.deepseek.com/v1` | LLM API 地址（OpenAI 兼容） |
| `llm_api_key` | `sk-xxx` | LLM API Key |
| `llm_model` | `deepseek-chat` | 聊天模型名 |

#### Embedding 配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `embedding_base_url` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | Embedding API 地址 |
| `embedding_api_key` | `sk-xxx` | Embedding API Key |
| `embedding_model` | `text-embedding-v3` | Embedding 模型名 |
| `embedding_dimensions` | `1024` | 向量维度（需与模型匹配） |

#### Agent 模式配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `agent_mode_enabled` | `True` | 是否启用 Agent 模式（false 则使用工作流模式） |
| `agent_max_reasoning_steps` | `3` | 单次决策最大 ReAct 步数（防止无限循环） |
| `agent_memory_enabled` | `True` | 是否启用长期记忆（跨面试会话） |
| `agent_planning_enabled` | `True` | 是否启用面试前策略规划 |

#### 面试参数配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `interview_follow_up_max` | `2` | 每题最大追问次数（工作流模式使用） |
| `interview_hint_enabled` | `True` | 是否启用提示功能 |
| `interview_pass_score` | `7` | 及格分数阈值 |
| `interview_follow_up_score` | `4` | 触发追问的分数阈值（4-6 分区间） |

#### 存储配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `storage_path` | `./storage` | 上传文件存储目录 |

---

## 14. 数据库初始化与迁移

### 14.1 建表机制

[源码验证：app/database/engine.py]

项目使用 SQLAlchemy 的 `create_all` 自动建表，在 FastAPI 启动时通过 lifespan 触发：

```python
async def init_db():
    """自动建表（开发环境）"""
    # 导入所有 ORM 模型，确保 Base.metadata 包含所有表定义
    from app.models import interview, memory, resume, knowledge_base

    # 条件导入 pgvector 模型
    try:
        from app.modules.knowledgebase.vector_service import VectorStore
    except ImportError:
        log.warning("pgvector 未安装，跳过 vector_store 表创建")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

**建表流程**：
1. FastAPI 启动 → `lifespan` 上下文管理器触发
2. `init_db()` 导入所有 ORM 模型模块
3. `Base.metadata.create_all` 为所有继承 `Base` 的模型创建表（已存在则跳过）
4. pgvector 的 `vector_store` 表为条件创建（需安装 `pgvector` 扩展）

**已注册的表**：

| 表名 | ORM 模型 | 说明 |
|------|----------|------|
| `interview_sessions` | `InterviewSessionEntity` | 面试会话 |
| `interview_answers` | `InterviewAnswerEntity` | 单题答案记录 |
| `knowledge_bases` | `KnowledgeBaseEntity` | 知识库文档 |
| `candidate_memories` | `CandidateMemoryEntity` | 候选人长期记忆 |
| `resumes` | `ResumeEntity` | 简历文件 |
| `resume_analyses` | `ResumeAnalysisEntity` | 简历分析结果 |
| `vector_store` | `VectorStore` | 向量存储（需 pgvector） |

### 14.2 迁移方案

当前项目**未使用 Alembic 等数据库迁移工具**，采用 `create_all` 自动建表策略。[源码验证]

**适用场景**：
- 开发阶段：表结构频繁变更，`create_all` 可自动新增表
- 新部署：从零创建所有表

**局限性**：
- `create_all` 只能创建新表，**不会修改已有表结构**（如新增列、修改列类型）
- 不支持数据迁移
- 不支持回滚

**生产环境建议** [推断]：
1. 引入 Alembic 进行版本化迁移管理
2. 初始化迁移仓库：`alembic init alembic`
3. 生成迁移脚本：`alembic revision --autogenerate -m "description"`
4. 执行迁移：`alembic upgrade head`

---

## 15. 前端层详解

### 15.1 前端架构

[源码验证：frontend/]

前端采用**纯原生 JavaScript 单页应用**，无构建工具、无框架依赖：

```text
frontend/
├── index.html          # 主页面（Tailwind CSS 暗色主题 + 内联样式）
└── js/
    ├── api.js          # HTTP 客户端封装（API 对象）
    └── app.js          # 业务逻辑（State + UI + App 三大对象）
```

**架构模式**：手动状态管理 + 直接 DOM 操作

```text
┌─────────────────────────────────────────┐
│  index.html                             │
│  ├── Tailwind CSS（CDN 引入）           │
│  ├── 内联样式（markdown、动画等）        │
│  ├── <div id="app">  ← UI.render() 目标 │
│  ├── <div id="toast"> ← 通知提示        │
│  ├── <script src="js/api.js">           │
│  └── <script src="js/app.js">           │
└─────────────────────────────────────────┘
```

### 15.2 核心对象

#### State — 全局状态

[源码验证：frontend/js/app.js]

```javascript
const State = {
  tab: 'interview',        // 当前标签页：interview | resume | kb | sessions
  // 面试状态
  sessionId: '',           // 当前面试会话 ID
  skillId: 'java-backend', // 选中的技能方向
  difficulty: 'medium',    // 难度
  agentMode: true,         // Agent 模式开关
  started: false,          // 面试是否已开始
  done: false,             // 面试是否结束
  currentQuestion: null,   // 当前题目
  evaluation: null,        // 当前评估结果
  agentReasoning: null,    // Agent 推理过程
  report: null,            // 最终报告
  history: [],             // 历史对话记录
  // 简历、知识库、会话列表等...
};
```

#### UI — 渲染层

`UI.render()` 根据 `State.tab` 和子状态分发到不同渲染函数：

```javascript
switch (State.tab) {
  case 'interview':
    State.started ? (State.done ? this.renderReport() : this.renderInterview()) : this.renderInterviewConfig();
    break;
  case 'resume':    State.resumeDetail ? this.renderResumeDetail() : this.renderResumeList(); break;
  case 'kb':        State.kbDetail ? this.renderKbDetail() : this.renderKbList(); break;
  case 'sessions':  State.sessionDetail ? this.renderSessionDetail() : this.renderSessionList(); break;
}
```

#### App — 业务逻辑层

封装所有 API 调用和状态更新：

```javascript
const App = {
  async startInterview() { ... },
  async submitAnswer() { ... },
  async loadResumes() { ... },
  async uploadResume(file) { ... },
  async loadSessions() { ... },
  // ...
};
```

### 15.3 API 调用方式

[源码验证：frontend/js/api.js]

```javascript
const API = {
  BASE: window.location.origin,

  // 通用请求方法
  async request(method, path, body = null) {
    const opts = { method, headers: {} };
    if (body) {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(this.BASE + path, opts);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (data.code != null && data.code !== 0) throw new Error(data.message);
    return data.data;  // 直接返回 data 字段
  },

  // 文件上传
  async upload(path, file, params = {}) {
    const form = new FormData();
    form.append('file', file);
    for (const [k, v] of Object.entries(params)) {
      if (v != null) form.append(k, v);
    }
    const res = await fetch(this.BASE + path, { method: 'POST', body: form });
    // ...
  },

  // 命名空间方法
  interview: {
    start: (data) => API.post('/api/interview/start', data),
    submitAnswer: (sessionId, answer) => API.post(`/api/interview/sessions/${sessionId}/answer`, { answer }),
    // ...
  },
};
```

**调用示例**：

```javascript
// 启动面试
const result = await API.interview.start({
  session_id: uuid(),
  skill_id: 'java-backend',
  difficulty: 'medium',
  question_count: 5,
  agent_mode: true,
});

// 提交答案
const response = await API.interview.submitAnswer(sessionId, answer);
```

### 15.4 UI 特性

| 特性 | 实现方式 |
|------|----------|
| 暗色主题 | Tailwind CSS `bg-gray-900` 系列 |
| 标签页导航 | `State.tab` 切换 + `UI.render()` 重绘 |
| 聊天气泡 | 左右布局，面试官灰色、候选人蓝色 |
| Agent 推理展示 | 可展开的紫色面板，显示 Thought/Action |
| 分数可视化 | 颜色编码（绿≥8、黄≥6、橙≥4、红<4） |
| Toast 通知 | 右上角浮层，3 秒/5 秒自动消失 |
| Markdown 渲染 | 基础样式支持（标题、列表、代码块） |
| 快捷键 | Ctrl+Enter 提交答案 |
| 加载状态 | 旋转动画 + 文字提示 |
| 错误处理 | 错误页面 + 重试按钮 |

---

## 附录：技术选型说明

| 选型 | 理由 |
|------|------|
| **LangGraph** | 原生支持状态图、interrupt（人机交互）、checkpointer（状态持久化），适合面试这种多轮对话+人工介入的场景 |
| **DeepSeek** | OpenAI 兼容 API，性价比高，支持 function calling |
| **pgvector** | 与 PostgreSQL 一体，无需额外向量数据库，支持余弦相似度 |
| **BM25 + RRF** | 向量检索擅长语义匹配，BM25 擅长精确匹配专有名词，RRF 融合两者优势 |
| **Jinja2 模板** | Prompt 版本化管理，易于调试和迭代，与 Python 生态无缝集成 |
| **SKILL.md + skill.meta.yml** | 纯文件驱动的技能管理，无需数据库迁移，支持 Git 版本控制 |
| **原生 JS 前端** | 零构建依赖，适合内部工具/MVP 阶段，快速迭代 |
