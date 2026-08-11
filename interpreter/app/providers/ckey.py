"""OpenAI-compatible chat providers (CKey) for the interpreter.

CarePath's only LLM gateway is CKey, which speaks the OpenAI ``chat/completions``
shape rather than the Anthropic Messages API. The Anthropic providers stay in
place for ``PROVIDER_MODE=cloud``; this module serves ``PROVIDER_MODE=ckey`` and
deliberately reuses their prompts and strict output parsers so both transports
enforce the same translate-only contract.

The request shape mirrors ``carepath.services.llm.OpenAICompatibleLLM``. It is
duplicated rather than imported because the interpreter package must not depend
on the scribe package.
"""

from __future__ import annotations

import base64
import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import asdict

from app.providers.base import ASRResult, GlossaryEntry, MTResult, ProviderOutputError, Review
from app.providers.claude_common import parse_strict_json
from app.providers.claude_mt import TRANSLATE_ONLY_SYSTEM, parse_mt_output
from app.providers.claude_reviewer import REVIEWER_SYSTEM, parse_review_output


def strip_json_fence(text: str) -> str:
    """Unwrap a ```json fenced block so the strict parsers see bare JSON."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    return stripped


def can_retry_without_response_format(status_code: int, body: str) -> bool:
    if status_code not in {400, 422}:
        return False
    lowered = body.lower()
    return "response_format" in lowered or "json_object" in lowered


class CKeyChatClient:
    """Minimal chat/completions transport shared by the MT and reviewer providers."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 30,
        opener: object | None = None,
        use_response_format: bool = False,
        attempts: int = 3,
        backoff_seconds: float = 1.0,
    ) -> None:
        if opener is None and not api_key:
            raise ValueError("LLM_API_KEY is required for PROVIDER_MODE=ckey")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        # Off by default: measured 2026-08-11, CKey's gpt-5.4 hangs past a 60s
        # timeout when sent response_format=json_object but answers in ~8s
        # without it. A hang is not an HTTPError, so the retry below never fires
        # and every turn would fail. The prompt demands strict JSON and
        # parse_mt_output validates it, so the hint buys nothing here.
        self.use_response_format = use_response_format
        # Measured 2026-08-11: this gateway intermittently returns 502 and
        # occasionally stalls past a minute. Without retries a single blip drops
        # a clinician's turn mid-consultation.
        self.attempts = max(1, attempts)
        self.backoff_seconds = backoff_seconds
        # ponytail: injectable opener keeps tests off the network; urlopen otherwise.
        self._opener = opener or urllib.request.urlopen

    def chat_json(
        self,
        system: str,
        payload: dict[str, object],
        image: tuple[bytes, str] | None = None,
    ) -> str:
        """Ask for strict JSON, optionally about an attached (bytes, mime) image."""
        user = json.dumps(payload, ensure_ascii=False)
        use_response_format = self.use_response_format
        last_error: Exception | None = None

        for attempt in range(self.attempts):
            try:
                return self._post(
                    system, user, use_response_format=use_response_format, image=image
                )
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                if use_response_format and can_retry_without_response_format(exc.code, body):
                    use_response_format = False
                    continue
                if exc.code < 500:
                    # A client error will not fix itself; fail now. The body can
                    # echo clinical source text, so it never enters the message.
                    raise RuntimeError(f"CKey request failed with HTTP {exc.code}") from exc
                last_error = exc
            except Exception as exc:
                # Timeout or dropped connection: transient, worth another go.
                last_error = exc
            if attempt + 1 < self.attempts:
                time.sleep(self.backoff_seconds * (attempt + 1))

        raise RuntimeError(
            f"CKey request failed after {self.attempts} attempts"
        ) from last_error

    def _post(
        self,
        system: str,
        user: str,
        use_response_format: bool,
        image: tuple[bytes, str] | None = None,
    ) -> str:
        content: object = user
        if image is not None:
            data, mime = image
            content = [
                {"type": "text", "text": user},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
                    },
                },
            ]
        body: dict[str, object] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
            "temperature": 0.0,
        }
        if use_response_format:
            body["response_format"] = {"type": "json_object"}
        request = urllib.request.Request(
            url=f"{self.base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with self._opener(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("CKey response did not match chat completions shape") from exc
        return strip_json_fence(str(content))


DOCUMENT_OCR_SYSTEM = """You transcribe Vietnamese medical documents.
Return the clinically meaningful lines, in reading order, exactly as printed.

Keep each item whole. A table row is ONE line: join its cells in order, so a
medicine, its strength and its directions stay together on the same line.
Example: "Amoxicillin 500 mg - Uống 1 viên, ngày 2 lần, sau ăn".

Skip column headers, row numbers, clinic addresses, phone numbers, form numbers
and signature lines. Keep the patient name, the diagnosis, every medicine row,
and any instruction or follow-up line.

Do not translate. Do not summarize. Do not explain. Do not correct spelling.
Never invent a line that is not visible in the image.
If the image is unreadable, blank, or is not a medical document, return an empty list.
Return only compact JSON with exactly this key: lines."""


def parse_document_lines(text: str) -> list[str]:
    """Strict parse of the OCR envelope: a list of lines, nothing else.

    Fails closed. An unreadable document must yield zero lines rather than the
    model's guess at what a prescription usually says.
    """
    value = parse_strict_json(strip_json_fence(text))
    if set(value) != {"lines"}:
        raise ProviderOutputError("document output has unexpected keys")
    lines = value["lines"]
    if not isinstance(lines, list):
        raise ProviderOutputError("document lines must be a list")
    if not all(isinstance(line, str) for line in lines):
        raise ProviderOutputError("document lines must be strings")
    return [line.strip() for line in lines if line.strip()]


def read_document_lines(client: CKeyChatClient, image: bytes, mime: str) -> list[str]:
    return parse_document_lines(
        client.chat_json(
            DOCUMENT_OCR_SYSTEM,
            {"task": "transcribe_medical_document", "output_schema": {"lines": ["string"]}},
            image=(image, mime),
        )
    )


class CKeyMTProvider:
    def __init__(self, *, client: CKeyChatClient) -> None:
        self.client = client

    def translate(
        self,
        text: str,
        src: str,
        tgt: str,
        glossary_hits: list[GlossaryEntry],
    ) -> MTResult:
        return parse_mt_output(
            self.client.chat_json(
                TRANSLATE_ONLY_SYSTEM,
                {
                    "source_language": src,
                    "target_language": tgt,
                    "source_text": text,
                    "glossary": [asdict(entry) for entry in glossary_hits],
                },
            )
        )


class CKeyReviewerProvider:
    def __init__(self, *, client: CKeyChatClient) -> None:
        self.client = client

    def review(self, source: str, translation: str, src: str, tgt: str) -> Review:
        return parse_review_output(
            self.client.chat_json(
                REVIEWER_SYSTEM,
                {
                    "source_language": src,
                    "target_language": tgt,
                    "source_text": source,
                    "translation": translation,
                },
            )
        )


class UnavailableASRProvider:
    """Fail closed on audio turns when no transcription backend is configured.

    Substituting a mock transcript here would push invented text through the
    translation and risk pipeline and show it to a clinician as if it had been
    said. Raising instead surfaces a retryable ``turn_error`` on the websocket
    and leaves the typed path as the fallback.
    """

    def transcribe(self, audio: bytes, lang: str) -> ASRResult:
        del audio, lang
        raise RuntimeError("audio turns are unavailable in ckey mode; send text_turn instead")
