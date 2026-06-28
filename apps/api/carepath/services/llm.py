from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, replace
from typing import Any, Protocol

from carepath.config import Settings
from carepath.schemas import SoapNote
from carepath.services.retrieval import RetrievedTerm

logger = logging.getLogger("carepath.llm")


class LLMError(RuntimeError):
    """Raised when the configured LLM provider fails."""


@dataclass(frozen=True)
class CorrectionResult:
    corrected_text: str
    provider: str
    raw_response: str | None = None


@dataclass(frozen=True)
class SoapResult:
    soap: SoapNote
    provider: str


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
    ) -> "SoapResult":
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
    ) -> SoapResult:
        content = self._chat_json(
            system=SOAP_SYSTEM_PROMPT,
            user=build_soap_prompt(corrected_text, retrieved_terms, encounter_context),
        )
        parsed = extract_json_object(content)
        parsed["review_required"] = True
        parsed.setdefault("missing_information", [])
        return SoapResult(soap=SoapNote(**parsed), provider=self.provider_name)

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
    ) -> SoapResult:
        sections = _bucket_clauses(corrected_text)
        term_text = ", ".join(item.term for item in retrieved_terms) or "không có"

        subjective = sections["subjective"]
        objective = sections["objective"]
        assessment = sections["assessment"] or (
            "Chưa có đánh giá rõ ràng trong bản ghi. "
            f"Thuật ngữ liên quan được phát hiện: {term_text}. Cần bác sĩ xác nhận."
        )
        plan_reminder = (
            "Bác sĩ rà soát lại bản ghi âm, xác nhận triệu chứng, dấu hiệu sinh tồn, "
            "chẩn đoán và kế hoạch điều trị trước khi lưu hồ sơ."
        )
        plan = f"{sections['plan']}. {plan_reminder}" if sections["plan"] else plan_reminder

        missing = []
        if not objective:
            missing.append("Dấu hiệu sinh tồn hoặc kết quả cận lâm sàng chưa rõ.")
        if not subjective:
            missing.append("Triệu chứng/chủ quan của bệnh nhân chưa rõ.")
        soap = SoapNote(
            subjective=subjective or "Chưa đủ thông tin chủ quan trong transcript.",
            objective=objective or "Chưa đủ thông tin khách quan trong transcript.",
            assessment=assessment,
            plan=plan,
            missing_information=missing,
            review_required=True,
        )
        return SoapResult(soap=soap, provider="offline")


class FallbackClinicalLLM:
    """Wrap a network LLM so a provider failure never breaks the demo.

    If the primary provider raises ``LLMError`` (timeout, auth, bad gateway,
    malformed JSON), we transparently serve the deterministic offline generator
    and tag the provider as ``*_offline_fallback`` so the response metadata makes
    the degraded path visible to clinicians and operators.
    """

    def __init__(self, primary: ClinicalLLM, fallback: "OfflineClinicalLLM"):
        self.primary = primary
        self.fallback = fallback

    def readiness(self) -> tuple[bool, dict[str, object]]:
        ready, details = self.primary.readiness()
        return ready, {**details, "fallback": "offline", "fallback_enabled": True}

    def correct_transcript(
        self,
        raw_text: str,
        retrieved_terms: list[RetrievedTerm],
        encounter_context: str | None = None,
    ) -> CorrectionResult:
        try:
            return self.primary.correct_transcript(
                raw_text, retrieved_terms, encounter_context=encounter_context
            )
        except LLMError as exc:
            logger.warning("LLM correction failed; using offline fallback: %s", exc)
            result = self.fallback.correct_transcript(
                raw_text, retrieved_terms, encounter_context=encounter_context
            )
            return replace(result, provider="offline_fallback")

    def generate_soap(
        self,
        corrected_text: str,
        retrieved_terms: list[RetrievedTerm],
        encounter_context: str | None = None,
    ) -> SoapResult:
        try:
            return self.primary.generate_soap(
                corrected_text, retrieved_terms, encounter_context=encounter_context
            )
        except LLMError as exc:
            logger.warning("LLM SOAP generation failed; using offline fallback: %s", exc)
            result = self.fallback.generate_soap(
                corrected_text, retrieved_terms, encounter_context=encounter_context
            )
            return replace(result, provider="offline_fallback")


def build_llm(settings: Settings) -> ClinicalLLM:
    if settings.llm_provider in {"offline", "mock"}:
        return OfflineClinicalLLM()
    if settings.llm_provider in {"openai", "openai_compatible", "ckey"}:
        primary = OpenAICompatibleLLM(settings)
        if settings.llm_fallback_offline:
            return FallbackClinicalLLM(primary, OfflineClinicalLLM())
        return primary
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


