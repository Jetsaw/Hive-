from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # DeepSeek (OpenAI-compatible)
    DEEPSEEK_API_KEY: str = Field(..., description="DeepSeek API key")
    DEEPSEEK_BASE_URL: str = Field(default="https://api.deepseek.com")
    DEEPSEEK_MODEL: str = Field(default="deepseek-chat")

    # LLM Control
    USE_LLM: bool = Field(default=False, description="Enable LLM generation (set to False for RAG-only mode)")

    # Paths
    DATA_DIR: str = Field(default="./data")
    KB_DIR: str = Field(default="./data/kb")
    GLOBAL_DOCS_DIR: str = Field(default="./data/global_docs")
    GLOBAL_INDEX_DIR: str = Field(default="./data/indexes/global")
    SQLITE_PATH: str = Field(default="./data/hive.db")

    # Web
    FRONTEND_ORIGIN: str = Field(default="http://localhost:8080")

    # RAG tuning
    TOP_K: int = Field(default=4)
    MAX_CONTEXT_CHARS: int = Field(default=12000)
    MIN_SCORE: float = Field(default=0.25)

    # Memory
    HISTORY_LIMIT: int = Field(default=8)


settings = Settings()
