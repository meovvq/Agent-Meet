"""候选人长期记忆 ORM 模型"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.engine import Base


class CandidateMemoryEntity(Base):
    """候选人长期记忆

    存储跨会话的候选人画像、面试总结、技能进度等。
    在面试开始时加载，面试结束时更新。
    """
    __tablename__ = "candidate_memories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True, comment="关联用户 ID")
    memory_type: Mapped[str] = mapped_column(String(50), index=True, comment="记忆类型: profile / interview_summary / skill_progress")
    content: Mapped[dict] = mapped_column(JSON, comment="记忆内容（JSON）")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
