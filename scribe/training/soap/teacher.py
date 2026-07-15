"""Teacher transformation interface; secrets are read from env and never persisted."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Protocol

from soap.data import materialize_synthetic
from soap.schemas import stable_json

PROMPT_VERSION = "carepath-grounded-soap-v1"


class Teacher(Protocol):
    def transform(self, source_row: dict[str, Any]) -> dict[str, Any]: ...

    def predict(self, transcript: str) -> dict[str, Any]: ...

    def provenance(self) -> dict[str, Any]: ...


class SyntheticTeacher:
    def transform(self, source_row: dict[str, Any]) -> dict[str, Any]:
        return materialize_synthetic(source_row)

    def provenance(self) -> dict[str, Any]:
        return _provenance("deterministic_synthetic", "fixture", "local", 0.0)

    def predict(self, transcript: str) -> dict[str, Any]:
        raise ValueError("synthetic teacher predictions require the fixture reference")


class CKeyTeacher:
    """OpenAI-compatible CKey teacher for research-only silver-data generation."""

    def __init__(
        self,
        *,
        api_key_env: str = "LLM_API_KEY",
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 90.0,
    ) -> None:
        self.api_key_env = api_key_env
        self.api_key = os.environ.get(api_key_env, "")
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL", "https://api.xah.io/v1")).rstrip("/")
        self.model = model or os.environ.get("LLM_MODEL", "gpt-5.4")
        self.timeout_seconds = timeout_seconds

    def transform(self, source_row: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise ValueError(f"{self.api_key_env} is required for the CKey SOAP teacher")
        prompt = json.dumps(
            {
                "task": "adapt_public_dialogue_to_grounded_vietnamese_outpatient_soap",
                "rules": [
                    "Translate or adapt only facts supported by the source dialogue and note.",
                    "Do not add diagnoses, medications, doses, numbers, units, or negation.",
                    "Every fact must cite an exact character span in transcript.",
                    "Each non-missing SOAP section is semicolon-separated exact fact values.",
                    "Set review_required to true.",
                ],
                "source_dialogue": source_row["dialogue"],
                "source_note": source_row["source_note"],
                "output_schema": {
                    "transcript": "Vietnamese string",
                    "facts": [
                        {
                            "type": "symptom|history|observation|assessment|medication|dose|plan",
                            "value": "string",
                            "negated": False,
                            "uncertain": False,
                            "source_span": {"start": 0, "end": 1, "text": "exact transcript text"},
                        }
                    ],
                    "soap": {
                        "subjective": "string",
                        "objective": "string",
                        "assessment": "string",
                        "plan": "string",
                        "missing_information": ["string"],
                        "review_required": True,
                    },
                },
            },
            ensure_ascii=False,
        )
        payload = {
            "model": self.model,
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": "Create research-only Vietnamese SOAP data. Preserve source facts exactly.",
                },
                {"role": "user", "content": prompt},
            ],
        }
        try:
            parsed = self._request(payload)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code not in {400, 422} or "response_format" not in body.casefold():
                raise ValueError(f"CKey teacher HTTP {exc.code}: {body}") from exc
            payload.pop("response_format")
            parsed = self._request(payload)
        return _json_object(parsed)

    def predict(self, transcript: str) -> dict[str, Any]:
        prompt = json.dumps(
            {
                "task": "independent_vietnamese_soap_teacher_baseline",
                "transcript": transcript,
                "rules": [
                    "Extract facts with exact source_span start/end/text offsets.",
                    "Use only extracted facts to write the SOAP note.",
                    "Each non-missing SOAP section is semicolon-separated exact fact values.",
                    "Do not add diagnoses, medications, doses, numbers, units, or negation.",
                    "Set review_required to true.",
                ],
                "output_schema": {
                    "facts": [
                        {
                            "type": "string",
                            "value": "string",
                            "negated": False,
                            "uncertain": False,
                            "source_span": {"start": 0, "end": 1, "text": "exact text"},
                        }
                    ],
                    "soap": {
                        "subjective": "string",
                        "objective": "string",
                        "assessment": "string",
                        "plan": "string",
                        "missing_information": ["string"],
                        "review_required": True,
                    },
                },
            },
            ensure_ascii=False,
        )
        payload = {
            "model": self.model,
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "Return grounded Vietnamese SOAP JSON only."},
                {"role": "user", "content": prompt},
            ],
        }
        return _json_object(self._request(payload))

    def _request(self, payload: dict[str, Any]) -> str:
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            result = json.loads(response.read().decode("utf-8"))
        try:
            return str(result["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("CKey teacher response did not match chat-completions shape") from exc

    def provenance(self) -> dict[str, Any]:
        return {
            **_provenance("ckey", self.model, self.base_url, 0.0),
            "api_key_env": self.api_key_env,
        }


def build_teacher(name: str) -> Teacher:
    if name == "synthetic":
        return SyntheticTeacher()
    if name == "ckey":
        return CKeyTeacher()
    raise ValueError(f"unsupported SOAP teacher: {name!r}")


def _json_object(text: str) -> dict[str, Any]:
    stripped = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.IGNORECASE).strip()
    start, end = stripped.find("{"), stripped.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("teacher response has no JSON object")
    parsed = json.loads(stripped[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("teacher response JSON must be an object")
    return parsed


def _provenance(provider: str, model: str, base_url: str, temperature: float) -> dict[str, Any]:
    config = {
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "temperature": temperature,
        "prompt_version": PROMPT_VERSION,
    }
    import hashlib

    return {
        **config,
        "prompt_config_sha256": hashlib.sha256(stable_json(config).encode("utf-8")).hexdigest(),
    }
