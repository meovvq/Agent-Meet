"""Agent Meet —— AI 模拟面试 Agent 系统入口"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.common.exception import register_exception_handlers
from app.config import settings
from app.database.engine import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    log.info("Agent Meet 启动中...")
    await init_db()
    log.info("数据库初始化完成")
    yield
    log.info("Agent Meet 关闭")


app = FastAPI(
    title=settings.app_name,
    description="基于 LangGraph 的 AI 模拟面试 Agent",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理器
register_exception_handlers(app)


@app.get("/health")
async def health():
    return {"status": "ok", "mode": "agent"}


# 注册路由
from app.modules.interview.router import router as interview_router
from app.modules.resume.router import router as resume_router
from app.modules.knowledgebase.router import router as kb_router

app.include_router(interview_router)
app.include_router(resume_router)
app.include_router(kb_router)

# 挂载前端静态文件
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    async def index():
        return RedirectResponse(url="/static/index.html")
