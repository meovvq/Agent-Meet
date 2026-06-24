"""应用配置"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置（从环境变量或 .env 文件读取）"""

    # ---- 应用 ----
    app_name: str = "Agent Meet"
    debug: bool = False

    # ---- 数据库 ----
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agent_meet"

    # ---- Redis ----
    redis_url: str = "redis://localhost:6379/0"

    # ---- LLM ----
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_api_key: str = "sk-xxx"
    llm_model: str = "deepseek-chat"

    # ---- Embedding（默认阿里百炼 DashScope）----
    embedding_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    embedding_api_key: str = "sk-xxx"
    embedding_model: str = "text-embedding-v3"
    embedding_dimensions: int = 1024

    # ---- Agent 模式 ----
    agent_mode_enabled: bool = True
    agent_max_reasoning_steps: int = 3
    agent_memory_enabled: bool = True
    agent_planning_enabled: bool = True

    # ---- 存储 ----
    storage_path: str = "./storage"

    # ---- 面试参数 ----
    interview_follow_up_max: int = 2
    interview_hint_enabled: bool = True
    interview_pass_score: int = 7
    interview_follow_up_score: int = 4

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
