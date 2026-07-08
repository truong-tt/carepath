from io import BytesIO
from math import exp
from typing import Any

from openai import OpenAI

from app.providers.base import ASRResult


def _attr(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def confidence_from_logprobs(logprobs: list[Any] | None) -> float:
    """Mean token probability from transcription logprobs; missing logprobs fail low."""
    if not logprobs:
        return 0.0
    mean_logprob = sum(float(_attr(item, "logprob", -20.0)) for item in logprobs) / len(logprobs)
    return max(0.0, min(1.0, exp(mean_logprob)))


class OpenAIASRProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gpt-4o-transcribe",
        timeout: float = 30,
        client: Any | None = None,
        attempts: int = 2,
    ) -> None:
        if client is None and not api_key:
            raise ValueError("OPENAI_API_KEY is required for cloud provider mode")
        self.client = client or OpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        self.attempts = max(1, attempts)

    def transcribe(self, audio: bytes, lang: str) -> ASRResult:
        last_error: Exception | None = None
        for _ in range(self.attempts):
            try:
                file_obj = BytesIO(audio)
                file_obj.name = "turn.webm"
                response = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=file_obj,
                    language=lang[:2],
                    response_format="json",
                    include=["logprobs"],
                )
                return ASRResult(
                    text=str(_attr(response, "text", "")).strip(),
                    confidence=confidence_from_logprobs(_attr(response, "logprobs")),
                )
            except Exception as exc:
                last_error = exc
        raise RuntimeError("ASR transcription failed") from last_error
