from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from carepath.config import Settings
from carepath.schemas import SoapNote
from carepath.services.retrieval import RetrievedTerm


class LLMError(RuntimeError):
    """Raised when the configured LLM provider fails."""


@dataclass(frozen=True)
class CorrectionResult:
    corrected_text: str
    provider: str
    raw_response: str | None = None


class ClinicalLLM(Protocol):
    def readiness(self) -> tuple[bool, dict[str, object]]:
        ...

    def correct_transcript(
        self,
        raw_text: str,
        retrieved_terms: list[RetrievedTerm],
        encounter_context: str | None = None,
    ) -> CorrectionResult:
        ...

    def generate_soap(
        self,
        corrected_text: str,
        retrieved_terms: list[RetrievedTerm],
        encounter_context: str | None = None,
    ) -> SoapNote:
        ...


class OpenAICompatibleLLM:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.provider_name = "ckey" if settings.llm_provider == "ckey" else "openai_compatible"

    def readiness(self) -> tuple[bool, dict[str, object]]:
        return (
            bool(self.settings.llm_api_key),
            {
                "provider": self.provider_name,
                "base_url": self.settings.llm_base_url,
                "model": self.settings.llm_model,
                "missing_api_key": not bool(self.settings.llm_api_key),
            },
        )

    def correct_transcript(
        self,
        raw_text: str,
        retrieved_terms: list[RetrievedTerm],
        encounter_context: str | None = None,
    ) -> CorrectionResult:
        content = self._chat_json(
            system=CORRECTION_SYSTEM_PROMPT,
            user=build_correction_prompt(raw_text, retrieved_terms, encounter_context),
        )
        parsed = extract_json_object(content)
        corrected = str(parsed.get("corrected_transcript", "")).strip()
        if not corrected:
            raise LLMError("LLM correction response did not include corrected_transcript")
        return CorrectionResult(
            corrected_text=corrected,
            provider=self.provider_name,
            raw_response=content,
        )

    def generate_soap(
        self,
        corrected_text: str,
        retrieved_terms: list[RetrievedTerm],
        encounter_context: str | None = None,
    ) -> SoapNote:
        content = self._chat_json(
            system=SOAP_SYSTEM_PROMPT,
            user=build_soap_prompt(corrected_text, retrieved_terms, encounter_context),
        )
        parsed = extract_json_object(content)
        parsed["review_required"] = True
        parsed.setdefault("missing_information", [])
        return SoapNote(**parsed)

    def _chat_json(self, system: str, user: str) -> str:
        if not self.settings.llm_api_key:
            raise LLMError(f"LLM_API_KEY is required for {self.provider_name} provider")

        try:
            return self._request_chat(system, user, use_response_format=True)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if _can_retry_without_response_format(exc.code, body):
                return self._request_chat(system, user, use_response_format=False)
            raise LLMError(f"LLM HTTP {exc.code}: {body}") from exc
        except Exception as exc:
            raise LLMError(f"LLM request failed: {exc}") from exc

    def _request_chat(self, system: str, user: str, use_response_format: bool) -> str:
        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.0,
        }
        if use_response_format:
            payload["response_format"] = {"type": "json_object"}
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url=f"{self.settings.llm_base_url}/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {self.settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(
            request, timeout=self.settings.llm_timeout_seconds
        ) as response:
            response_payload = json.loads(response.read().decode("utf-8"))

        try:
            return str(response_payload["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("LLM response did not match chat completions shape") from exc


class OfflineClinicalLLM:
    """Deterministic fallback for local demos without sending clinical text out."""

    def readiness(self) -> tuple[bool, dict[str, object]]:
        return True, {
            "warning": "offline fallback does not replace a validated clinical LLM"
        }

    def correct_transcript(
        self,
        raw_text: str,
        retrieved_terms: list[RetrievedTerm],
        encounter_context: str | None = None,
    ) -> CorrectionResult:
        corrected = normalize_transcript_spacing(raw_text)
        corrected = _restore_common_units(corrected)
        for item in retrieved_terms:
            corrected = _restore_term_case(corrected, item.term)
        return CorrectionResult(corrected_text=corrected, provider="offline")

    def generate_soap(
        self,
        corrected_text: str,
        retrieved_terms: list[RetrievedTerm],
        encounter_context: str | None = None,
    ) -> SoapNote:
        subjective = _pick_subjective(corrected_text)
        objective = _pick_objective(corrected_text)
        term_text = ", ".join(item.term for item in retrieved_terms) or "không có"
        assessment = (
            "Bản nháp cần bác sĩ xác nhận. Thuật ngữ liên quan được phát hiện: "
            f"{term_text}."
        )
        plan = (
            "Bác sĩ rà soát lại bản ghi âm, xác nhận triệu chứng, dấu hiệu sinh tồn, "
            "chẩn đoán và kế hoạch điều trị trước khi lưu hồ sơ."
        )
        missing = []
        if not objective:
            missing.append("Dấu hiệu sinh tồn hoặc kết quả cận lâm sàng chưa rõ.")
        if not subjective:
            missing.append("Triệu chứng/chủ quan của bệnh nhân chưa rõ.")
        return SoapNote(
            subjective=subjective or "Chưa đủ thông tin chủ quan trong transcript.",
            objective=objective or "Chưa đủ thông tin khách quan trong transcript.",
            assessment=assessment,
            plan=plan,
            missing_information=missing,
            review_required=True,
        )


def build_llm(settings: Settings) -> ClinicalLLM:
    if settings.llm_provider in {"offline", "mock"}:
        return OfflineClinicalLLM()
    if settings.llm_provider in {"openai", "openai_compatible", "ckey"}:
        return OpenAICompatibleLLM(settings)
    raise ValueError("LLM_PROVIDER must be 'offline', 'openai_compatible', or 'ckey'")


CORRECTION_SYSTEM_PROMPT = """
You correct Vietnamese medical ASR transcripts for a clinical scribe MVP.
Rules:
- Preserve Vietnamese meaning and code-switched medical terms.
- Preserve numbers, units, medication names, biomarkers, and acronyms.
- Use retrieved terms only when they fit the transcript.
- Do not add diagnoses, medications, or facts not present in the transcript.
- Return one JSON object with key corrected_transcript.
""".strip()


SOAP_SYSTEM_PROMPT = """
You create draft SOAP notes for Vietnamese clinicians.
Rules:
- Write Vietnamese SOAP sections.
- Preserve English medical terms, acronyms, biomarkers, numbers, and units.
- Do not invent clinical facts.
- If information is missing, state that it is missing.
- Always set review_required to true.
- Return one JSON object with subjective, objective, assessment, plan,
  missing_information, and review_required.
""".strip()


def build_correction_prompt(
    raw_text: str,
    retrieved_terms: list[RetrievedTerm],
    encounter_context: str | None,
) -> str:
    terms = [
        {
            "term": item.term,
            "vietnamese": item.vietnamese,
            "category": item.category,
            "score": round(item.score, 3),
        }
        for item in retrieved_terms
    ]
    return json.dumps(
        {
            "task": "correct_asr_transcript",
            "encounter_context": encounter_context,
            "raw_transcript": raw_text,
            "retrieved_terms": terms,
            "output_schema": {"corrected_transcript": "string"},
        },
        ensure_ascii=False,
    )


def build_soap_prompt(
    corrected_text: str,
    retrieved_terms: list[RetrievedTerm],
    encounter_context: str | None,
) -> str:
    return json.dumps(
        {
            "task": "draft_vietnamese_soap_note",
            "encounter_context": encounter_context,
            "corrected_transcript": corrected_text,
            "retrieved_terms": [item.term for item in retrieved_terms],
            "output_schema": {
                "subjective": "string",
                "objective": "string",
                "assessment": "string",
                "plan": "string",
                "missing_information": ["string"],
                "review_required": True,
            },
        },
        ensure_ascii=False,
    )


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise LLMError("No JSON object found in LLM response")
        parsed = json.loads(stripped[start : end + 1])
    if not isinstance(parsed, dict):
        raise LLMError("LLM response JSON must be an object")
    return parsed


def _can_retry_without_response_format(status_code: int, body: str) -> bool:
    if status_code not in {400, 422}:
        return False
    lowered = body.lower()
    return "response_format" in lowered or "json_object" in lowered


def normalize_transcript_spacing(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.:%])", r"\1", text)
    text = re.sub(r"([,.:%])([^\s])", r"\1 \2", text)
    return text


def _restore_common_units(text: str) -> str:
    replacements = {
        "spo2": "SpO2",
        "ecg": "ECG",
        "hba1c": "HbA1c",
        "bmi": "BMI",
        "mmhg": "mmHg",
        "mg/dl": "mg/dL",
        "mg dl": "mg/dL",
    }
    for needle, replacement in replacements.items():
        text = re.sub(rf"\b{re.escape(needle)}\b", replacement, text, flags=re.I)
    return text


def _restore_term_case(text: str, term: str) -> str:
    if len(term) < 3 or term.islower():
        return text
    return re.sub(rf"\b{re.escape(term)}\b", term, text, flags=re.I)


def _pick_subjective(text: str) -> str:
    keywords = (
        "đau",
        "mệt",
        "ho",
        "sốt",
        "chóng mặt",
        "buồn nôn",
        "khó thở",
        "tê",
        "rát",
        "ngứa",
    )
    return _sentences_matching(text, keywords)


def _pick_objective(text: str) -> str:
    keywords = (
        "huyết áp",
        "mạch",
        "nhiệt độ",
        "spo2",
        "mmhg",
        "mg/dl",
        "bpm",
        "xét nghiệm",
        "siêu âm",
        "x-quang",
        "ct",
        "mri",
    )
    return _sentences_matching(text, keywords)


def _sentences_matching(text: str, keywords: tuple[str, ...]) -> str:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?。])\s+|;\s+", text)]
    matches = [
        sentence
        for sentence in sentences
        if any(keyword in sentence.lower() for keyword in keywords)
    ]
    return " ".join(matches)
