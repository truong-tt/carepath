from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from carepath.evaluation import normalize_text, split_terms


DEFAULT_SYNTHETIC_MODEL = "Qwen/Qwen3-4B-Instruct-2507"
FALLBACK_SYNTHETIC_MODELS = [
    "Qwen/Qwen2.5-7B-Instruct",
    "google/gemma-3-4b-it",
]

GEC_PAIR_REQUIRED_FIELDS = {
    "split",
    "source_kind",
    "audio_id",
    "raw_asr",
    "gold_text",
    "gold_terms",
    "retrieved_terms",
    "asr_model",
    "duration_seconds",
}

SYNTHETIC_REQUIRED_FIELDS = {
    "source_kind",
    "synthetic_id",
    "clean_text",
    "topic",
    "seed_example_ids",
    "model",
}


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[str]


def validate_gec_pair(row: dict[str, Any]) -> ValidationResult:
    errors = _missing_errors(row, GEC_PAIR_REQUIRED_FIELDS)
    if row.get("source_kind") not in {"vimedcss_real", "darag_synthetic_tts", "text_noise_ablation"}:
        errors.append("source_kind must identify real, DARAG synthetic, or ablation data")
    if not str(row.get("raw_asr", "")).strip():
        errors.append("raw_asr must be non-empty")
    if not str(row.get("gold_text", "")).strip():
        errors.append("gold_text must be non-empty")
    if not isinstance(row.get("gold_terms"), list):
        errors.append("gold_terms must be a list")
    if not isinstance(row.get("retrieved_terms"), list):
        errors.append("retrieved_terms must be a list")
    return ValidationResult(ok=not errors, errors=errors)


def validate_synthetic_transcript(row: dict[str, Any]) -> ValidationResult:
    errors = _missing_errors(row, SYNTHETIC_REQUIRED_FIELDS)
    clean_text = str(row.get("clean_text", "")).strip()
    if not clean_text:
        errors.append("clean_text must be non-empty")
    if len(clean_text.split()) < 5:
        errors.append("clean_text is too short for ASR/GEC training")
    if row.get("source_kind") != "darag_synthetic_clean":
        errors.append("source_kind must be darag_synthetic_clean")
    return ValidationResult(ok=not errors, errors=errors)


def format_darag_training_prompt(row: dict[str, Any]) -> str:
    retrieved_terms = row.get("retrieved_terms") or row.get("gold_terms") or []
    if isinstance(retrieved_terms, str):
        retrieved_terms = split_terms(retrieved_terms)
    return (
        "<|im_start|>system\n"
        "You correct Vietnamese medical ASR transcripts. Preserve code-switched "
        "medical terms, numbers, units, acronyms, and clinical meaning. Output only "
        "the corrected transcript.\n"
        "<|im_end|>\n"
        "<|im_start|>user\n"
        f"Retrieved medical/code-switch terms: {json.dumps(retrieved_terms, ensure_ascii=False)}\n"
        f"Raw ASR transcript: {row['raw_asr']}\n"
        "<|im_end|>\n"
        "<|im_start|>assistant\n"
        f"{row['gold_text']}\n"
        "<|im_end|>"
    )


def build_synthetic_generation_messages(
    examples: list[dict[str, Any]],
    count: int,
    topic: str | None = None,
) -> list[dict[str, str]]:
    example_lines = []
    for idx, example in enumerate(examples, start=1):
        terms = split_terms(example.get("cs_terms_list") or example.get("gold_terms"))
        example_lines.append(
            f"{idx}. Topic: {example.get('topic') or topic or 'medical'} | "
            f"Terms: {', '.join(terms) or 'none'} | "
            f"Transcript: {example.get('segment_text') or example.get('gold_text')}"
        )
    user = (
        "Generate synthetic Vietnamese medical speech transcripts for ASR/GEC training. "
        "Match the examples' spoken style, length, and code-switching behavior. "
        "Do not copy examples. Do not create patient identifiers. "
        "Prefer short clinical utterances, doctor-patient phrasing, symptoms, exam findings, "
        "medications, biomarkers, and English medical terms when natural. "
        f"Generate exactly {count} diverse transcripts as JSON with key transcripts, "
        "where each item has clean_text, topic, and intended_terms.\n\n"
        "Examples:\n"
        + "\n".join(example_lines)
    )
    return [
        {
            "role": "system",
            "content": "You are a synthetic data generator for Vietnamese medical ASR research.",
        },
        {"role": "user", "content": user},
    ]


def parse_synthetic_transcripts(text: str) -> list[dict[str, Any]]:
    parsed = _extract_json(text)
    if isinstance(parsed, list):
        rows = parsed
    elif isinstance(parsed, dict):
        rows = parsed.get("transcripts", [])
    else:
        rows = []
    if not isinstance(rows, list):
        raise ValueError("Synthetic generation must return a list under transcripts")
    clean_rows = []
    for row in rows:
        if isinstance(row, str):
            clean_rows.append({"clean_text": row, "topic": None, "intended_terms": []})
        elif isinstance(row, dict):
            clean_rows.append(row)
    return clean_rows


def ngram_overlap(candidate: str, reference: str, n: int = 3) -> float:
    cand = _ngrams(normalize_text(candidate).split(), n)
    ref = _ngrams(normalize_text(reference).split(), n)
    if not cand or not ref:
        return 0.0
    return len(cand & ref) / len(cand)


def duplicate_rejection_reason(
    candidate: str,
    references: list[str],
    max_ngram_overlap: float = 0.72,
) -> str | None:
    for reference in references:
        overlap = ngram_overlap(candidate, reference)
        if overlap >= max_ngram_overlap:
            return f"near_duplicate_ngram_overlap:{overlap:.3f}"
    return None


def _extract_json(text: str) -> Any:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(stripped[start : end + 1])


def _ngrams(tokens: list[str], n: int) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return set()
    return {tuple(tokens[idx : idx + n]) for idx in range(len(tokens) - n + 1)}


def _missing_errors(row: dict[str, Any], required_fields: set[str]) -> list[str]:
    return [f"missing required field: {field}" for field in sorted(required_fields) if field not in row]
