import pytest

from app.config import Settings
from app.providers import get_providers
from app.providers.base import ASRProvider, ASRResult, MTProvider, MTResult, ReviewerProvider
from app.providers.mock import MockASRProvider, MockMTProvider, MockReviewerProvider


def test_provider_registry_returns_mock_contracts() -> None:
    providers = get_providers(Settings(provider_mode="mock"))

    assert isinstance(providers.asr, ASRProvider)
    assert isinstance(providers.mt, MTProvider)
    assert isinstance(providers.reviewer, ReviewerProvider)


def test_mock_providers_default_and_canned_results() -> None:
    asr = MockASRProvider(confidence=0.42)
    mt = MockMTProvider(canned={("vi", "en", "xin chao"): MTResult("hello", 0.91)})
    reviewer = MockReviewerProvider()

    assert asr.transcribe(b"xin chao", "vi") == ASRResult("xin chao", 0.42)
    assert mt.translate("xin chao", "vi", "en", []) == MTResult("hello", 0.91)
    assert reviewer.review("xin chao", "hello", "vi", "en").back_translation == "xin chao"


def test_mock_failures_are_injectable() -> None:
    with pytest.raises(RuntimeError, match="mock ASR failure"):
        MockASRProvider(fail=True).transcribe(b"x", "vi")

    with pytest.raises(RuntimeError, match="mock MT failure"):
        MockMTProvider(fail=True).translate("x", "vi", "en", [])

    with pytest.raises(RuntimeError, match="mock reviewer failure"):
        MockReviewerProvider(fail=True).review("x", "y", "vi", "en")
