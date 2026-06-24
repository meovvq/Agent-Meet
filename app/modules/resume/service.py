"""简历业务逻辑

支持：文件上传（PDF/DOCX/TXT）、SHA-256 去重、文本解析、LLM 分析评分、CRUD
"""

import hashlib
import json
import logging
import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exception import BusinessException, ErrorCode
from app.config import settings
from app.models.resume import ResumeAnalysisEntity, ResumeEntity
from app.schemas.resume import AnalysisHistoryDTO, ResumeAnalysisResponse, ResumeDetailDTO, ResumeListItemDTO

log = logging.getLogger(__name__)

ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "text/markdown",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class ResumeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_and_analyze(self, file: UploadFile) -> dict:
        """上传简历并同步分析"""
        log.info("上传简历: %s (type=%s)", file.filename, file.content_type)

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise BusinessException(ErrorCode.BAD_REQUEST, "文件大小超过 10MB 限制")

        content_type = file.content_type or "application/octet-stream"
        if content_type not in ALLOWED_TYPES:
            raise BusinessException(ErrorCode.BAD_REQUEST, f"不支持的文件类型: {content_type}")

        # SHA-256 去重
        file_hash = hashlib.sha256(content).hexdigest()
        existing = await self.db.execute(select(ResumeEntity).where(ResumeEntity.file_hash == file_hash))
        existing_resume = existing.scalar_one_or_none()
        if existing_resume:
            existing_resume.access_count += 1
            await self.db.commit()
            log.info("简历已存在 (hash=%s), id=%d", file_hash[:16], existing_resume.id)
            analysis = await self._get_latest_analysis(existing_resume.id)
            return {
                "duplicate": True,
                "resume": {"id": existing_resume.id, "filename": existing_resume.original_filename, "analyzeStatus": existing_resume.analyze_status},
                "analysis": analysis,
            }

        # 解析文本
        resume_text = self._parse_text(content, content_type, file.filename or "unknown")

        # 存储文件
        storage_path = self._save_file(content, file.filename or "unknown")

        # 持久化
        resume = ResumeEntity(
            file_hash=file_hash,
            original_filename=file.filename or "unknown",
            file_size=len(content),
            content_type=content_type,
            storage_path=storage_path,
            resume_text=resume_text,
            analyze_status="PROCESSING",
        )
        self.db.add(resume)
        await self.db.commit()
        await self.db.refresh(resume)

        # 同步调用 LLM 分析
        await self._analyze(resume.id, resume_text or "")

        return {
            "duplicate": False,
            "resume": {"id": resume.id, "filename": resume.original_filename, "analyzeStatus": "COMPLETED"},
        }

    async def list_all(self) -> list[dict]:
        result = await self.db.execute(select(ResumeEntity).order_by(ResumeEntity.uploaded_at.desc()))
        resumes = result.scalars().all()
        items = []
        for r in resumes:
            analysis = await self._get_latest_analysis(r.id)
            items.append(ResumeListItemDTO(
                id=r.id,
                filename=r.original_filename,
                file_size=r.file_size,
                uploaded_at=r.uploaded_at,
                access_count=r.access_count,
                latest_score=analysis.get("overall_score") if analysis else None,
                analyze_status=r.analyze_status,
                analyze_error=r.analyze_error,
            ).model_dump())
        return items

    async def get_detail(self, resume_id: int) -> dict:
        result = await self.db.execute(select(ResumeEntity).where(ResumeEntity.id == resume_id))
        resume = result.scalar_one_or_none()
        if not resume:
            raise BusinessException(ErrorCode.RESUME_NOT_FOUND, f"简历不存在: {resume_id}")

        analyses_result = await self.db.execute(
            select(ResumeAnalysisEntity)
            .where(ResumeAnalysisEntity.resume_id == resume_id)
            .order_by(ResumeAnalysisEntity.analyzed_at.desc())
        )
        analyses = []
        for a in analyses_result.scalars().all():
            analyses.append(AnalysisHistoryDTO(
                id=a.id,
                overall_score=a.overall_score,
                content_score=a.content_score,
                structure_score=a.structure_score,
                skill_match_score=a.skill_match_score,
                expression_score=a.expression_score,
                project_score=a.project_score,
                summary=a.summary,
                analyzed_at=a.analyzed_at,
                strengths=json.loads(a.strengths_json) if a.strengths_json else [],
                suggestions=json.loads(a.suggestions_json) if a.suggestions_json else [],
            ).model_dump())

        return ResumeDetailDTO(
            id=resume.id,
            filename=resume.original_filename,
            file_size=resume.file_size,
            content_type=resume.content_type,
            uploaded_at=resume.uploaded_at,
            access_count=resume.access_count,
            resume_text=resume.resume_text,
            analyze_status=resume.analyze_status,
            analyze_error=resume.analyze_error,
            analyses=analyses,
        ).model_dump()

    async def get_resume_text(self, resume_id: int) -> str:
        """获取简历纯文本（供 Agent 工具调用）"""
        result = await self.db.execute(select(ResumeEntity).where(ResumeEntity.id == resume_id))
        resume = result.scalar_one_or_none()
        if not resume:
            raise BusinessException(ErrorCode.RESUME_NOT_FOUND, f"简历不存在: {resume_id}")
        return resume.resume_text or ""

    async def delete(self, resume_id: int):
        result = await self.db.execute(select(ResumeEntity).where(ResumeEntity.id == resume_id))
        resume = result.scalar_one_or_none()
        if not resume:
            raise BusinessException(ErrorCode.RESUME_NOT_FOUND, f"简历不存在: {resume_id}")
        try:
            os.remove(resume.storage_path)
        except OSError:
            pass
        await self.db.delete(resume)
        await self.db.commit()

    async def reanalyze(self, resume_id: int):
        result = await self.db.execute(select(ResumeEntity).where(ResumeEntity.id == resume_id))
        resume = result.scalar_one_or_none()
        if not resume:
            raise BusinessException(ErrorCode.RESUME_NOT_FOUND, f"简历不存在: {resume_id}")
        resume.analyze_status = "PROCESSING"
        resume.analyze_error = None
        await self.db.commit()
        await self._analyze(resume.id, resume.resume_text or "")

    async def _analyze(self, resume_id: int, content: str):
        """调用 LLM 分析简历"""
        from app.common.llm_client import chat_completion_json
        try:
            system_prompt = "你是简历分析专家。分析候选人简历，返回 JSON 格式评分。"
            user_prompt = f"""请分析以下简历，返回 JSON 格式：
{{
  "overall_score": 0-100,
  "score_detail": {{
    "content_score": 0-100,
    "structure_score": 0-100,
    "skill_match_score": 0-100,
    "expression_score": 0-100,
    "project_score": 0-100
  }},
  "summary": "总体评价",
  "strengths": ["强项1", "强项2"],
  "suggestions": ["建议1", "建议2"]
}}

简历内容：
{content[:6000]}"""

            data = await chat_completion_json(system_prompt, user_prompt, temperature=0.3)

            result = await self.db.execute(select(ResumeEntity).where(ResumeEntity.id == resume_id))
            resume = result.scalar_one_or_none()
            if not resume:
                return

            score_detail = data.get("score_detail", data.get("scoreDetail", {}))
            analysis = ResumeAnalysisEntity(
                resume_id=resume_id,
                overall_score=data.get("overall_score", data.get("overallScore", 0)),
                content_score=score_detail.get("content_score", score_detail.get("contentScore", 0)),
                structure_score=score_detail.get("structure_score", score_detail.get("structureScore", 0)),
                skill_match_score=score_detail.get("skill_match_score", score_detail.get("skillMatchScore", 0)),
                expression_score=score_detail.get("expression_score", score_detail.get("expressionScore", 0)),
                project_score=score_detail.get("project_score", score_detail.get("projectScore", 0)),
                summary=data.get("summary", ""),
                strengths_json=json.dumps(data.get("strengths", []), ensure_ascii=False),
                suggestions_json=json.dumps(data.get("suggestions", []), ensure_ascii=False),
            )
            self.db.add(analysis)
            resume.analyze_status = "COMPLETED"
            resume.analyze_error = None
            await self.db.commit()

        except Exception as e:
            log.error("简历分析失败: %s", e)
            await self.db.rollback()
            result = await self.db.execute(select(ResumeEntity).where(ResumeEntity.id == resume_id))
            resume = result.scalar_one_or_none()
            if resume:
                resume.analyze_status = "FAILED"
                resume.analyze_error = str(e)[:500]
            await self.db.commit()

    async def _get_latest_analysis(self, resume_id: int) -> dict | None:
        result = await self.db.execute(
            select(ResumeAnalysisEntity)
            .where(ResumeAnalysisEntity.resume_id == resume_id)
            .order_by(ResumeAnalysisEntity.analyzed_at.desc())
            .limit(1)
        )
        a = result.scalar_one_or_none()
        if not a:
            return None
        return ResumeAnalysisResponse(
            overall_score=a.overall_score,
            score_detail={
                "project_score": a.project_score,
                "skill_match_score": a.skill_match_score,
                "content_score": a.content_score,
                "structure_score": a.structure_score,
                "expression_score": a.expression_score,
            },
            summary=a.summary or "",
            strengths=json.loads(a.strengths_json) if a.strengths_json else [],
            suggestions=json.loads(a.suggestions_json) if a.suggestions_json else [],
        ).model_dump()

    def _parse_text(self, content: bytes, content_type: str, filename: str) -> str:
        if content_type == "application/pdf":
            return self._parse_pdf(content)
        elif "word" in content_type or "document" in content_type:
            return self._parse_docx(content)
        else:
            import chardet
            detected = chardet.detect(content)
            encoding = detected.get("encoding", "utf-8") or "utf-8"
            return content.decode(encoding, errors="replace")

    def _parse_pdf(self, content: bytes) -> str:
        from PyPDF2 import PdfReader
        import io
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    def _parse_docx(self, content: bytes) -> str:
        from docx import Document
        import io
        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    def _save_file(self, content: bytes, filename: str) -> str:
        ext = Path(filename).suffix or ".bin"
        unique_name = f"{uuid.uuid4().hex}{ext}"
        save_dir = Path(settings.storage_path)
        save_dir.mkdir(parents=True, exist_ok=True)
        file_path = save_dir / unique_name
        file_path.write_bytes(content)
        return str(file_path)
