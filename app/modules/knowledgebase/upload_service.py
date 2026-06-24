"""知识库上传与管理"""

import hashlib
import logging
import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exception import BusinessException, ErrorCode
from app.config import settings
from app.models.knowledge_base import KnowledgeBaseEntity
from app.schemas.knowledge_base import KnowledgeBaseListItemDTO, KnowledgeBaseStatsDTO

log = logging.getLogger(__name__)

ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "text/markdown",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class KnowledgeBaseUploadService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload(self, file: UploadFile, name: str | None = None, category: str | None = None) -> dict:
        log.info("上传知识库文件: %s (type=%s)", file.filename, file.content_type)
        content = await file.read()
        log.info("文件大小: %d bytes", len(content))
        if len(content) > MAX_FILE_SIZE:
            raise BusinessException(ErrorCode.BAD_REQUEST, "文件大小超过 50MB 限制")

        content_type = file.content_type or "application/octet-stream"
        if content_type not in ALLOWED_TYPES:
            raise BusinessException(ErrorCode.BAD_REQUEST, f"不支持的文件类型: {content_type}")

        # SHA-256 去重
        file_hash = hashlib.sha256(content).hexdigest()
        existing = await self.db.execute(select(KnowledgeBaseEntity).where(KnowledgeBaseEntity.file_hash == file_hash))
        existing_kb = existing.scalar_one_or_none()
        if existing_kb:
            existing_kb.access_count += 1
            await self.db.commit()
            log.info("文件已存在 (hash=%s), id=%d", file_hash[:16], existing_kb.id)
            return {"duplicate": True, "knowledgeBase": self._to_list_dto(existing_kb)}

        # 解析文本
        text = self._parse_text(content, content_type, file.filename or "unknown")
        log.info("文本解析完成, 长度=%d", len(text) if text else 0)

        # 存储文件
        storage_path = self._save_file(content, file.filename or "unknown")
        log.info("文件已保存: %s", storage_path)

        # 写入数据库
        kb = KnowledgeBaseEntity(
            file_hash=file_hash,
            name=name or file.filename or "unknown",
            category=category,
            original_filename=file.filename or "unknown",
            file_size=len(content),
            content_type=content_type,
            storage_path=storage_path,
            vector_status="PROCESSING",
        )
        self.db.add(kb)
        await self.db.commit()
        await self.db.refresh(kb)
        log.info("数据库记录已创建, id=%d, 开始向量化...", kb.id)

        # 同步向量化
        await self._vectorize(kb.id, text)

        return {"duplicate": False, "knowledgeBase": self._to_list_dto(kb)}

    async def list_all(self) -> list[dict]:
        result = await self.db.execute(select(KnowledgeBaseEntity).order_by(KnowledgeBaseEntity.uploaded_at.desc()))
        return [self._to_list_dto(kb) for kb in result.scalars().all()]

    async def get_detail(self, kb_id: int) -> dict:
        result = await self.db.execute(select(KnowledgeBaseEntity).where(KnowledgeBaseEntity.id == kb_id))
        kb = result.scalar_one_or_none()
        if not kb:
            raise BusinessException(ErrorCode.KNOWLEDGE_BASE_NOT_FOUND, f"知识库不存在: {kb_id}")
        return self._to_list_dto(kb)

    async def delete(self, kb_id: int):
        result = await self.db.execute(select(KnowledgeBaseEntity).where(KnowledgeBaseEntity.id == kb_id))
        kb = result.scalar_one_or_none()
        if not kb:
            raise BusinessException(ErrorCode.KNOWLEDGE_BASE_NOT_FOUND, f"知识库不存在: {kb_id}")

        from app.modules.knowledgebase.vector_service import VectorService
        await VectorService().delete_by_kb_id(kb_id)

        try:
            os.remove(kb.storage_path)
        except OSError:
            pass

        await self.db.delete(kb)
        await self.db.commit()

    async def revectorize(self, kb_id: int):
        result = await self.db.execute(select(KnowledgeBaseEntity).where(KnowledgeBaseEntity.id == kb_id))
        kb = result.scalar_one_or_none()
        if not kb:
            raise BusinessException(ErrorCode.KNOWLEDGE_BASE_NOT_FOUND, f"知识库不存在: {kb_id}")

        kb.vector_status = "PROCESSING"
        kb.vector_error = None
        await self.db.commit()

        text = ""
        try:
            with open(kb.storage_path, "rb") as f:
                content = f.read()
            text = self._parse_text(content, kb.content_type, kb.original_filename)
        except Exception as e:
            log.error("读取文件失败: %s", e)

        await self._vectorize(kb.id, text)

    async def get_stats(self) -> dict:
        total = await self.db.execute(select(func.count(KnowledgeBaseEntity.id)))
        completed = await self.db.execute(
            select(func.count(KnowledgeBaseEntity.id)).where(KnowledgeBaseEntity.vector_status == "COMPLETED")
        )
        processing = await self.db.execute(
            select(func.count(KnowledgeBaseEntity.id)).where(KnowledgeBaseEntity.vector_status.in_(["PENDING", "PROCESSING"]))
        )
        return KnowledgeBaseStatsDTO(
            total_count=total.scalar() or 0,
            completed_count=completed.scalar() or 0,
            processing_count=processing.scalar() or 0,
        ).model_dump()

    async def _vectorize(self, kb_id: int, text: str):
        from app.modules.knowledgebase.vector_service import VectorService
        log.info("开始向量化: kb_id=%d, text_len=%d", kb_id, len(text) if text else 0)
        try:
            chunk_count = await VectorService().vectorize_and_store(kb_id, text)
            result = await self.db.execute(select(KnowledgeBaseEntity).where(KnowledgeBaseEntity.id == kb_id))
            kb = result.scalar_one_or_none()
            if kb:
                kb.vector_status = "COMPLETED"
                kb.vector_error = None
                kb.chunk_count = chunk_count
            await self.db.commit()
            log.info("向量化完成: kb_id=%d, chunks=%d", kb_id, chunk_count)
        except Exception as e:
            log.error("向量化失败: kb_id=%d, error=%s", kb_id, e, exc_info=True)
            await self.db.rollback()
            result = await self.db.execute(select(KnowledgeBaseEntity).where(KnowledgeBaseEntity.id == kb_id))
            kb = result.scalar_one_or_none()
            if kb:
                kb.vector_status = "FAILED"
                kb.vector_error = str(e)[:500]
            await self.db.commit()
            log.info("已标记为 FAILED: kb_id=%d", kb_id)

    def _to_list_dto(self, kb: KnowledgeBaseEntity) -> dict:
        return KnowledgeBaseListItemDTO(
            id=kb.id,
            name=kb.name,
            category=kb.category,
            original_filename=kb.original_filename,
            file_size=kb.file_size,
            content_type=kb.content_type,
            uploaded_at=kb.uploaded_at,
            access_count=kb.access_count,
            question_count=kb.question_count,
            vector_status=kb.vector_status,
            vector_error=kb.vector_error,
            chunk_count=kb.chunk_count,
        ).model_dump()

    def _parse_text(self, content: bytes, content_type: str, filename: str) -> str:
        if content_type == "application/pdf":
            from PyPDF2 import PdfReader
            import io
            reader = PdfReader(io.BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        elif "word" in content_type or "document" in content_type:
            from docx import Document
            import io
            doc = Document(io.BytesIO(content))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        else:
            import chardet
            detected = chardet.detect(content)
            encoding = detected.get("encoding", "utf-8") or "utf-8"
            return content.decode(encoding, errors="replace")

    def _save_file(self, content: bytes, filename: str) -> str:
        ext = Path(filename).suffix or ".bin"
        unique_name = f"{uuid.uuid4().hex}{ext}"
        save_dir = Path(settings.storage_path)
        save_dir.mkdir(parents=True, exist_ok=True)
        file_path = save_dir / unique_name
        file_path.write_bytes(content)
        return str(file_path)
