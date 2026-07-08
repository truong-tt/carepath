from sqlmodel import Session

from app import crud
from app.config import Settings
from app.glossary import lookup_glossary
from app.normalize import normalize_text
from app.providers.base import Review
from app.providers.registry import ProviderSet
from app.risk import classify_risk


def target_lang(lang: str) -> str:
    return "en" if lang.lower().startswith("vi") else "vi"


def turn_status(risk_tier: str) -> str:
    return "awaiting_confirm" if risk_tier in {"high", "critical"} else "delivered"


def review_payload(review: Review) -> dict[str, object]:
    return {
        "back_translation": review.back_translation,
        "entities": [
            {
                "kind": entity.kind,
                "source_span": list(entity.source_span),
                "translated_span": list(entity.translated_span),
            }
            for entity in review.entities
        ],
        "flags": review.flags,
    }


def blocked_review_payload(source: str, reason: str) -> dict[str, object]:
    return {"back_translation": source, "entities": [], "flags": [reason]}


def process_text_turn(
    db: Session,
    providers: ProviderSet,
    settings: Settings,
    *,
    session_id: str,
    speaker: str,
    lang: str,
    text: str,
    asr_confidence: float,
) -> crud.TurnRecord:
    normalized = normalize_text(text)
    tgt = target_lang(lang)
    glossary_hits = lookup_glossary(db, normalized)
    mt_result = providers.mt.translate(normalized, lang, tgt, glossary_hits)
    risk = classify_risk(
        normalized,
        mt_result.text,
        asr_confidence,
        mt_result.confidence,
        settings.confidence_threshold,
        glossary_hits,
    )
    status = turn_status(risk.tier)
    readback = None
    if risk.tier in {"high", "critical"}:
        try:
            readback = review_payload(
                providers.reviewer.review(normalized, mt_result.text, lang, tgt)
            )
        except Exception:
            status = "blocked"
            readback = blocked_review_payload(normalized, "reviewer_failed")
    return crud.create_turn(
        db,
        session_id=session_id,
        speaker=speaker,
        src_lang=lang,
        tgt_lang=tgt,
        source_text=text,
        normalized_text=normalized,
        translation=mt_result.text,
        asr_confidence=asr_confidence,
        mt_confidence=mt_result.confidence,
        risk_tier=risk.tier,
        risk_spans=risk.spans,
        status=status,
        readback=readback,
    )


def process_audio_turn(
    db: Session,
    providers: ProviderSet,
    settings: Settings,
    *,
    session_id: str,
    speaker: str,
    lang: str,
    audio: bytes,
) -> crud.TurnRecord:
    asr_result = providers.asr.transcribe(audio, lang)
    return process_text_turn(
        db,
        providers,
        settings,
        session_id=session_id,
        speaker=speaker,
        lang=lang,
        text=asr_result.text,
        asr_confidence=asr_result.confidence,
    )
