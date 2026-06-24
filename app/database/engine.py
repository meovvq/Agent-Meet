"""数据库引擎与会话管理"""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

log = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession]:
    """请求级数据库会话（FastAPI 依赖注入）

    用法：
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """自动建表（开发环境）"""
    from app.models import interview, memory, resume, knowledge_base  # noqa: F401

    # 导入 VectorStore（条件依赖 pgvector）
    try:
        from app.modules.knowledgebase.vector_service import VectorStore  # noqa: F401
    except ImportError:
        log.warning("pgvector 未安装，跳过 vector_store 表创建")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("数据库表已初始化")
