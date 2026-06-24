"""面试模块 Schema（请求/响应模型）"""

from datetime import datetime

from pydantic import BaseModel


# ========== 请求模型 ==========

class StartInterviewRequest(BaseModel):
    """启动面试请求

    questions 为可选：如果不传或为空，自动调用出题引擎生成。
    question_count 仅在自动生成时生效。
    """
    session_id: str
    skill_id: str
    difficulty: str = "medium"
    questions: list[dict] | None = None
    question_count: int = 5
    resume_text: str = ""
    agent_mode: bool = True


class SubmitAnswerRequest(BaseModel):
    """提交答案请求"""
    answer: str


# ========== 响应模型 ==========

class InterviewQuestionDTO(BaseModel):
    """题目 DTO"""
    question: str = ""
    category: str = ""
    is_follow_up: bool = False


class SessionListItemDTO(BaseModel):
    """会话列表项"""
    session_id: str
    skill_id: str
    difficulty: str
    total_questions: int
    status: str
    evaluate_status: str = "PENDING"
    overall_score: float | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class InterviewSessionDTO(BaseModel):
    """会话详情"""
    session_id: str
    skill_id: str = ""
    difficulty: str = ""
    total_questions: int = 0
    current_question_index: int = 0
    status: str = ""
    agent_mode: bool = False
    questions: list[InterviewQuestionDTO] = []
    created_at: datetime | None = None
    completed_at: datetime | None = None


class InterviewAnswerDTO(BaseModel):
    """单题答案 DTO"""
    question_index: int
    question: str = ""
    category: str = ""
    is_follow_up: bool = False
    user_answer: str = ""
    score: float | None = None
    feedback: str | None = None
    reference_answer: str | None = None
    key_points: list[str] = []


class InterviewDetailDTO(BaseModel):
    """会话详情（含答题记录）"""
    session_id: str
    skill_id: str
    difficulty: str
    total_questions: int
    status: str
    evaluate_status: str = "PENDING"
    overall_score: float | None = None
    overall_feedback: str | None = None
    strengths: list[str] = []
    improvements: list[str] = []
    question_details: list[InterviewAnswerDTO] = []
    created_at: datetime | None = None
    completed_at: datetime | None = None


class InterviewReportDTO(BaseModel):
    """面试报告"""
    session_id: str
    total_questions: int = 0
    overall_score: float = 0
    overall_feedback: str = ""
    strengths: list[str] = []
    improvements: list[str] = []
    topic_scores: dict[str, float] = {}
