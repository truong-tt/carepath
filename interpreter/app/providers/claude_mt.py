import json
from dataclasses import asdict
from typing import Any

from app.providers.base import GlossaryEntry, MTResult, ProviderOutputError
from app.providers.claude_common import build_anthropic_client, message_text, parse_strict_json

TRANSLATE_ONLY_SYSTEM = """You are a medical interpreter. Translate only the user's source text.
Never add advice, diagnoses, drug recommendations, explanations, or extra context.
Preserve numbers, units, negation, drug names, laterality, and route of administration exactly.
The glossary field lists approved term pairs for this clinic; when a source term appears there,
use its paired translation rather than your own wording.
Return only compact JSON with exactly these keys: translation, confidence."""


class ClaudeMTProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str = "claude-sonnet-5",
        timeout: float = 30,
        client: Any | None = None,
    ) -> None:
        self.client = client or build_anthropic_client(api_key, timeout)
        self.model = model

    def translate(
        self,
        text: str,
        src: str,
        tgt: str,
        glossary_hits: list[GlossaryEntry],
    ) -> MTResult:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            temperature=0,
            system=TRANSLATE_ONLY_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "source_language": src,
                            "target_language": tgt,
                            "source_text": text,
                            "glossary": [asdict(entry) for entry in glossary_hits],
                        },
                        ensure_ascii=False,
                    ),
                }
            ],
        )
        return parse_mt_output(message_text(response))


def parse_mt_output(text: str) -> MTResult:
    value = parse_strict_json(text)
    if set(value) != {"translation", "confidence"}:
        raise ProviderOutputError("translation output has unexpected keys")
    translation = value["translation"]
    confidence = value["confidence"]
    if not isinstance(translation, str) or not translation.strip():
        raise ProviderOutputError("translation must be a non-empty string")
    if isinstance(confidence, bool) or not isinstance(confidence, int | float):
        confidence = 0.0
    elif not 0 <= float(confidence) <= 1:
        # Models sometimes answer 95 for 95%. Reading that as 0.95 would be a
        # guess; discarding an otherwise valid translation costs the clinician a
        # turn. Unlike the translation, confidence has a safe default: treat an
        # unusable value as no confidence at all, which routes the turn through
        # the low-confidence path instead of silently trusting it.
        confidence = 0.0
    return MTResult(text=translation.strip(), confidence=float(confidence))
