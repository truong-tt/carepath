import json
from typing import Any

from app.providers.base import CriticalEntity, ProviderOutputError, Review
from app.providers.claude_common import build_anthropic_client, message_text, parse_strict_json

REVIEWER_SYSTEM = """You verify high-risk medical translations.
Back-translate the translation and extract only critical entities: drug, dose, frequency,
route, allergen, laterality, negation. Return only compact JSON with exactly these keys:
back_translation, entities, flags."""


class ClaudeReviewerProvider:
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

    def review(self, source: str, translation: str, src: str, tgt: str) -> Review:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            temperature=0,
            system=REVIEWER_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "source_language": src,
                            "target_language": tgt,
                            "source_text": source,
                            "translation": translation,
                        },
                        ensure_ascii=False,
                    ),
                }
            ],
        )
        return parse_review_output(message_text(response))


def _span(value: Any) -> tuple[int, int]:
    if (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(item, int) for item in value)
        and value[0] <= value[1]
    ):
        return (value[0], value[1])
    raise ProviderOutputError("entity spans must be [start, end] integer pairs")


def parse_review_output(text: str) -> Review:
    value = parse_strict_json(text)
    if set(value) != {"back_translation", "entities", "flags"}:
        raise ProviderOutputError("review output has unexpected keys")
    if not isinstance(value["back_translation"], str) or not value["back_translation"].strip():
        raise ProviderOutputError("back_translation must be a non-empty string")
    if not isinstance(value["entities"], list) or not isinstance(value["flags"], list):
        raise ProviderOutputError("entities and flags must be lists")

    entities: list[CriticalEntity] = []
    for entity in value["entities"]:
        expected_entity_keys = {"kind", "source_span", "translated_span"}
        if not isinstance(entity, dict) or set(entity) != expected_entity_keys:
            raise ProviderOutputError("entity has unexpected keys")
        if not isinstance(entity["kind"], str):
            raise ProviderOutputError("entity kind must be a string")
        entities.append(
            CriticalEntity(
                kind=entity["kind"],
                source_span=_span(entity["source_span"]),
                translated_span=_span(entity["translated_span"]),
            )
        )

    flags = value["flags"]
    if not all(isinstance(flag, str) for flag in flags):
        raise ProviderOutputError("flags must be strings")
    return Review(
        back_translation=value["back_translation"].strip(),
        entities=entities,
        flags=flags,
    )
