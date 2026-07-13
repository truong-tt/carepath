"""Standalone GEC metrics (no ML dependencies).

Paper-faithful: WER (paper's primary metric, Tables 1/3/5), and NE F1 over
code-switched medical terms (paper Tables 2/4). CarePath adds two clinical
guardrails the paper does not need — number/unit preservation and an
overcorrection rate — so the acceptance gate can refuse a model that improves
fluency while silently dropping a dose or a vital.

NE F1 is offered two ways:
* per-pair macro P/R/F1 (used inside ``PairMetrics`` averages), and
* a corpus ``TermConfusion`` of summed TP/FP/FN so the NE-F1 ablation table can
  report **micro**-F1, matching the paper's F1-micro reporting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from carepath_shared.normalize import normalize_for_metrics as normalize_text


@dataclass(frozen=True)
class TermConfusion:
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    def __add__(self, other: "TermConfusion") -> "TermConfusion":
        return TermConfusion(
            self.true_positives + other.true_positives,
            self.false_positives + other.false_positives,
            self.false_negatives + other.false_negatives,
        )

    @property
    def precision(self) -> float:
        denom = self.true_positives + self.false_positives
        return self.true_positives / denom if denom else 1.0

    @property
    def recall(self) -> float:
        denom = self.true_positives + self.false_negatives
        return self.true_positives / denom if denom else 1.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0


@dataclass(frozen=True)
class PairMetrics:
    wer: float
    cer: float
    term_precision: float
    term_recall: float
    term_f1: float
    number_unit_preservation: float
    overcorrection_rate: float


def word_error_rate(reference: str, hypothesis: str, segment: bool = False) -> float:
    """Word/syllable error rate.

    Default ``segment=False`` splits on whitespace, which for Vietnamese is
    *syllable*-level error rate — the standard ASR convention for the language.
    ``segment=True`` first runs pyvi word segmentation (multi-syllable words become
    single tokens) to give a true word-level WER; if pyvi is unavailable it falls
    back to syllable tokens rather than failing.
    """

    ref = _wer_tokens(normalize_text(reference), segment)
    hyp = _wer_tokens(normalize_text(hypothesis), segment)
    if not ref:
        return 0.0 if not hyp else 1.0
    return _edit_distance(ref, hyp) / len(ref)


def _wer_tokens(text: str, segment: bool) -> list[str]:
    if segment and text:
        try:
            from pyvi import ViTokenizer  # type: ignore

            text = ViTokenizer.tokenize(text)
        except Exception:
            pass
    return text.split()


def char_error_rate(reference: str, hypothesis: str) -> float:
    ref = list(normalize_text(reference))
    hyp = list(normalize_text(hypothesis))
    if not ref:
        return 0.0 if not hyp else 1.0
    return _edit_distance(ref, hyp) / len(ref)


def term_confusion(reference: str, hypothesis: str, terms: list[str]) -> TermConfusion:
    """TP/FP/FN of NE presence: a term counts if it is correctly rendered.

    Expected = terms that appear in the gold transcript; predicted = terms that
    appear in the hypothesis. This is the same presence test the runtime
    retriever uses, so training and evaluation agree on what "the NE is correct"
    means.
    """

    expected = {t for t in terms if _contains(reference, t)}
    predicted = {t for t in terms if _contains(hypothesis, t)}
    return TermConfusion(
        true_positives=len(expected & predicted),
        false_positives=len(predicted - expected),
        false_negatives=len(expected - predicted),
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
    return [re.sub(r"\s+", "", m.group(0).lower()) for m in pattern.finditer(text)]


def overcorrection_rate(reference: str, raw_hypothesis: str, corrected_hypothesis: str) -> float:
    ref = normalize_text(reference).split()
    raw = normalize_text(raw_hypothesis).split()
    corrected = normalize_text(corrected_hypothesis).split()
    aligned = min(len(ref), len(raw), len(corrected))
    if aligned == 0:
        return 0.0
    already_correct = 0
    changed_away = 0
    for idx in range(aligned):
        if raw[idx] == ref[idx]:
            already_correct += 1
            if corrected[idx] != ref[idx]:
                changed_away += 1
    return changed_away / already_correct if already_correct else 0.0


def score_pair(reference: str, hypothesis: str, terms: list[str]) -> PairMetrics:
    confusion = term_confusion(reference, hypothesis, terms)
    return PairMetrics(
        wer=word_error_rate(reference, hypothesis),
        cer=char_error_rate(reference, hypothesis),
        term_precision=confusion.precision,
        term_recall=confusion.recall,
        term_f1=confusion.f1,
        number_unit_preservation=number_unit_preservation(reference, hypothesis),
        overcorrection_rate=0.0,
    )


def score_correction(
    reference: str,
    raw_hypothesis: str,
    corrected_hypothesis: str,
    terms: list[str],
) -> PairMetrics:
    metrics = score_pair(reference, corrected_hypothesis, terms)
    return PairMetrics(
        wer=metrics.wer,
        cer=metrics.cer,
        term_precision=metrics.term_precision,
        term_recall=metrics.term_recall,
        term_f1=metrics.term_f1,
        number_unit_preservation=metrics.number_unit_preservation,
        overcorrection_rate=overcorrection_rate(reference, raw_hypothesis, corrected_hypothesis),
    )


def average_metrics(metrics: list[PairMetrics]) -> PairMetrics:
    if not metrics:
        return PairMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    n = len(metrics)
    return PairMetrics(
        wer=sum(m.wer for m in metrics) / n,
        cer=sum(m.cer for m in metrics) / n,
        term_precision=sum(m.term_precision for m in metrics) / n,
        term_recall=sum(m.term_recall for m in metrics) / n,
        term_f1=sum(m.term_f1 for m in metrics) / n,
        number_unit_preservation=sum(m.number_unit_preservation for m in metrics) / n,
        overcorrection_rate=sum(m.overcorrection_rate for m in metrics) / n,
    )


def split_terms(raw: str | list[str] | None) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    return [item.strip() for item in str(raw).split(";") if item.strip()]


def _contains(text: str, needle: str) -> bool:
    return normalize_text(needle) in normalize_text(text)


def _edit_distance(reference: list, hypothesis: list) -> int:
    prev = list(range(len(hypothesis) + 1))
    for i, ref_item in enumerate(reference, start=1):
        current = [i]
        for j, hyp_item in enumerate(hypothesis, start=1):
            cost = 0 if ref_item == hyp_item else 1
            current.append(min(prev[j] + 1, current[j - 1] + 1, prev[j - 1] + cost))
        prev = current
    return prev[-1]
