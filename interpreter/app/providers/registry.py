from dataclasses import dataclass

from app.config import Settings, get_settings
from app.providers.base import ASRProvider, MTProvider, ReviewerProvider
from app.providers.claude_mt import ClaudeMTProvider
from app.providers.claude_reviewer import ClaudeReviewerProvider
from app.providers.mock import MockASRProvider, MockMTProvider, MockReviewerProvider
from app.providers.openai_asr import OpenAIASRProvider


@dataclass(frozen=True, slots=True)
class ProviderSet:
    asr: ASRProvider
    mt: MTProvider
    reviewer: ReviewerProvider


def get_providers(settings: Settings | None = None) -> ProviderSet:
    settings = settings or get_settings()
    if settings.provider_mode == "mock":
        return ProviderSet(
            asr=MockASRProvider(),
            mt=MockMTProvider(),
            reviewer=MockReviewerProvider(),
        )
    return ProviderSet(
        asr=OpenAIASRProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_transcribe_model,
            timeout=settings.provider_timeout_seconds,
        ),
        mt=ClaudeMTProvider(
            api_key=settings.anthropic_api_key,
            model=settings.claude_mt_model,
            timeout=settings.provider_timeout_seconds,
        ),
        reviewer=ClaudeReviewerProvider(
            api_key=settings.anthropic_api_key,
            model=settings.claude_reviewer_model,
            timeout=settings.provider_timeout_seconds,
        ),
    )
