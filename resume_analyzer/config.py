from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Resume Analyzer"
    environment: str = "local"
    log_level: str = "INFO"
    database_path: str = "resume_analyzer.db"
    embedding_model_name: str = "all-MiniLM-L6-v2"
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    semantic_weight: float = Field(default=0.6, ge=0, le=1)
    skill_weight: float = Field(default=0.4, ge=0, le=1)
    max_upload_size_mb: int = 10

    model_config = SettingsConfigDict(
        env_prefix="RESUME_ANALYZER_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
