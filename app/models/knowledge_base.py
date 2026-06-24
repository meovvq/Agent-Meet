"""知识库相关 ORM 模型"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.engine import Base


class KnowledgeBaseEntity(Base):
    """知识库文档"""
    __tablename__ = "knowledge_bases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="SHA-256")
    name: Mapped[str] = mapped_column(String(500))
    category: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(500))
    file_size: Mapped[int] = mapped_column(Integer)
    content_type: Mapped[str] = mapped_column(String(200))
    storage_path: Mapped[str] = mapped_column(String(1000))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    access_count: Mapped[int] = mapped_column(Integer, default=1)
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    vector_status: Mapped[str] = mapped_column(String(20), default="PENDING", comment="PENDING / PROCESSING / COMPLETED / FAILED")
    vector_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
