"""知识库相关 Schema"""

from datetime import datetime

from pydantic import BaseModel


class KnowledgeBaseListItemDTO(BaseModel):
    id: int
    name: str
    category: str | None = None
    original_filename: str
    file_size: int
    content_type: str
    uploaded_at: datetime
    access_count: int
    question_count: int
    vector_status: str
    vector_error: str | None = None
    chunk_count: int = 0


class KnowledgeBaseStatsDTO(BaseModel):
    total_count: int = 0
    completed_count: int = 0
    processing_count: int = 0
    total_question_count: int = 0
    total_access_count: int = 0


class QueryRequest(BaseModel):
    knowledge_base_ids: list[int]
    question: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]
