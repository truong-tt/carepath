from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    provider_mode: Literal["mock", "cloud"] = "mock"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    admin_token: str = "change-me"
    confidence_threshold: float = Field(default=0.7, ge=0, le=1)
    database_url: str = "sqlite:///./carepath.db"
    openai_transcribe_model: str = "gpt-4o-transcribe"
    claude_mt_model: str = "claude-sonnet-5"
    claude_reviewer_model: str = "claude-sonnet-5"
    provider_timeout_seconds: float = 30

    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
