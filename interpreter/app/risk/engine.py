import csv
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.glossary.store import SEED_CSV
from app.normalize import fold_for_match
from app.providers.base import GlossaryEntry

LEXICON_DIR = Path(__file__).with_name("lexicons")
SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


@dataclass(frozen=True, slots=True)
class RiskResult:
    tier: str
    spans: list[dict[str, Any]]


@lru_cache
def load_lexicon(name: str) -> Any:
    with (LEXICON_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache
def drug_terms() -> tuple[str, ...]:
    with SEED_CSV.open(encoding="utf-8", newline="") as handle:
        return tuple(row["term_vi"] for row in csv.DictReader(handle) if row["kind"] == "drug")


@lru_cache
def lasa_terms() -> frozenset[str]:
    pairs = load_lexicon("lasa_pairs.json")
    return frozenset(fold_for_match(term) for pair in pairs for term in pair)


@lru_cache
def lasa_display_terms() -> tuple[str, ...]:
    return tuple(term for pair in load_lexicon("lasa_pairs.json") for term in pair)


def _span(text: str, term: str, kind: str, severity: str) -> dict[str, Any] | None:
    folded_text = fold_for_match(text)
    folded_term = fold_for_match(term)
    if " " not in folded_term and re.fullmatch(r"\w+", folded_term):
        match = re.search(rf"\b{re.escape(folded_term)}\b", folded_text)
        start = match.start() if match else -1
    else:
        start = folded_text.find(folded_term)
    if start < 0:
        return None
    return {
        "start": start,
        "end": start + len(folded_term),
        "kind": kind,
        "severity": severity,
        "term": term,
    }


def _term_spans(text: str, terms: list[str], kind: str, severity: str) -> list[dict[str, Any]]:
    return [span for term in terms if (span := _span(text, term, kind, severity))]


def _literal_word_spans(
    text: str,
    terms: list[str],
    kind: str,
    severity: str,
) -> list[dict[str, Any]]:
    folded = text.casefold()
    spans: list[dict[str, Any]] = []
    for term in terms:
        match = re.search(rf"\b{re.escape(term.casefold())}\b", folded)
        if match:
            spans.append(
                {
                    "start": match.start(),
                    "end": match.end(),
                    "kind": kind,
                    "severity": severity,
                    "term": term,
                }
            )
    return spans


def _negation_spans(text: str) -> list[dict[str, Any]]:
    terms = load_lexicon("negation_cues.json")
    folded_terms = [term for term in terms if term != "dừng"]
    return _term_spans(text, folded_terms, "negation", "high") + _literal_word_spans(
        text, ["dừng"], "negation", "high"
    )


def _count_terms(text: str, terms: list[str]) -> int:
    folded = fold_for_match(text)
    total = 0
    for term in terms:
        if term == "dừng":
            total += len(re.findall(r"\bdừng\b", text.casefold()))
            continue
        folded_term = fold_for_match(term)
        if " " in folded_term:
            total += folded.count(folded_term)
        else:
            total += len(re.findall(rf"\b{re.escape(folded_term)}\b", folded))
    return total


def _numbers(text: str) -> list[str]:
    return NUMBER_RE.findall(text)


def _dose_spans(text: str) -> list[dict[str, Any]]:
    units = "|".join(re.escape(unit) for unit in load_lexicon("units_forms.json"))
    pattern = re.compile(rf"\b\d+(?:\.\d+)?\s*(?:{units})\b", re.IGNORECASE)
    return [
        {
            "start": match.start(),
            "end": match.end(),
            "kind": "dose_number",
            "severity": "high",
            "term": match.group(0),
        }
        for match in pattern.finditer(text)
    ]


def _frequency_spans(text: str) -> list[dict[str, Any]]:
    patterns = [
        r"ngày\s+\d+(?:\.\d+)?\s+lần",
        r"trong\s+\d+(?:\.\d+)?\s+ngày",
        r"\+\d+(?:\.\d+)?\s+days",
        r"\d+(?:\.\d+)?\s+times\s+(?:a|per)\s+day",
        r"for\s+\d+(?:\.\d+)?\s+days",
    ]
    spans: list[dict[str, Any]] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            spans.append(
                {
                    "start": match.start(),
                    "end": match.end(),
                    "kind": "frequency_duration",
                    "severity": "high",
                    "term": match.group(0),
                }
            )
    return spans


def _drug_spans(text: str, glossary_hits: list[GlossaryEntry]) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    terms = (
        {entry.term_vi for entry in glossary_hits if entry.kind == "drug"}
        | set(drug_terms())
        | set(lasa_display_terms())
    )
    for term in terms:
        severity = "critical" if fold_for_match(term) in lasa_terms() else "high"
        span = _span(text, term, "drug_name", severity)
        if span:
            spans.append(span)
    return spans


def _mismatch_spans(source_text: str, translation: str) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    source_numbers = _numbers(source_text)
    translation_numbers = _numbers(translation)
    if source_numbers and source_numbers != translation_numbers:
        spans.append(
            {
                "start": 0,
                "end": len(source_text),
                "kind": "number_mismatch",
                "severity": "critical",
                "term": ",".join(source_numbers),
            }
        )

    negation_terms = load_lexicon("negation_cues.json")
    if _count_terms(source_text, negation_terms) != _count_terms(translation, negation_terms):
        spans.append(
            {
                "start": 0,
                "end": len(source_text),
                "kind": "negation_mismatch",
                "severity": "critical",
                "term": "negation",
            }
        )
    return spans


def classify_risk(
    source_text: str,
    translation: str,
    asr_confidence: float,
    mt_confidence: float,
    confidence_threshold: float,
    glossary_hits: list[GlossaryEntry] | None = None,
) -> RiskResult:
    glossary_hits = glossary_hits or []
    spans: list[dict[str, Any]] = []
    combined = f"{source_text}\n{translation}"
    spans.extend(_term_spans(combined, load_lexicon("red_flags.json"), "red_flag", "critical"))
    spans.extend(
        _term_spans(
            combined,
            ["dị ứng", "phản vệ", "allergic", "allergy", "anaphylaxis"],
            "allergy",
            "critical",
        )
    )
    spans.extend(
        _term_spans(combined, load_lexicon("pregnancy.json"), "pregnancy", "critical")
    )
    spans.extend(_term_spans(combined, load_lexicon("laterality.json"), "laterality", "high"))
    spans.extend(_term_spans(combined, load_lexicon("routes.json"), "route", "high"))
    spans.extend(_negation_spans(combined))
    spans.extend(
        _term_spans(combined, load_lexicon("abbreviations_vi.json").keys(), "abbreviation", "high")
    )
    spans.extend(
        _term_spans(combined, load_lexicon("subject_omission.json"), "subject_omission", "high")
    )
    spans.extend(
        _term_spans(combined, load_lexicon("medical_history.json"), "medical_history", "high")
    )
    spans.extend(
        _literal_word_spans(combined, load_lexicon("pronoun_cues.json"), "pronoun", "medium")
    )
    spans.extend(
        _term_spans(combined, load_lexicon("body_locations.json"), "body_location", "medium")
    )
    spans.extend(
        _term_spans(combined, load_lexicon("symptom_severity.json"), "symptom_severity", "critical")
    )
    spans.extend(_dose_spans(combined))
    spans.extend(_frequency_spans(combined))
    spans.extend(_drug_spans(combined, glossary_hits))
    spans.extend(_mismatch_spans(source_text, translation))
    if asr_confidence < confidence_threshold or mt_confidence < confidence_threshold:
        spans.append(
            {
                "start": 0,
                "end": 0,
                "kind": "low_confidence",
                "severity": "low",
                "term": "confidence",
            }
        )

    tier = "low"
    for span in spans:
        if SEVERITY_RANK[span["severity"]] > SEVERITY_RANK[tier]:
            tier = span["severity"]
    return RiskResult(tier=tier, spans=spans)
