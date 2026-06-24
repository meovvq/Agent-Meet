"""知识库服务模块

提供混合检索（向量 + BM25）和知识库查询功能。
复用 knowledgebase.vector_service 的混合检索能力，避免重复实现。
"""

import logging
from typing import Optional

from app.common.llm_client import chat_completion, get_embedding

log = logging.getLogger(__name__)

# 复用 VectorService（已内置混合检索 + BM25 + RRF）
from app.modules.knowledgebase.vector_service import VectorService

_HAS_PGVECTOR = True
try:
    from pgvector.sqlalchemy import Vector  # noqa: F401 — 仅检测是否可用
except ImportError:
    _HAS_PGVECTOR = False
    log.warning("pgvector 未安装，知识库检索功能不可用")


# ========== 知识库服务 ==========

class KnowledgeBaseService:
    """知识库检索服务（委托 VectorService 执行混合检索）"""

    def __init__(self):
        self._vector_service = VectorService()

    async def search(
        self,
        query: str,
        skill_id: str = "",
        top_k: int = 3,
        min_score: float = 0.40,
    ) -> list[dict]:
        """混合检索：向量 + BM25 + RRF 融合

        Args:
            query: 查询文本
            skill_id: 技能领域 ID（暂未使用，预留）
            top_k: 返回结果数量
            min_score: 最小相似度分数（余弦相似度阈值）

        Returns:
            检索结果列表，每项包含 content 和 score
        """
        if not _HAS_PGVECTOR:
            log.warning("pgvector 不可用，跳过知识库检索")
            return []

        try:
            # 直接复用 VectorService 的混合检索（不传 kb_ids，检索全部）
            docs = await self._vector_service.similarity_search(
                query=query,
                kb_ids=None,
                top_k=top_k,
                min_score=min_score,
            )
            return docs

        except Exception as e:
            log.error("知识库检索失败: %s", e, exc_info=True)
            return []

    async def query_with_context(
        self,
        question: str,
        skill_id: str = "",
        top_k: int = 3,
    ) -> str:
        """查询知识库并生成带上下文的回答

        Args:
            question: 用户问题
            skill_id: 技能领域 ID
            top_k: 检索结果数量

        Returns:
            格式化的参考资料文本
        """
        docs = await self.search(question, skill_id, top_k)
        if not docs:
            return "知识库中未找到相关资料"

        # 格式化检索结果
        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"[来源{i}] (相关度: {doc['score']:.2f})\n{doc['content']}")

        return "\n\n".join(context_parts)


# 全局单例
knowledge_base_service = KnowledgeBaseService()
