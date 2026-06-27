# Agent Meet

基于 LangGraph 的 AI 模拟面试 Agent 系统。

从 [interview-guide-python](../interview-guide-python) 的工作流模式演进而来，
将"开发者定义流程、LLM 执行任务"改造为"LLM 自主决策、开发者定义边界"。

## 核心特性

- **Agent 自主决策**：LLM 根据上下文自主选择下一步动作（追问/提示/跳题/结束），替代硬编码路由
- **工具系统**：8 个注册式工具，Agent 通过 function calling 自主调用
- **记忆系统**：短期记忆（会话内实时更新）+ 长期记忆（跨会话候选人画像持久化）
- **动态规划**：面试前 LLM 制定策略，面试中根据表现实时调整难度和方向
- **混合检索**：pgvector 向量检索 + BM25 关键词检索 + RRF 融合，提升知识库召回质量
- **双图模式**：Agent 模式（LLM 自主决策）+ 工作流模式（硬编码规则 fallback）

## 技术栈

| 层次 | 技术 |
|------|------|
| 后端框架 | Python 3.12+ / FastAPI / SQLAlchemy (async) |
| Agent 引擎 | LangGraph (StateGraph + interrupt/resume) |
| LLM | DeepSeek / OpenAI 兼容 API |
| 数据库 | PostgreSQL + pgvector |
| 向量检索 | pgvector + BM25 + RRF 混合检索 |
| 前端 | 原生 HTML + Tailwind CSS + Alpine.js |
| 测试 | pytest + pytest-asyncio |

## 架构概览

```
用户请求
  ↓
FastAPI Router
  ↓
InterviewGraphService (HTTP ↔ LangGraph 桥接)
  ↓
LangGraph StateGraph
  ├── load_memory        ← 加载长期记忆
  ├── plan_strategy      ← LLM 制定面试策略
  ├── present_question   ← 展示题目
  ├── wait_for_answer    ← interrupt 暂停等待用户
  ├── evaluate_answer    ← LLM 评估 + 知识库检索
  ├── update_agent_context ← 更新候选人画像
  ├── agent_route_decision ← LLM 自主决策下一步
  │     ├── save_and_advance → 下一题
  │     ├── generate_follow_up → 追问
  │     ├── provide_hint → 提示
  │     └── generate_report → 结束
  ├── generate_report    ← 生成面试报告
  └── save_memory        ← 持久化长期记忆
```

## 目录结构

```
agent-meet/
├── app/
│   ├── main.py                  # FastAPI 入口
│   ├── config.py                # 配置管理（pydantic-settings）
│   ├── common/                  # 公共模块
│   │   ├── llm_client.py        # LLM 调用封装（chat/tools/stream/json/embedding）
│   │   ├── prompt_loader.py     # Jinja2 模板加载
│   │   ├── metrics.py           # LLM 调用指标统计
│   │   └── result.py            # 统一响应格式
│   ├── models/                  # SQLAlchemy ORM
│   │   ├── interview.py         # 面试会话/答案/报告模型
│   │   ├── memory.py            # 候选人长期记忆模型
│   │   └── resume.py            # 简历模型
│   ├── database/                # 数据库连接
│   │   └── engine.py            # async engine + session
│   ├── schemas/                 # Pydantic 请求/响应模型
│   └── modules/
│       ├── interview/           # 面试模块
│       │   ├── graph/           # LangGraph Agent 核心
│       │   │   ├── state.py     # Agent 状态定义（AgentState）
│       │   │   ├── tools.py     # 工具注册与执行（8 个工具）
│       │   │   ├── agent.py     # Agent 节点（ReAct 循环）
│       │   │   ├── planner.py   # 动态规划节点
│       │   │   ├── memory.py    # 记忆管理节点
│       │   │   ├── graph_builder.py  # 图构建与编译（双图）
│       │   │   └── service.py   # 服务层（HTTP ↔ Graph 桥接）
│       │   ├── prompts/
│       │   │   └── templates/   # 13 个 Jinja2 prompt 模板
│       │   ├── router.py        # API 路由
│       │   ├── question_service.py  # 出题引擎
│       │   ├── session_service.py   # 会话管理
│       │   ├── skill_service.py     # 技能方向管理
│       │   └── knowledge_base.py    # 知识库检索服务
│       ├── knowledgebase/       # 知识库模块
│       │   ├── router.py        # 知识库 API
│       │   ├── upload_service.py    # 文件上传处理
│       │   └── vector_service.py    # 向量检索（pgvector + BM25 + RRF）
│       └── resume/              # 简历模块
│           ├── router.py        # 简历 API
│           └── service.py       # 简历处理服务
├── frontend/                    # 前端静态文件
│   ├── index.html               # 主页面
│   └── js/
│       └── app.js               # 前端逻辑
├── skills/                      # 技能方向配置
│   ├── java-backend/
│   ├── python-backend/
│   ├── system-design/
│   └── ...                      # 10+ 技能方向
├── tests/                       # 测试
│   ├── test_tools.py            # 工具单元测试
│   └── test_agent_integration.py # Agent 集成测试
├── output/                      # 输出文件
└── docker-compose.yml           # Docker 部署配置
```

