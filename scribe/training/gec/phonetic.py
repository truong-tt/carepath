"""Deterministic PiDA-style Vietnamese text corruption for GEC experiments."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from gec.metrics import extract_numbers_and_units

OPERATIONS = ("tone", "vowel", "consonant", "code_switch_boundary")

_TONE_GROUPS = {
    "áàảãạ": "a",
    "ắằẳẵặ": "ă",
    "ấầẩẫậ": "â",
    "éèẻẽẹ": "e",
    "ếềểễệ": "ê",
    "íìỉĩị": "i",
    "óòỏõọ": "o",
    "ốồổỗộ": "ô",
    "ớờởỡợ": "ơ",
    "úùủũụ": "u",
    "ứừửữự": "ư",
    "ýỳỷỹỵ": "y",
}
_TONE_MAP = str.maketrans(
    {
        char: base.upper() if char.isupper() else base
        for group, base in _TONE_GROUPS.items()
        for char in (group + group.upper())
    }
)
_VOWEL_PAIRS = (("ă", "â"), ("â", "ă"), ("i", "y"), ("y", "i"))
_CONSONANT_PAIRS = (("tr", "ch"), ("ch", "tr"), ("s", "x"), ("x", "s"), ("d", "gi"))


def add_phonetic_corruption(rows: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    """Add balanced identity-clean/corrupted text pairs to real train rows only."""

    output: list[dict[str, Any]] = []
    for row in rows:
        output.append(dict(row))
        if row.get("split") != "train":
            continue
        source = str(row.get("gold_text", ""))
        terms = [str(term) for term in row.get("gold_terms", [])]
        corrupted, operation = corrupt_text(
            source,
            terms,
            seed=seed,
            row_id=str(row.get("audio_id", "")),
        )
        if extract_numbers_and_units(corrupted) != extract_numbers_and_units(source):
            raise ValueError("phonetic corruption changed a number or unit")
        shared = {
            **row,
            "other_hypotheses": [],
            "asr_model": "deterministic_text_corruption",
        }
        output.append(
            {
                **shared,
                "audio_id": f"{row.get('audio_id')}:phonetic-clean:{seed}",
                "raw_asr": source,
                "source_kind": "pida_clean_text",
                "phonetic_corruption": {
                    "method": "pida_vietnamese_adaptation",
                    "operation": "identity_clean",
                    "seed": seed,
                    "source_audio_id": row.get("audio_id"),
                    "target_unchanged": True,
                },
            }
        )
        output.append(
            {
                **shared,
                "audio_id": f"{row.get('audio_id')}:phonetic:{seed}",
                "raw_asr": corrupted,
                "source_kind": "pida_phonetic_text",
                "phonetic_corruption": {
                    "method": "pida_vietnamese_adaptation",
                    "operation": operation,
                    "seed": seed,
                    "source_audio_id": row.get("audio_id"),
                    "target_unchanged": True,
                },
            }
        )
    return output


def corrupt_text(
    text: str,
    protected_terms: list[str],
    *,
    seed: int,
    row_id: str,
    preferred_operation: str | None = None,
) -> tuple[str, str]:
    """Apply one reproducible phonetic/boundary error without changing terms or numbers."""

    if preferred_operation and preferred_operation not in OPERATIONS:
        raise ValueError(f"preferred_operation must be one of {OPERATIONS}")
    protected = _protected_spans(text, protected_terms)
    if preferred_operation:
        order = [preferred_operation]
    else:
        offset = int(hashlib.sha256(f"{seed}:{row_id}".encode()).hexdigest()[:8], 16)
        order = [OPERATIONS[(offset + index) % len(OPERATIONS)] for index in range(len(OPERATIONS))]
    for operation in order:
        candidate = _apply(text, operation, protected_terms, protected)
        if candidate != text and extract_numbers_and_units(candidate) == extract_numbers_and_units(text):
            return candidate, operation
    raise ValueError(f"no safe phonetic corruption available for train row {row_id!r}")


def _apply(
    text: str,
    operation: str,
    protected_terms: list[str],
    protected: list[tuple[int, int]],
) -> str:
    if operation == "code_switch_boundary":
        for term in protected_terms:
            match = re.search(rf"(?i)(?<=\w)\s+(?={re.escape(term)}\b)", text)
            if match:
                return text[: match.start()] + text[match.end() :]
            match = re.search(rf"(?i)\b{re.escape(term)}(?P<gap>\s+)(?=\w)", text)
            if match:
                start, end = match.span("gap")
                return text[:start] + text[end:]
        return text
    if operation == "tone":
        for index, char in enumerate(text):
            replacement = char.translate(_TONE_MAP)
            if replacement != char and not _inside(index, protected):
                return text[:index] + replacement + text[index + 1 :]
        return text
    pairs = _VOWEL_PAIRS if operation == "vowel" else _CONSONANT_PAIRS
    for source, target in pairs:
        for match in re.finditer(rf"(?i)\b{re.escape(source)}", text):
            if not _inside(match.start(), protected):
                replacement = target.upper() if match.group().isupper() else target
                return text[: match.start()] + replacement + text[match.end() :]
    return text


def _protected_spans(text: str, terms: list[str]) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for term in terms:
        spans.extend(match.span() for match in re.finditer(re.escape(term), text, flags=re.IGNORECASE))
    spans.extend(match.span() for match in re.finditer(r"\b\d+(?:[.,]\d+)?\s*[%A-Za-z/]*\b", text))
    return spans


def _inside(index: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= index < end for start, end in spans)
