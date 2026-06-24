"""简历 API 路由"""

import logging

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.result import Result
from app.database.engine import get_db
from app.modules.resume.service import ResumeService

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/resumes", tags=["简历"])


@router.post("/upload")
async def upload_resume(file: UploadFile, db: AsyncSession = Depends(get_db)):
    """上传简历（PDF/DOCX/TXT），自动解析 + LLM 分析"""
    service = ResumeService(db)
    data = await service.upload_and_analyze(file)
    return Result.success(data)


@router.get("")
async def list_resumes(db: AsyncSession = Depends(get_db)):
    """获取简历列表"""
    service = ResumeService(db)
    data = await service.list_all()
    return Result.success(data)


@router.get("/{resume_id}/detail")
async def get_resume_detail(resume_id: int, db: AsyncSession = Depends(get_db)):
    """获取简历详情（含分析历史）"""
    service = ResumeService(db)
    data = await service.get_detail(resume_id)
    return Result.success(data)


@router.delete("/{resume_id}")
async def delete_resume(resume_id: int, db: AsyncSession = Depends(get_db)):
    """删除简历"""
    service = ResumeService(db)
    await service.delete(resume_id)
    return Result.success()


@router.post("/{resume_id}/reanalyze")
async def reanalyze_resume(resume_id: int, db: AsyncSession = Depends(get_db)):
    """重新分析简历"""
    service = ResumeService(db)
    await service.reanalyze(resume_id)
    return Result.success()