# Offline SOAP bucketing. Each clause is assigned to exactly one section, in
# priority order, so a run-on dictation is split into S/O/A/P instead of being
# dumped wholesale into Subjective. This is a heuristic safety net, not a
# replacement for the validated clinical LLM.
_ASSESSMENT_KEYWORDS = (
    "chẩn đoán",
    "nghĩ đến",
    "nghĩ tới",
    "nghi ngờ",
    "hội chứng",
    "ấn tượng",
    "đánh giá",
)
_HISTORY_KEYWORDS = ("tiền sử", "tiền căn", "bệnh sử")
_PLAN_KEYWORDS = (
    "cho làm",
    "chỉ định",
    "kê đơn",
    "kê toa",
    "cho thuốc",
    "cho uống",
    "theo dõi",
    "tái khám",
    "chuyển",
    "nhập viện",
    "điều trị",
    "dặn",
    "hẹn",
    "truyền",
    "tiêm",
    "bù dịch",
    "hội chẩn",
)
_OBJECTIVE_KEYWORDS = (
    "huyết áp",
    "mạch",
    "nhiệt độ",
    "spo2",
    "mmhg",
    "mg/dl",
    "bpm",
    "lần/phút",
    "xét nghiệm",
    "siêu âm",
    "x-quang",
    "ct",
    "mri",
    "ecg",
    "điện tim",
    "khám",
    "nghe phổi",
    "phù",
    "vàng da",
    "troponin",
    "công thức máu",
)
_SUBJECTIVE_KEYWORDS = (
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
    "mỏi",
    "nôn",
    "tiêu chảy",
    "hồi hộp",
    "mất ngủ",
    "sụt cân",
    "chán ăn",
    "than",
)
# A number directly followed by a clinical unit is an objective measurement.
_MEASUREMENT = re.compile(
    r"\d+(?:[.,]\d+)?\s*(?:%|mmhg|mg/dl|bpm|lần/phút|mmol|°c)",
    flags=re.IGNORECASE,
)


# Raw ASR is often unpunctuated, so punctuation alone cannot segment it. We
# insert a break before where a new clinical statement begins:
#   - a vital sign immediately followed by a number ("huyết áp 150"), so a real
#     measurement splits but a history phrase ("tăng huyết áp") does not; and
#   - statement-starter verbs/markers (orders, impressions, history), curated to
#     avoid substrings of one another so multi-word phrases stay intact.
_VITAL_MEASUREMENT_CUE = r"(?:huyết áp|mạch|nhiệt độ|nhịp thở|spo2)\s*\d"
_STARTER_CUES = (
    "cho làm",
    "chỉ định",
    "kê đơn",
    "kê toa",
    "theo dõi",
    "tái khám",
    "nhập viện",
    "hội chẩn",
    "chẩn đoán",
    "nghĩ đến",
    "nghĩ tới",
    "nghi ngờ",
    "tiền sử",
    "tiền căn",
    "bệnh sử",
)
_BOUNDARY_RE = re.compile(
    r"\s+(?=(?:"
    + "|".join(re.escape(c) for c in sorted(_STARTER_CUES, key=len, reverse=True))
    + r"|"
    + _VITAL_MEASUREMENT_CUE
    + r"))",
    flags=re.IGNORECASE,
)


def _split_clauses(text: str) -> list[str]:
    # Insert breaks before clinical cue words (handles unpunctuated ASR), then
    # split on commas, semicolons, newlines, and sentence punctuation -- but not
    # on a period/comma between digits (e.g. 37.5, 1,5) so numbers stay intact.
    text = _BOUNDARY_RE.sub("\n", text)
    parts = re.split(r"[;\n]+|,(?!\d)|(?<!\d)[.!?]+(?!\d)", text)
    return [part.strip() for part in parts if part and part.strip()]


def _classify_clause(clause: str) -> str:
    lowered = clause.lower()
    if any(kw in lowered for kw in _ASSESSMENT_KEYWORDS):
        return "assessment"
    if any(kw in lowered for kw in _HISTORY_KEYWORDS):
        return "subjective"
    if any(kw in lowered for kw in _PLAN_KEYWORDS):
        return "plan"
    if _MEASUREMENT.search(lowered) or any(kw in lowered for kw in _OBJECTIVE_KEYWORDS):
        return "objective"
    if any(kw in lowered for kw in _SUBJECTIVE_KEYWORDS):
        return "subjective"
    return "subjective"


def _bucket_clauses(text: str) -> dict[str, str]:
    buckets: dict[str, list[str]] = {
        "subjective": [],
        "objective": [],
        "assessment": [],
        "plan": [],
    }
    for clause in _split_clauses(text):
        buckets[_classify_clause(clause)].append(clause)
    return {
        section: ". ".join(c[:1].upper() + c[1:] for c in clauses)
        for section, clauses in buckets.items()
    }