## 快速开始

### 环境准备

```bash
# 克隆项目
git clone https://github.com/meovvq/Agent-Meet.git
cd Agent-Meet

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -e .
```

### 配置

```bash
# 复制环境配置
cp .env.example .env

# 编辑 .env，配置 LLM 和数据库
# LLM_BASE_URL=https://api.deepseek.com
# LLM_API_KEY=your_key
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/agent_meet
```

### 启动

```bash
# 启动数据库（Docker）
docker-compose up -d postgres

# 启动服务
python -m app.main
```

访问 http://localhost:8000 即可使用。

## API 接口

### 面试流程

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/interview/start` | 启动面试 |
| POST | `/api/interview/sessions/{id}/answer` | 提交答案 |
| GET | `/api/interview/skills` | 获取技能列表 |
| GET | `/api/interview/sessions` | 获取会话列表 |
| GET | `/api/interview/sessions/{id}` | 获取会话详情 |
| GET | `/api/interview/sessions/{id}/report` | 获取评估报告 |

### 知识库

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/knowledgebase/upload` | 上传知识库文件 |
| GET | `/api/knowledgebase` | 获取知识库列表 |
| DELETE | `/api/knowledgebase/{id}` | 删除知识库 |

### 简历

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/resume/upload` | 上传简历 |
| GET | `/api/resume` | 获取简历列表 |
| DELETE | `/api/resume/{id}` | 删除简历 |

## 面试流程

```
1. 用户上传简历/知识库（可选）
2. 选择技能方向 + 难度 + 题数
3. POST /start → 系统自动出题，返回第一题
4. 用户回答 → POST /answer → LLM 评估 + 决策
   ├── 7分以上 → 下一题
   ├── 4-7分 → 追问（最多2次）
   └── 4分以下 → 给提示，重新回答
5. 所有题目完成 → 生成报告
```

## 工具系统

Agent 可调用的 8 个工具：

| 工具 | 说明 |
|------|------|
| `adjust_difficulty` | 调整面试难度（up/down） |
| `skip_question` | 跳过当前题目 |
| `end_interview` | 提前结束面试 |
| `update_strategy` | 更新面试策略（重点/跳过/难度方向） |
| `query_knowledge_base` | 查询知识库获取参考资料 |
| `analyze_resume` | 分析候选人简历 |
| `generate_follow_up` | 生成追问问题 |
| `generate_hint` | 生成引导性提示 |

## 测试

```bash
# 运行所有测试
pytest

# 运行工具测试
pytest tests/test_tools.py

# 运行 Agent 集成测试
pytest tests/test_agent_integration.py
```

## License

MIT
