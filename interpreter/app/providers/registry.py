import json
from dataclasses import dataclass
from pathlib import Path

from app.config import Settings, get_settings
from app.normalize import normalize_text
from app.providers.base import (
    ASRProvider,
    CriticalEntity,
    MTProvider,
    MTResult,
    Review,
    ReviewerProvider,
)
from app.providers.ckey import (
    CKeyChatClient,
    CKeyMTProvider,
    CKeyReviewerProvider,
    UnavailableASRProvider,
    read_document_lines,
)
from app.providers.claude_mt import ClaudeMTProvider
from app.providers.claude_reviewer import ClaudeReviewerProvider
from app.providers.mock import MockASRProvider, MockMTProvider, MockReviewerProvider
from app.providers.openai_asr import OpenAIASRProvider

DEMO_SCENARIO_PATH = Path(__file__).parent / "demo_scenario.json"


@dataclass(frozen=True, slots=True)
class ProviderSet:
    asr: ASRProvider
    mt: MTProvider
    reviewer: ReviewerProvider


def load_demo_scenario(path: Path | None = None) -> tuple[dict, dict]:
    """Build canned MT and reviewer maps from a scripted consultation.

    Keys are normalized with the same ``normalize_text`` the pipeline applies
    before translating, so a scenario can be written in natural language
    ("500 milligrams") and still match the text the providers actually receive
    ("500 mg").
    """
    scenario = json.loads((path or DEMO_SCENARIO_PATH).read_text(encoding="utf-8"))
    mt_canned: dict[tuple[str, str, str], MTResult] = {}
    review_canned: dict[tuple[str, str, str, str], Review] = {}
    for turn in scenario["turns"]:
        src, tgt = turn["src"], turn["tgt"]
        source = normalize_text(turn["source"])
        translation = turn["translation"]
        mt_canned[(src, tgt, source)] = MTResult(
            text=translation, confidence=float(turn.get("confidence", 0.95))
        )
        review = turn.get("review")
        if review:
            review_canned[(src, tgt, source, translation)] = Review(
                back_translation=review["back_translation"],
                entities=[CriticalEntity(**entity) for entity in review.get("entities", [])],
                flags=list(review.get("flags", [])),
            )
    return mt_canned, review_canned


def read_document(settings: Settings, image: bytes, mime: str) -> list[str]:
    """Vietnamese text lines from a photographed medical document.

    OCR only. Translation, risk classification and the clinician gate all happen
    downstream in ``process_text_turn``, so the vision model never decides
    whether something is dangerous.

    Fails closed on modes with no vision backend rather than returning nothing
    and letting the caller think the document was blank.
    """
    if settings.provider_mode == "demo":
        # Derived from the scripted turns flagged as document lines, so the OCR
        # output and its canned translation cannot drift apart.
        scenario = json.loads(DEMO_SCENARIO_PATH.read_text(encoding="utf-8"))
        return [turn["source"] for turn in scenario["turns"] if turn.get("document")]
    if settings.provider_mode != "ckey":
        raise RuntimeError(
            f"document reading needs PROVIDER_MODE=ckey or demo, not {settings.provider_mode}"
        )
    client = CKeyChatClient(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        timeout=settings.provider_timeout_seconds,
    )
    return read_document_lines(client, image, mime)


def get_providers(settings: Settings | None = None) -> ProviderSet:
    settings = settings or get_settings()
    if settings.provider_mode == "mock":
        return ProviderSet(
            asr=MockASRProvider(),
            mt=MockMTProvider(),
            reviewer=MockReviewerProvider(),
        )
    if settings.provider_mode == "demo":
        # Rehearsal and emergency demo path: the model calls are replaced by a
        # scripted consultation, but the normalizer, glossary, risk engine,
        # confirmation flow and persistence all still run for real.
        mt_canned, review_canned = load_demo_scenario()
        return ProviderSet(
            asr=UnavailableASRProvider(),
            mt=MockMTProvider(canned=mt_canned),
            reviewer=MockReviewerProvider(canned=review_canned),
        )
    if settings.provider_mode == "ckey":
        client = CKeyChatClient(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_model,
            timeout=settings.provider_timeout_seconds,
        )
        # Speech capture happens in the browser on the ckey path, so audio turns
        # fail closed rather than inventing a transcript.
        return ProviderSet(
            asr=UnavailableASRProvider(),
            mt=CKeyMTProvider(client=client),
            reviewer=CKeyReviewerProvider(client=client),
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
