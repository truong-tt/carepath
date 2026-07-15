"""Private research staging provider for a dual-adapter Scribe bundle.

The provider loads one 4-bit base model, switches between the transcript GEC
and grounded SOAP adapters, and keeps the public ``ClinicalLLM`` interface
unchanged. It is opt-in with ``LLM_PROVIDER=scribe_local`` and is never a
production default.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Callable

from carepath.config import Settings
from carepath.schemas import SoapNote
from carepath.services.gec_local import _passes_safety
from carepath.services.llm import ClinicalLLM, CorrectionResult, LLMError, SoapResult
from carepath.services.retrieval import RetrievedTerm
from carepath_shared.normalize import contains_folded, normalize_for_match

logger = logging.getLogger("carepath.scribe_local")

Generator = Callable[[str, str], str]
_NUMBER_UNIT_RE = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:mg|mcg|µg|g|kg|ml|l|mmhg|%|bpm|cm|mm)?\b",
    re.IGNORECASE,
)
_MISSING_PREFIXES = ("chua", "khong co thong tin", "khong ghi nhan")
_FACT_TYPES = {"symptom", "history", "observation", "assessment", "medication", "dose", "plan"}
_NEGATION_CUES = ("khong", "chua", "am tinh", "no ", "not ", "denies")
_SECTION_FACT_TYPES = {
    "subjective": {"symptom", "history", "medication", "dose"},
    "objective": {"observation"},
    "assessment": {"assessment"},
    "plan": {"plan", "medication", "dose"},
}


class LocalScribeLLM:
    """One base model with GEC and SOAP PEFT adapters for Colab staging."""

    provider_name = "scribe_local"

    def __init__(self, bundle_path: Path, generate_fn: Generator | None = None):
        self.bundle = Path(bundle_path)
        manifest_path = self.bundle / "scribe_manifest.json"
        try:
            self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Invalid Scribe bundle manifest: {manifest_path}") from exc
        _validate_manifest(self.manifest)
        self._generate_fn = generate_fn
        self._model = None
        self._tokenizer = None

    def readiness(self) -> tuple[bool, dict[str, object]]:
        adapters = self.manifest["adapters"]
        missing = [name for name, rel in adapters.items() if not (self.bundle / rel).exists()]
        return not missing, {
            "provider": self.provider_name,
            "bundle": str(self.bundle),
            "base_model": self.manifest["base_model"],
            "adapters": sorted(adapters),
            "missing_adapters": missing,
            "usage_scope": self.manifest["usage_scope"],
            "promotion_status": self.manifest["promotion_status"],
            "fallback": "disabled",
        }

    def correct_transcript(
        self,
        raw_text: str,
        retrieved_terms: list[RetrievedTerm],
        encounter_context: str | None = None,
    ) -> CorrectionResult:
        if self.manifest.get("correction_mode", "adapter") == "identity":
            return CorrectionResult(raw_text, "scribe_local_identity")
        prompt = json.dumps(
            {
                "task": "correct_asr_transcript",
                "raw_transcript": raw_text,
                "retrieved_terms": [term.term for term in retrieved_terms],
                "encounter_context": encounter_context,
            },
            ensure_ascii=False,
        )
        corrected = _strip_generation(self._generate("gec", prompt))
        if not _passes_safety(raw_text, corrected):
            raise LLMError("scribe_local correction failed safety gate")
        if not _numbers_supported(corrected, raw_text):
            raise LLMError("scribe_local correction introduced a number or unit")
        return CorrectionResult(corrected, self.provider_name)

    def generate_soap(
        self,
        corrected_text: str,
        retrieved_terms: list[RetrievedTerm],
        encounter_context: str | None = None,
    ) -> SoapResult:
        extraction_prompt = json.dumps(
            {
                "task": "extract_grounded_clinical_facts",
                "transcript": corrected_text,
                "encounter_context": encounter_context,
                "schema": {
                    "facts": [
                        {
                            "type": "string",
                            "value": "string",
                            "negated": False,
                            "uncertain": False,
                            "source_span": {
                                "start": 0,
                                "end": 1,
                                "text": "exact transcript substring",
                            },
                        }
                    ]
                },
            },
            ensure_ascii=False,
        )
        extracted = _json_object(self._generate("soap", extraction_prompt), "SOAP extraction")
        facts = _ground_facts(corrected_text, extracted.get("facts"))

        writing_prompt = json.dumps(
            {
                "task": "write_grounded_soap_note",
                "facts": facts,
                "rules": [
                    "Use only supplied facts.",
                    "Each non-missing section is semicolon-separated exact fact values.",
                    "Leave assessment or plan missing when no matching fact exists.",
                    "Always set review_required to true.",
                ],
                "schema": {
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
        payload = _json_object(self._generate("soap", writing_prompt), "SOAP writing")
        payload["review_required"] = True
        payload.setdefault("missing_information", [])
        try:
            soap = SoapNote(**payload)
        except Exception as exc:
            raise LLMError(f"scribe_local SOAP response failed schema validation: {exc}") from exc
        _validate_soap(soap, facts, corrected_text, retrieved_terms)
        return SoapResult(soap=soap, provider=self.provider_name)

    def _generate(self, adapter: str, user_prompt: str) -> str:
        if self._generate_fn is not None:
            return self._generate_fn(adapter, user_prompt)
        self._ensure_model()
        import torch  # type: ignore

        self._model.set_adapter(adapter)
        system = self.manifest.get("prompts", {}).get(
            adapter, "Return only the requested JSON without unsupported clinical facts."
        )
        rendered = self._tokenizer.apply_chat_template(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = self._tokenizer(rendered, return_tensors="pt").to(self._model.device)
        limit = int(self.manifest.get("max_new_tokens", {}).get(adapter, 512))
        with torch.no_grad():
            output = self._model.generate(
                **inputs,
                max_new_tokens=limit,
                do_sample=False,
                num_beams=1,
                pad_token_id=self._tokenizer.pad_token_id,
            )
        generated = output[0][inputs["input_ids"].shape[-1] :]
        return self._tokenizer.decode(generated, skip_special_tokens=True)

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        import torch  # type: ignore
        from peft import PeftModel  # type: ignore
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig  # type: ignore

        if not torch.cuda.is_available():
            raise RuntimeError("scribe_local requires a CUDA GPU; use private Colab staging")
        base_name = self.manifest["base_model"]
        revision = self.manifest.get("base_revision")
        kwargs = {"revision": revision} if revision else {}
        tokenizer = AutoTokenizer.from_pretrained(base_name, trust_remote_code=True, **kwargs)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        compute_dtype = (
            torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        )
        quantization = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=True,
        )
        base = AutoModelForCausalLM.from_pretrained(
            base_name,
            quantization_config=quantization,
            device_map="auto",
            trust_remote_code=True,
            **kwargs,
        )
        adapters = self.manifest["adapters"]
        if self.manifest.get("correction_mode", "adapter") == "adapter":
            model = PeftModel.from_pretrained(
                base, str(self.bundle / adapters["gec"]), adapter_name="gec"
            )
            model.load_adapter(str(self.bundle / adapters["soap"]), adapter_name="soap")
        else:
            model = PeftModel.from_pretrained(
                base, str(self.bundle / adapters["soap"]), adapter_name="soap"
            )
        model.eval()
        self._model, self._tokenizer = model, tokenizer
        logger.info("Loaded research Scribe adapters from %s", self.bundle)


def _validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schema") != "carepath.scribe.bundle/1":
        raise ValueError("Unsupported Scribe bundle schema")
    if manifest.get("usage_scope") != "research_only":
        raise ValueError("Scribe bundle must be research_only")
    if manifest.get("promotion_status") != "blocked_research_only":
        raise ValueError("Scribe bundle promotion must remain blocked_research_only")
    if not manifest.get("base_model"):
        raise ValueError("Scribe bundle requires base_model")
    adapters = manifest.get("adapters")
    if not isinstance(adapters, dict) or "soap" not in adapters:
        raise ValueError("Scribe bundle requires a SOAP adapter")
    if manifest.get("correction_mode", "adapter") == "adapter" and "gec" not in adapters:
        raise ValueError("Adapter correction mode requires a GEC adapter")


def _json_object(text: str, label: str) -> dict[str, Any]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise LLMError(f"{label} did not return JSON")
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError(f"{label} returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise LLMError(f"{label} must return one JSON object")
    return payload


def _strip_generation(text: str) -> str:
    return text.split("<|im_end|>", 1)[0].strip()


def _numbers(text: str) -> set[str]:
    return {normalize_for_match(match.group(0)) for match in _NUMBER_UNIT_RE.finditer(text)}


def _numbers_supported(output: str, source: str) -> bool:
    return _numbers(output).issubset(_numbers(source))


def _ground_facts(transcript: str, rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        raise LLMError("SOAP extraction must return a facts list")
    accepted: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise LLMError("SOAP fact must be an object")
        fact_type = str(row.get("type", "")).strip().lower()
        value = str(row.get("value", "")).strip()
        span_value = row.get("source_span")
        if not isinstance(span_value, dict):
            raise LLMError("SOAP fact source_span must include start, end, and text")
        start, end = span_value.get("start"), span_value.get("end")
        span = str(span_value.get("text", ""))
        if (
            not fact_type
            or fact_type not in _FACT_TYPES
            or not value
            or not span
            or not isinstance(start, int)
            or isinstance(start, bool)
            or not isinstance(end, int)
            or isinstance(end, bool)
            or start < 0
            or end <= start
            or end > len(transcript)
            or transcript[start:end] != span
        ):
            raise LLMError("SOAP fact is not grounded to an exact transcript span")
        if not contains_folded(span, value):
            raise LLMError("SOAP fact value is not present in its exact source span")
        if not _numbers_supported(value, span):
            raise LLMError("SOAP fact number/unit is not grounded to its source span")
        negated = bool(row.get("negated", False))
        has_negation_cue = any(cue in normalize_for_match(span) for cue in _NEGATION_CUES)
        if negated != has_negation_cue:
            raise LLMError("SOAP fact negation does not match its exact source span")
        accepted.append(
            {
                "type": fact_type,
                "value": value,
                "negated": negated,
                "uncertain": bool(row.get("uncertain", False)),
                "source_span": span,
            }
        )
    return accepted


def _missing_section(text: str) -> bool:
    folded = normalize_for_match(text)
    return not folded or folded.startswith(_MISSING_PREFIXES)


def _validate_soap(
    soap: SoapNote,
    facts: list[dict[str, Any]],
    transcript: str,
    retrieved_terms: list[RetrievedTerm],
) -> None:
    rendered = " ".join((soap.subjective, soap.objective, soap.assessment, soap.plan))
    evidence = " ".join(str(fact["source_span"]) for fact in facts)
    if not _numbers_supported(rendered, evidence):
        raise LLMError("SOAP output introduced an unsupported number or unit")
    for term in retrieved_terms:
        if contains_folded(rendered, term.term) and not contains_folded(transcript, term.term):
            raise LLMError(f"SOAP output introduced unsupported retrieved term: {term.term}")
    fact_types = {str(fact["type"]) for fact in facts}
    for section, allowed_types in _SECTION_FACT_TYPES.items():
        text = str(getattr(soap, section))
        if _missing_section(text):
            continue
        allowed_values = {
            normalize_for_match(str(fact["value"])).strip(" .")
            for fact in facts
            if fact["type"] in allowed_types
        }
        fragments = {
            normalize_for_match(fragment).strip(" .")
            for fragment in text.split(";")
            if fragment.strip()
        }
        if not fragments or not fragments.issubset(allowed_values):
            raise LLMError(f"SOAP {section} contains text outside grounded fact values")
    if not _missing_section(soap.assessment) and not fact_types.intersection(
        {"assessment", "diagnosis"}
    ):
        raise LLMError("SOAP assessment lacks a grounded assessment/diagnosis fact")
    if not _missing_section(soap.plan) and not fact_types.intersection(
        {"plan", "treatment", "medication", "follow_up"}
    ):
        raise LLMError("SOAP plan lacks a grounded plan fact")


def build_scribe_local(settings: Settings) -> ClinicalLLM:
    if not settings.scribe_bundle_path:
        raise ValueError("SCRIBE_BUNDLE_PATH is required for the scribe_local provider")
    return LocalScribeLLM(Path(settings.scribe_bundle_path))
