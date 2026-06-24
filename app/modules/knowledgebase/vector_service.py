"""向量化与混合检索（pgvector + BM25 + RRF）

分块策略：
1. 空行不急着切 → 长度阈值保护 → 标题和正文不拆散
2. chunk 重叠 80 字符 → 上下文连续，检索时能命中完整语义
3. chunk_size=300 tokens → 适合 Q&A 结构，减少话题混杂

检索策略：
1. 向量检索（余弦相似度）→ 语义匹配
2. BM25 关键词检索 → 精确匹配专有名词
3. RRF 融合排序 → 综合两种信号
"""

import asyncio
import json
import logging
import re
import time

from rank_bm25 import BM25Okapi

from app.common.llm_client import get_embedding, get_embeddings
from app.config import settings
from app.database.engine import async_session

log = logging.getLogger(__name__)

CHUNK_SIZE = 300       # 约 300 tokens（1200 字符），适合 Q&A 结构
CHUNK_OVERLAP = 80     # chunk 重叠字符数，防止标题与正文被拆散
CHUNK_BATCH_SIZE = 10  # 每批向量化数量
BM25_CACHE_TTL = 300   # BM25 索引缓存过期时间（秒）

_HAS_PGVECTOR = False
VectorStore = None

try:
    from pgvector.sqlalchemy import Vector
    from sqlalchemy import Column, Integer, String, Text, delete, select, text
    from app.database.engine import Base

    class VectorStore(Base):
        __tablename__ = "vector_store"
        id = Column(Integer, primary_key=True, autoincrement=True)
        content = Column(Text)
        metadata_ = Column("metadata", String)
        embedding = Column(Vector(settings.embedding_dimensions))

    _HAS_PGVECTOR = True
except ImportError:
    log.warning("pgvector 未安装，知识库向量功能不可用")


