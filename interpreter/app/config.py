from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CORS_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")


class Settings(BaseSettings):
    provider_mode: Literal["mock", "cloud"] = "mock"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    admin_token: str = "change-me"
    confidence_threshold: float = Field(default=0.7, ge=0, le=1)
    retention_days: int = Field(default=30, ge=0)
    max_turn_audio_bytes: int = Field(default=10 * 1024 * 1024, ge=1)
    database_url: str = "sqlite:///./carepath.db"
    openai_transcribe_model: str = "gpt-4o-transcribe"
    claude_mt_model: str = "claude-sonnet-5"
    claude_reviewer_model: str = "claude-sonnet-5"
    provider_timeout_seconds: float = 30
    cors_origins: tuple[str, ...] = DEFAULT_CORS_ORIGINS

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"), enable_decoding=False, extra="ignore"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            origins = (item.strip().rstrip("/") for item in value.split(","))
            return tuple(origin for origin in origins if origin)
        return tuple(value) if value else ()


@lru_cache
def get_settings() -> Settings:
    return Settings()
