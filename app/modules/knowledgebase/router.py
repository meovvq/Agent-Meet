"""知识库 API 路由"""

import logging

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.result import Result
from app.database.engine import get_db
from app.modules.knowledgebase.upload_service import KnowledgeBaseUploadService
from app.schemas.knowledge_base import QueryRequest

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/knowledgebase", tags=["知识库"])


@router.get("/list")
async def list_knowledge_bases(db: AsyncSession = Depends(get_db)):
    """获取知识库列表"""
    service = KnowledgeBaseUploadService(db)
    data = await service.list_all()
    return Result.success(data)


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """获取知识库统计"""
    service = KnowledgeBaseUploadService(db)
    data = await service.get_stats()
    return Result.success(data)


@router.post("/upload")
async def upload_knowledge_base(
    file: UploadFile,
    name: str | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """上传知识库文件（PDF/DOCX/TXT），自动分块 + 向量化"""
    service = KnowledgeBaseUploadService(db)
    data = await service.upload(file, name=name, category=category)
    return Result.success(data)


@router.get("/{kb_id}")
async def get_knowledge_base(kb_id: int, db: AsyncSession = Depends(get_db)):
    """获取知识库详情"""
    service = KnowledgeBaseUploadService(db)
    data = await service.get_detail(kb_id)
    return Result.success(data)


@router.delete("/{kb_id}")
async def delete_knowledge_base(kb_id: int, db: AsyncSession = Depends(get_db)):
    """删除知识库"""
    service = KnowledgeBaseUploadService(db)
    await service.delete(kb_id)
    return Result.success()


@router.post("/{kb_id}/revectorize")
async def revectorize(kb_id: int, db: AsyncSession = Depends(get_db)):
    """重新向量化"""
    service = KnowledgeBaseUploadService(db)
    await service.revectorize(kb_id)
    return Result.success()


@router.post("/query")
async def query_knowledge_base(req: QueryRequest):
    """RAG 检索 + LLM 生成回答"""
    from app.modules.knowledgebase.vector_service import VectorService

    # 1. 检索
    docs = await VectorService().similarity_search(
        query=req.question,
        kb_ids=req.knowledge_base_ids,
        top_k=5,
    )

    # 2. 用 LLM 基于检索结果生成回答
    answer = ""
    if docs:
        from app.common.llm_client import chat_completion

        context = "\n\n".join(
            f"[来源{i+1}] (相关度: {d['score']:.2f})\n{d['content']}"
            for i, d in enumerate(docs)
        )
        system_prompt = (
            "你是一个知识库问答助手。请严格基于以下检索到的参考资料回答用户问题。\n"
            "要求：\n"
            "1. 只基于参考资料中的内容回答，不要编造\n"
            "2. 回答要准确、简洁、完整\n"
            "3. 如果参考资料中没有相关信息，明确说明「知识库中未找到相关内容」\n"
            "4. 适当引用来源编号，如 [来源1]"
        )
        user_prompt = f"## 参考资料\n\n{context}\n\n## 用户问题\n\n{req.question}"

        answer = await chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=2048,
        )
    else:
        answer = "知识库中未找到相关内容"

    return Result.success(data={"answer": answer, "sources": docs})
