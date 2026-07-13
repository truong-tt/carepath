import json
from typing import Any

from anthropic import Anthropic

from app.providers.base import ProviderOutputError


def build_anthropic_client(api_key: str, timeout: float) -> Anthropic:
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is required for cloud provider mode")
    return Anthropic(api_key=api_key, timeout=timeout)


def message_text(message: Any) -> str:
    parts: list[str] = []
    for block in getattr(message, "content", []):
        text = block.get("text") if isinstance(block, dict) else getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


def parse_strict_json(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProviderOutputError("provider returned non-JSON output") from exc
    if not isinstance(value, dict):
        raise ProviderOutputError("provider output must be a JSON object")
    return value
