"""知识库相关 Schema

定义知识库模块的请求/响应数据模型：
- KnowledgeBaseListItemDTO — 知识库列表项（列表页展示）
- KnowledgeBaseStatsDTO   — 知识库统计摘要（概览面板）
- QueryRequest            — 知识库检索请求
- QueryResponse           — 知识库检索响应
"""

from datetime import datetime

from pydantic import BaseModel


class KnowledgeBaseListItemDTO(BaseModel):
    """知识库列表项 DTO

    用于 GET /api/knowledgebase 列表接口的响应，
    展示每个知识库的基本信息和处理状态。
    """
    id: int                              # 知识库 ID
    name: str                            # 知识库名称
    category: str | None = None          # 分类标签（如 "java", "python"）
    original_filename: str               # 原始文件名
    file_size: int                       # 文件大小（字节）
    content_type: str                    # 文件 MIME 类型（如 "application/pdf"）
    uploaded_at: datetime                # 上传时间
    access_count: int                    # 被检索次数
    question_count: int                  # 关联的题目数量
    vector_status: str                   # 向量化状态：PENDING / PROCESSING / COMPLETED / ERROR
    vector_error: str | None = None      # 向量化失败的错误信息
    chunk_count: int = 0                 # 向量化后的分块数量


class KnowledgeBaseStatsDTO(BaseModel):
    """知识库统计摘要 DTO

    用于首页或概览面板，展示知识库整体情况。
    """
    total_count: int = 0                 # 知识库总数
    completed_count: int = 0             # 已完成向量化的数量
    processing_count: int = 0            # 正在处理中的数量
    total_question_count: int = 0        # 所有知识库的题目总数
    total_access_count: int = 0          # 所有知识库的累计检索次数


class QueryRequest(BaseModel):
    """知识库检索请求

    用于 POST /api/knowledgebase/query 接口，
    指定要检索的知识库 ID 列表和查询问题。
    """
    knowledge_base_ids: list[int]        # 要检索的知识库 ID 列表
    question: str                        # 查询问题文本


class QueryResponse(BaseModel):
    """知识库检索响应

    返回检索到的回答文本和来源文档列表。
    """
    answer: str                          # 基于检索结果生成的回答
    sources: list[dict]                  # 来源文档列表（含 content, score 等）
