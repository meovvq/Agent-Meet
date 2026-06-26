"""简历相关 Schema

定义简历模块的请求/响应数据模型：
- ResumeListItemDTO      — 简历列表项（列表页展示）
- AnalysisHistoryDTO     — 单次分析记录详情
- ResumeDetailDTO        — 简历详情（含分析历史）
- ResumeAnalysisResponse — 简历分析结果响应
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ResumeListItemDTO(BaseModel):
    """简历列表项 DTO

    用于 GET /api/resume 列表接口的响应，
    展示每份简历的基本信息和分析状态。
    """
    id: int                              # 简历 ID
    filename: str                        # 文件名
    file_size: int                       # 文件大小（字节）
    uploaded_at: datetime                # 上传时间
    access_count: int                    # 被引用次数（面试中使用次数）
    latest_score: int | None = None      # 最新一次分析的总分（未分析时为 None）
    analyze_status: str                  # 分析状态：PENDING / PROCESSING / COMPLETED / ERROR
    analyze_error: str | None = None     # 分析失败的错误信息


class AnalysisHistoryDTO(BaseModel):
    """单次简历分析记录 DTO

    对应一次完整的简历分析结果，包含多维度评分和改进建议。
    """
    id: int                              # 分析记录 ID
    overall_score: int                   # 综合评分（0-100）
    content_score: int                   # 内容丰富度评分
    structure_score: int                 # 结构清晰度评分
    skill_match_score: int               # 技能匹配度评分
    expression_score: int                # 表达规范性评分
    project_score: int                   # 项目经验评分
    summary: str | None = None           # LLM 生成的综合评语
    analyzed_at: datetime                # 分析时间
    strengths: list[str] = []            # 优势列表
    suggestions: list[Any] = []          # 改进建议列表


class ResumeDetailDTO(BaseModel):
    """简历详情 DTO

    用于 GET /api/resume/{id} 详情接口的响应，
    包含简历全文和所有历史分析记录。
    """
    id: int                              # 简历 ID
    filename: str                        # 文件名
    file_size: int                       # 文件大小（字节）
    content_type: str                    # 文件 MIME 类型
    uploaded_at: datetime                # 上传时间
    access_count: int                    # 被引用次数
    resume_text: str | None = None       # 提取的简历全文（OCR/解析后）
    analyze_status: str                  # 分析状态
    analyze_error: str | None = None     # 分析失败的错误信息
    analyses: list[AnalysisHistoryDTO] = []  # 历史分析记录列表（按时间倒序）


class ResumeAnalysisResponse(BaseModel):
    """简历分析结果响应

    用于 POST /api/resume/{id}/analyze 接口的响应，
    返回单次分析的评分和建议。
    """
    overall_score: int = 0               # 综合评分（0-100）
    score_detail: dict = {}              # 各维度评分明细
    summary: str = ""                    # 综合评语
    strengths: list[str] = []            # 优势列表
    suggestions: list[Any] = []          # 改进建议列表