class VectorService:
    """向量化服务（支持向量 + BM25 混合检索）"""

    # BM25 索引缓存: {kb_id: (bm25_index, corpus_texts, timestamp)}
    _bm25_cache: dict[int, tuple] = {}

    async def vectorize_and_store(self, kb_id: int, content: str) -> int:
        """分块 + 向量化 + 存储，返回 chunk 数量"""
        if not _HAS_PGVECTOR:
            log.warning("pgvector 不可用，跳过向量化")
            return 0

        await self.delete_by_kb_id(kb_id)

        # 分块
        chunks = self._split_text(content)
        if not chunks:
            log.warning("分块结果为空: kb_id=%d, content_len=%d", kb_id, len(content))
            return 0

        chunk_lens = [len(c) for c in chunks]
        log.info(
            "分块完成: kb_id=%d, content_len=%d, chunks=%d | "
            "chunk_len: min=%d, max=%d, avg=%d, median=%d",
            kb_id, len(content), len(chunks),
            min(chunk_lens), max(chunk_lens),
            sum(chunk_lens) // len(chunk_lens), sorted(chunk_lens)[len(chunk_lens) // 2],
        )
        # 打印前 3 个 chunk 的预览
        for i, c in enumerate(chunks[:3]):
            log.info("  chunk[%d] len=%d preview=%s", i, len(c), c[:100].replace("\n", " "))

        # 批量向量化并存储
        total_stored = 0
        for i in range(0, len(chunks), CHUNK_BATCH_SIZE):
            batch = chunks[i: i + CHUNK_BATCH_SIZE]
            log.info("批量向量化: kb_id=%d, batch %d-%d / %d", kb_id, i, i + len(batch), len(chunks))
            embeddings = await get_embeddings(batch)

            async with async_session() as db:
                for text_content, embedding in zip(batch, embeddings):
                    vec = VectorStore(
                        content=text_content,
                        metadata_=json.dumps({"kb_id": str(kb_id)}),
                        embedding=embedding,
                    )
                    db.add(vec)
                await db.commit()
                total_stored += len(batch)

        log.info("向量化存储完成: kb_id=%d, total_stored=%d", kb_id, total_stored)
        return total_stored

    async def similarity_search(
        self, query: str, kb_ids: list[int] | None = None,
        top_k: int = 8, min_score: float = 0.40,
    ) -> list[dict]:
        """混合检索：向量相似度 + BM25 关键词，RRF 融合排序

        Args:
            query: 查询文本
            kb_ids: 知识库 ID 列表，为空时检索全部
            top_k: 返回结果数量
            min_score: 最小相似度分数（余弦相似度）

        Returns:
            检索结果列表，每项包含 content 和 score
        """
        if not _HAS_PGVECTOR:
            log.warning("pgvector 不可用，跳过检索")
            return []

        # 扩大向量检索范围，为 RRF 融合留足候选
        vector_top_k = top_k * 4

        # ---- 1. 向量检索 ----
        query_embedding = await get_embedding(query)
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        async with async_session() as db:
            if kb_ids:
                sql = text("""
                    SELECT id, content, metadata, 1 - (embedding <=> CAST(:query_embedding AS vector)) AS score
                    FROM vector_store
                    WHERE CAST(metadata AS jsonb)->>'kb_id' = ANY(:kb_ids)
                    ORDER BY embedding <=> CAST(:query_embedding AS vector)
                    LIMIT :top_k
                """)
                result = await db.execute(sql, {
                    "query_embedding": embedding_str,
                    "kb_ids": [str(kid) for kid in kb_ids],
                    "top_k": vector_top_k,
                })
            else:
                sql = text("""
                    SELECT id, content, metadata, 1 - (embedding <=> CAST(:query_embedding AS vector)) AS score
                    FROM vector_store
                    ORDER BY embedding <=> CAST(:query_embedding AS vector)
                    LIMIT :top_k
                """)
                result = await db.execute(sql, {
                    "query_embedding": embedding_str,
                    "top_k": vector_top_k,
                })
            rows = result.fetchall()

        vector_results = []
        for row in rows:
            score = float(row.score)
            if score >= min_score:
                vector_results.append({
                    "id": row.id,
                    "content": row.content,
                    "vector_score": score,
                    "metadata": row.metadata,
                })

        # ---- 2. BM25 检索 ----
        bm25_results = await self._bm25_search(query, kb_ids, top_k=vector_top_k)

        # ---- 3. RRF 融合 ----
        docs = self._rrf_fusion(vector_results, bm25_results, top_k=top_k, query=query)

        # ---- 4. 日志 ----
        log.info(
            "混合检索: query='%s' | 向量命中=%d, BM25命中=%d, 融合后=%d",
            query[:50], len(vector_results), len(bm25_results), len(docs),
        )
        for i, doc in enumerate(docs):
            log.info(
                "  doc[%d] rrf_score=%.6f vector=%.4f bm25_rank=%s preview=%s",
                i, doc["score"], doc.get("vector_score", 0),
                doc.get("bm25_rank", "-"), doc["content"][:80].replace("\n", " "),
            )

        return docs

    # ========== BM25 检索 ==========

    async def _bm25_search(
        self, query: str, kb_ids: list[int] | None = None, top_k: int = 20,
    ) -> list[dict]:
        """BM25 关键词检索"""
        bm25_index, corpus_texts, corpus_ids = await self._get_bm25_index(kb_ids)
        if not bm25_index:
            return []

        # 简单分词：按字符级别 + 空格切分，适配中英文混合
        query_tokens = self._tokenize(query)
        scores = bm25_index.get_scores(query_tokens)

        # 按分数排序取 top_k
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in ranked_indices:
            if scores[idx] > 0:
                results.append({
                    "id": corpus_ids[idx],
                    "content": corpus_texts[idx],
                    "bm25_score": float(scores[idx]),
                })
        return results

    async def _get_bm25_index(
        self, kb_ids: list[int] | None = None,
    ) -> tuple:
        """获取或构建 BM25 索引（带缓存）"""
        cache_key = tuple(sorted(kb_ids)) if kb_ids else None
        now = time.time()

        # 检查缓存
        if cache_key in self._bm25_cache:
            bm25, corpus_data, ts = self._bm25_cache[cache_key]
            if now - ts < BM25_CACHE_TTL:
                cached_ids = [t[0] for t in corpus_data]
                cached_texts = [t[1] for t in corpus_data]
                return bm25, cached_texts, cached_ids

        # 从数据库加载语料
        async with async_session() as db:
            if kb_ids:
                sql = text("""
                    SELECT id, content FROM vector_store
                    WHERE CAST(metadata AS jsonb)->>'kb_id' = ANY(:kb_ids)
                """)
                result = await db.execute(sql, {"kb_ids": [str(kid) for kid in kb_ids]})
            else:
                sql = text("SELECT id, content FROM vector_store")
                result = await db.execute(sql)
            rows = result.fetchall()

        if not rows:
            return None, [], []

        corpus_ids = [row.id for row in rows]
        corpus_texts = [row.content for row in rows]
        tokenized_corpus = [self._tokenize(doc) for doc in corpus_texts]

        bm25 = BM25Okapi(tokenized_corpus)

        # 更新缓存（存储 id 和 content 的配对）
        corpus_data = list(zip(corpus_ids, corpus_texts))
        self._bm25_cache[cache_key] = (bm25, corpus_data, now)

        log.info("BM25 索引构建完成: kb_ids=%s, corpus_size=%d", kb_ids, len(corpus_texts))
        return bm25, corpus_texts, corpus_ids

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """中英文混合分词：保留英文短语 + 汉字 + 数字，同时生成 bigram"""
        # 1. 提取基本 token：连续中文、连续英文词（含连字符）、数字
        raw = re.findall(r'[一-鿿]+|[a-zA-Z](?:[a-zA-Z''-]*[a-zA-Z])?|[0-9]+', text)
        tokens = [t.lower() for t in raw if len(t) > 0]

        # 2. 对英文词生成 bigram（如 "lost in the middle" → "lost_in", "in_the", "the_middle"）
        english_words = [t for t in tokens if re.match(r'^[a-zA-Z]', t)]
        if len(english_words) >= 2:
            for i in range(len(english_words) - 1):
                tokens.append(f"{english_words[i]}_{english_words[i+1]}")

        # 3. 对中文生成 bigram（如 "上下文窗口" → "上下", "下文", "文窗", "窗口"）
        chinese_chars = [t for t in tokens if re.match(r'^[一-鿿]', t)]
        for seg in chinese_chars:
            if len(seg) >= 2:
                for i in range(len(seg) - 1):
                    tokens.append(seg[i:i+2])

        return tokens

    @staticmethod
    def _rrf_fusion(
        vector_results: list[dict],
        bm25_results: list[dict],
        top_k: int = 8,
        k: int = 60,
        query: str = "",
    ) -> list[dict]:
        """RRF (Reciprocal Rank Fusion) 融合向量和 BM25 检索结果

        公式: score = 1/(k + rank_vector) + 1/(k + rank_bm25) + overlap_bonus
        overlap_bonus: 查询词在文档中出现的比例加分
        """
        # 按 content 去重，建立统一的文档池
        doc_pool: dict[str, dict] = {}

        for rank, doc in enumerate(vector_results):
            key = doc["content"]
            if key not in doc_pool:
                doc_pool[key] = {**doc, "vector_rank": rank + 1, "bm25_rank": None}
            else:
                doc_pool[key]["vector_rank"] = rank + 1
                doc_pool[key]["vector_score"] = doc["vector_score"]

        for rank, doc in enumerate(bm25_results):
            key = doc["content"]
            if key not in doc_pool:
                doc_pool[key] = {**doc, "vector_rank": None, "bm25_rank": rank + 1}
            else:
                doc_pool[key]["bm25_rank"] = rank + 1

        # 提取查询关键词（用于重叠加分）
        query_terms = set()
        if query:
            # 英文短语
            en_words = re.findall(r'[a-zA-Z]+', query.lower())
            query_terms.update(en_words)
            # 中文 bigram
            cn_segments = re.findall(r'[一-鿿]+', query)
            for seg in cn_segments:
                if len(seg) >= 2:
                    for i in range(len(seg) - 1):
                        query_terms.add(seg[i:i+2])
                else:
                    query_terms.add(seg)
            # 完整查询（用于精确匹配）
            query_terms.add(query.lower().strip())

        # 计算 RRF 分数 + 查询重叠加分
        # 权重：向量 1.5x，BM25 1.0x（向量语义匹配更可靠）
        VECTOR_WEIGHT = 1.5
        BM25_WEIGHT = 1.0
        for doc in doc_pool.values():
            rrf = 0.0
            if doc["vector_rank"] is not None:
                rrf += VECTOR_WEIGHT / (k + doc["vector_rank"])
            if doc["bm25_rank"] is not None:
                rrf += BM25_WEIGHT / (k + doc["bm25_rank"])

            # 查询重叠加分：查询词在文档中出现的比例
            if query_terms:
                content_lower = doc["content"].lower()
                matched = sum(1 for t in query_terms if t in content_lower)
                overlap_ratio = matched / len(query_terms)
                rrf += overlap_ratio * 0.005  # 小幅加分，不主导排序

            doc["score"] = rrf

        # 按 RRF 分数排序
        sorted_docs = sorted(doc_pool.values(), key=lambda d: d["score"], reverse=True)[:top_k]

        # 清理内部字段
        return [
            {
                "content": d["content"],
                "score": d["score"],
                "vector_score": d.get("vector_score"),
                "bm25_rank": d.get("bm25_rank"),
            }
            for d in sorted_docs
        ]

    async def delete_by_kb_id(self, kb_id: int):
        """删除指定知识库的所有向量"""
        if not _HAS_PGVECTOR:
            return
        try:
            async with asyncio.timeout(10):
                async with async_session() as db:
                    try:
                        await db.execute(
                            delete(VectorStore).where(
                                text("CAST(metadata AS jsonb)->>'kb_id' = :kb_id")
                            ),
                            {"kb_id": str(kb_id)},
                        )
                        await db.commit()
                        # 清除该知识库的 BM25 缓存
                        cache_key = (kb_id,)
                        self._bm25_cache.pop(cache_key, None)
                        self._bm25_cache.pop(None, None)  # 全量缓存也清除
                        log.info("已删除知识库 %d 的向量", kb_id)
                    except Exception:
                        await db.rollback()
                        raise
        except Exception as e:
            log.warning("删除向量失败 kb_id=%s: %s", kb_id, e)

    def _split_text(self, text: str) -> list[str]:
        """智能分块：按 Markdown 标题结构切分，每个 chunk 尽量是一个完整的 Q&A 或段落

        策略：
        1. 优先按 ## / ### 标题切分（保留标题与正文不拆散）
        2. 单个 section 超长时，按段落二次切分
        3. chunk 重叠 100 字符 → 上下文连续，检索时能命中完整语义
        """
        if not text or not text.strip():
            return []

        max_chars = CHUNK_SIZE * 4  # 粗略 1 token ≈ 4 chars

        # 第一步：按 Markdown 标题切分
        sections = self._split_by_headers(text)

        # 第二步：合并过短的 section，拆分过长的 section
        raw_chunks = []
        current = ""
        for section in sections:
            # 如果当前 + 新 section 不超限，合并
            if current and len(current) + len(section) < max_chars:
                current += "\n\n" + section
            else:
                # 先 flush 当前
                if current:
                    raw_chunks.append(current.strip())
                # 如果单个 section 超长，按段落二次切分
                if len(section) > max_chars:
                    sub_chunks = self._split_by_paragraphs(section, max_chars)
                    raw_chunks.extend(sub_chunks)
                    current = ""
                else:
                    current = section

        if current.strip():
            raw_chunks.append(current.strip())

        # 第三步：添加 chunk 重叠
        if CHUNK_OVERLAP > 0 and len(raw_chunks) > 1:
            chunks = [raw_chunks[0]]
            for i in range(1, len(raw_chunks)):
                prev = raw_chunks[i - 1]
                overlap_text = prev[-CHUNK_OVERLAP:] if len(prev) > CHUNK_OVERLAP else prev
                # 在重叠处找一个自然断句点
                for sep in ["\n", "。", "！", "？", "；"]:
                    idx = overlap_text.find(sep)
                    if idx >= 0:
                        overlap_text = overlap_text[idx + 1:]
                        break
                chunks.append(overlap_text + "\n" + raw_chunks[i] if overlap_text else raw_chunks[i])
            return [c.strip() for c in chunks if c.strip()]

        return [c for c in raw_chunks if c]

    def _split_by_headers(self, text: str) -> list[str]:
        """按 Markdown 标题（## / ###）切分，保留标题与下方内容在一起"""
        import re
        # 匹配 ## 或 ### 开头的行作为分割点
        parts = re.split(r'(?=^#{2,3}\s)', text, flags=re.MULTILINE)
        # 过滤空块，strip 每块
        return [p.strip() for p in parts if p.strip()]

    def _split_by_paragraphs(self, text: str, max_chars: int) -> list[str]:
        """按段落切分长文本，空行不急着切，长度阈值保护"""
        raw_chunks = []
        current = ""

        for para in text.split("\n"):
            para_stripped = para.strip()
            if not para_stripped:
                # 空行：只有当 current 已经足够长时才 flush
                if current and len(current) > max_chars * 0.6:
                    raw_chunks.append(current.strip())
                    current = ""
                else:
                    current += "\n"
                continue

            if len(current) + len(para_stripped) < max_chars:
                current += "\n" + para_stripped if current else para_stripped
            else:
                if current:
                    raw_chunks.append(current.strip())
                # 单段落超长，按标点切分
                if len(para_stripped) > max_chars:
                    raw_chunks.extend(self._split_by_punctuation(para_stripped))
                    current = ""
                else:
                    current = para_stripped

        if current.strip():
            raw_chunks.append(current.strip())
        return raw_chunks

    def _split_by_punctuation(self, text: str) -> list[str]:
        """按标点符号切分长文本"""
        sentences = re.split(r'([。！？；\n])', text)
        chunks = []
        current = ""
        for part in sentences:
            if len(current) + len(part) < CHUNK_SIZE * 4:
                current += part
            else:
                if current:
                    chunks.append(current.strip())
                current = part
        if current.strip():
            chunks.append(current.strip())
        return chunks
