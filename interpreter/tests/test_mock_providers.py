import pytest

from app.config import Settings
from app.normalize import normalize_text
from app.providers import get_providers
from app.providers.base import ASRProvider, ASRResult, MTProvider, MTResult, ReviewerProvider
from app.providers.mock import MockASRProvider, MockMTProvider, MockReviewerProvider
from app.providers.registry import load_demo_scenario


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


def test_demo_mode_returns_scenario_translations() -> None:
    providers = get_providers(Settings(provider_mode="demo"))

    # The scenario is authored as "500 milligrams"; the pipeline normalizes it to
    # "500 mg" before translating, and the loader keys on the normalized form.
    result = providers.mt.translate(
        normalize_text("I was taking 500 milligrams twice a day"), "en", "vi", []
    )

    assert result.text == "Tôi uống 500 mg, ngày hai lần"
    assert result.confidence == 0.94


def test_demo_mode_pins_low_confidence_on_the_uncertain_dose_turn() -> None:
    providers = get_providers(Settings(provider_mode="demo"))

    result = providers.mt.translate(normalize_text("I take 15 milligrams"), "en", "vi", [])

    assert result.confidence < Settings().confidence_threshold


def test_demo_mode_supplies_reviewer_readbacks() -> None:
    providers = get_providers(Settings(provider_mode="demo"))
    source = normalize_text("I am allergic to amoxicillin, I developed a rash after taking it")

    review = providers.reviewer.review(
        source, "Tôi bị dị ứng amoxicillin, tôi bị nổi mẩn sau khi dùng thuốc", "en", "vi"
    )

    assert "amoxicillin" in review.back_translation
    assert any(entity.kind == "allergen" for entity in review.entities)


def test_demo_mode_falls_back_instead_of_crashing_off_script() -> None:
    providers = get_providers(Settings(provider_mode="demo"))

    result = providers.mt.translate("something nobody scripted", "en", "vi", [])

    assert result.text == "[en->vi] something nobody scripted"


def test_demo_mode_fails_closed_on_audio_turns() -> None:
    providers = get_providers(Settings(provider_mode="demo"))

    with pytest.raises(RuntimeError, match="text_turn"):
        providers.asr.transcribe(b"audio", "en")


def test_every_scenario_turn_key_is_already_normalized() -> None:
    """A scenario line that normalizes to something else would never match."""
    mt_canned, _ = load_demo_scenario()

    for _src, _tgt, source in mt_canned:
        assert normalize_text(source) == source
