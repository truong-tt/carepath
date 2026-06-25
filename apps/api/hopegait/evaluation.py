from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class TermMetrics:
    precision: float
    recall: float
    f1: float
    true_positives: int
    false_positives: int
    false_negatives: int


@dataclass(frozen=True)
class PairMetrics:
    wer: float
    cer: float
    term_recall: float
    term_precision: float
    term_f1: float
    number_unit_preservation: float
    overcorrection_rate: float


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text)
    return text


def word_error_rate(reference: str, hypothesis: str) -> float:
    ref_words = normalize_text(reference).split()
    hyp_words = normalize_text(hypothesis).split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0
    return _edit_distance(ref_words, hyp_words) / len(ref_words)


def char_error_rate(reference: str, hypothesis: str) -> float:
    ref_chars = list(normalize_text(reference))
    hyp_chars = list(normalize_text(hypothesis))
    if not ref_chars:
        return 0.0 if not hyp_chars else 1.0
    return _edit_distance(ref_chars, hyp_chars) / len(ref_chars)


def term_recall(reference: str, hypothesis: str, terms: list[str]) -> float:
    return term_precision_recall_f1(reference, hypothesis, terms).recall


def term_precision_recall_f1(reference: str, hypothesis: str, terms: list[str]) -> TermMetrics:
    expected = {term for term in terms if _contains(reference, term)}
    predicted = {term for term in terms if _contains(hypothesis, term)}
    true_positives = len(expected & predicted)
    false_positives = len(predicted - expected)
    false_negatives = len(expected - predicted)
    precision = true_positives / len(predicted) if predicted else (1.0 if not expected else 0.0)
    recall = true_positives / len(expected) if expected else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
    return TermMetrics(
        precision=precision,
        recall=recall,
        f1=f1,
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
    )


def number_unit_preservation(reference: str, hypothesis: str) -> float:
    ref_items = set(extract_numbers_and_units(reference))
    if not ref_items:
        return 1.0
    hyp_items = set(extract_numbers_and_units(hypothesis))
    return len(ref_items & hyp_items) / len(ref_items)


def extract_numbers_and_units(text: str) -> list[str]:
    pattern = re.compile(
        r"\b\d+(?:[.,]\d+)?\s*(?:%|mmhg|mg/dl|mg/dL|mg|g|mcg|microgram|ml|l|bpm)?\b",
        flags=re.IGNORECASE,
    )
    return [re.sub(r"\s+", "", item.group(0).lower()) for item in pattern.finditer(text)]


def score_pair(reference: str, hypothesis: str, terms: list[str]) -> PairMetrics:
    term_metrics = term_precision_recall_f1(reference, hypothesis, terms)
    return PairMetrics(
        wer=word_error_rate(reference, hypothesis),
        cer=char_error_rate(reference, hypothesis),
        term_recall=term_metrics.recall,
        term_precision=term_metrics.precision,
        term_f1=term_metrics.f1,
        number_unit_preservation=number_unit_preservation(reference, hypothesis),
        overcorrection_rate=0.0,
    )


def score_correction(
    reference: str,
    raw_hypothesis: str,
    corrected_hypothesis: str,
    terms: list[str],
) -> PairMetrics:
    term_metrics = term_precision_recall_f1(reference, corrected_hypothesis, terms)
    return PairMetrics(
        wer=word_error_rate(reference, corrected_hypothesis),
        cer=char_error_rate(reference, corrected_hypothesis),
        term_recall=term_metrics.recall,
        term_precision=term_metrics.precision,
        term_f1=term_metrics.f1,
        number_unit_preservation=number_unit_preservation(reference, corrected_hypothesis),
        overcorrection_rate=overcorrection_rate(
            reference, raw_hypothesis, corrected_hypothesis
        ),
    )


def average_metrics(metrics: list[PairMetrics]) -> PairMetrics:
    if not metrics:
        return PairMetrics(
            wer=0.0,
            cer=0.0,
            term_recall=0.0,
            term_precision=0.0,
            term_f1=0.0,
            number_unit_preservation=0.0,
            overcorrection_rate=0.0,
        )
    return PairMetrics(
        wer=sum(item.wer for item in metrics) / len(metrics),
        cer=sum(item.cer for item in metrics) / len(metrics),
        term_recall=sum(item.term_recall for item in metrics) / len(metrics),
        term_precision=sum(item.term_precision for item in metrics) / len(metrics),
        term_f1=sum(item.term_f1 for item in metrics) / len(metrics),
        number_unit_preservation=sum(item.number_unit_preservation for item in metrics)
        / len(metrics),
        overcorrection_rate=sum(item.overcorrection_rate for item in metrics)
        / len(metrics),
    )


def overcorrection_rate(
    reference: str,
    raw_hypothesis: str,
    corrected_hypothesis: str,
) -> float:
    ref_tokens = normalize_text(reference).split()
    raw_tokens = normalize_text(raw_hypothesis).split()
    corrected_tokens = normalize_text(corrected_hypothesis).split()
    aligned_count = min(len(ref_tokens), len(raw_tokens), len(corrected_tokens))
    if aligned_count == 0:
        return 0.0

    already_correct = 0
    changed_away = 0
    for idx in range(aligned_count):
        if raw_tokens[idx] == ref_tokens[idx]:
            already_correct += 1
            if corrected_tokens[idx] != ref_tokens[idx]:
                changed_away += 1
    if already_correct == 0:
        return 0.0
    return changed_away / already_correct


def split_terms(raw: str | list[str] | None) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    return [item.strip() for item in str(raw).split(";") if item.strip()]


def _contains(text: str, needle: str) -> bool:
    return normalize_text(needle) in normalize_text(text)


def _edit_distance(reference: list[str], hypothesis: list[str]) -> int:
    prev = list(range(len(hypothesis) + 1))
    for i, ref_item in enumerate(reference, start=1):
        current = [i]
        for j, hyp_item in enumerate(hypothesis, start=1):
            cost = 0 if ref_item == hyp_item else 1
            current.append(
                min(
                    prev[j] + 1,
                    current[j - 1] + 1,
                    prev[j - 1] + cost,
                )
            )
        prev = current
    return prev[-1]
