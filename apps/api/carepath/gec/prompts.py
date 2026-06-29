"""DARAG instruction templates and the synthetic-generation prompt.

The fine-tuning template follows paper §4.3 (best hypothesis + other hypotheses +
named-entities -> response), expressed in ChatML so it trains cleanly on Qwen.
Training and inference share one builder so the two can never drift: at inference
the string stops at the assistant header ready for generation; training appends
the gold transcript and the end-of-turn marker.

``use_retrieval=False`` reproduces the paper's ``w/o RAC`` ablation by dropping
the named-entities line entirely.
"""

from __future__ import annotations

import json
import re
from typing import Any

IM_START = "<|im_start|>"
IM_END = "<|im_end|>"

SYSTEM_PROMPT = (
    "You correct Vietnamese medical ASR transcripts. Preserve code-switched "
    "medical terms, numbers, units, acronyms, and clinical meaning. Use the other "
    "hypotheses and the retrieved named entities only as evidence. Output only the "
    "corrected transcript."
)


def format_named_entities(terms: Any) -> str:
    """Render retrieved NEs as the paper's simple comma-separated list (§4.2 Step 3)."""

    return ", ".join(_as_term_list(terms))


def format_inference_prompt(row: dict[str, Any], use_retrieval: bool = True) -> str:
    """Prompt up to (and including) the assistant header, ready for generation.

    ``row`` must carry ``raw_asr``; ``retrieved_terms`` (falling back to
    ``gold_terms``) supplies the NE list, and an optional ``other_hypotheses``
    list supplies the N-best evidence (paper N=5). Missing optional fields are
    simply omitted.
    """

    lines = [f"Best hypothesis: {row['raw_asr']}"]

    others = _as_term_list(row.get("other_hypotheses"))
    if others:
        rendered = "\n".join(f"  {idx}. {hyp}" for idx, hyp in enumerate(others, start=1))
        lines.append(f"Other hypotheses:\n{rendered}")

    if use_retrieval:
        retrieved = row.get("retrieved_terms")
        if retrieved is None:
            retrieved = row.get("gold_terms")
        lines.append(f"Named entities: {format_named_entities(retrieved)}")

    user = "\n".join(lines)
    return (
        f"{IM_START}system\n{SYSTEM_PROMPT}\n{IM_END}\n"
        f"{IM_START}user\n{user}\n{IM_END}\n"
        f"{IM_START}assistant\n"
    )


def format_training_prompt(row: dict[str, Any], use_retrieval: bool = True) -> str:
    """Inference prompt + gold transcript + end-of-turn marker (the SFT target)."""

    return (
        f"{format_inference_prompt(row, use_retrieval=use_retrieval)}"
        f"{row['gold_text']}\n"
        f"{IM_END}"
    )


def strip_generated(text: str) -> str:
    """Clean a decoded completion: stop at the end-of-turn marker, trim."""

    return text.split(IM_END)[0].strip()


def build_synthetic_generation_messages(
    examples: list[dict[str, Any]],
    count: int,
    topic: str | None = None,
) -> list[dict[str, str]]:
    """Few-shot chat messages for synthetic transcript generation (paper §4.1/App. B).

    The model is shown a handful of in-domain example transcripts and asked to
    produce *new* short clinical utterances that match the domain, style, length,
    and code-switching behavior — without copying the examples.
    """

    example_lines = []
    for idx, example in enumerate(examples, start=1):
        terms = _as_term_list(example.get("cs_terms_list") or example.get("gold_terms"))
        transcript = example.get("segment_text") or example.get("gold_text") or ""
        example_lines.append(
            f"{idx}. Topic: {example.get('topic') or topic or 'medical'} | "
            f"Terms: {', '.join(terms) or 'none'} | "
            f"Transcript: {transcript}"
        )
    user = (
        "You generate synthetic Vietnamese medical speech transcripts for ASR/GEC "
        "training. Study the spoken style, length, and code-switching behavior of the "
        "examples, then write new, diverse transcripts with the same properties but "
        "different content. Do not copy the examples. Do not invent patient "
        "identifiers. Prefer short clinical utterances: doctor-patient phrasing, "
        "symptoms, exam findings, medications, biomarkers, and natural English medical "
        "terms.\n"
        f"Generate exactly {count} transcripts as JSON with key \"transcripts\", where "
        "each item has \"clean_text\", \"topic\", and \"intended_terms\".\n\n"
        "Examples:\n" + "\n".join(example_lines)
    )
    return [
        {
            "role": "system",
            "content": "You are a synthetic data generator for Vietnamese medical ASR research.",
        },
        {"role": "user", "content": user},
    ]


def parse_synthetic_transcripts(text: str) -> list[dict[str, Any]]:
    """Parse the generator's JSON reply into transcript dicts (tolerant of fences)."""

    parsed = _extract_json(text)
    if isinstance(parsed, list):
        rows = parsed
    elif isinstance(parsed, dict):
        rows = parsed.get("transcripts", [])
    else:
        rows = []
    if not isinstance(rows, list):
        raise ValueError("Synthetic generation must return a list under 'transcripts'")
    clean_rows: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, str):
            clean_rows.append({"clean_text": row, "topic": None, "intended_terms": []})
        elif isinstance(row, dict):
            clean_rows.append(row)
    return clean_rows


def _as_term_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    return [item.strip() for item in str(raw).split(";") if item.strip()]


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
