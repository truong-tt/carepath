"""Acceptance gate for the trained GEC adapter (no ML dependencies).

CarePath ships the trained model only if it earns its place. Given the WER report
from ``evaluate.wer_report``, the candidate (``gec_pred``) is accepted iff, on the
frozen ``validation`` and ``hard`` splits, it is at least as good as every present
baseline (raw Gipformer and, when available, the LLM/RAG correction) on WER and
term-F1, and does not regress number/unit preservation beyond a small tolerance.

``run_gate`` returns ``(accepted, lines)``; the CLI turns that into an exit code so
a notebook / CI can block shipping on a REJECT.
"""

from __future__ import annotations

from typing import Any

from gec.config import GATE_SPLITS

SAFETY_WEIGHTED_METRICS = {
    "drug_name": "term_recall",
    "dosage": "number_unit_preservation",
}


def run_gate(
    report: dict[str, Any],
    candidate: str = "gec_pred",
    baselines: tuple[str, ...] = ("raw_asr", "corrected_text"),
    splits: tuple[str, ...] = GATE_SPLITS,
    number_unit_epsilon: float = 0.02,
    safety_report: dict[str, Any] | None = None,
    safety_split: str = "frozen",
) -> tuple[bool, list[str]]:
    lines: list[str] = []
    if candidate not in report:
        return False, [f"REJECT: report has no candidate column '{candidate}'."]

    cand_metrics = report[candidate]
    present = [b for b in baselines if b in report]
    for name in baselines:
        if name not in report:
            lines.append(f"note: baseline '{name}' absent from report — skipping.")

    failures: list[str] = []
    checked_any = False
    for split in splits:
        cand = cand_metrics.get(split)
        if cand is None:
            failures.append(f"{split}: candidate has no metrics for this split")
            continue
        for baseline_name in present:
            base = report[baseline_name].get(split)
            if base is None:
                continue
            checked_any = True
            failures.extend(_compare(split, baseline_name, base, cand, number_unit_epsilon))

    lines.append(f"Gate: candidate='{candidate}' vs {present} on splits {list(splits)}")
    if not checked_any:
        return False, lines + ["REJECT: no overlapping split/baseline metrics to evaluate."]
    if safety_report is not None:
        safety_failures = _compare_safety_weighted(
            safety_report, candidate, present, safety_split
        )
        lines.append(
            "Safety-weighted gate: drug_name.term_recall and "
            "dosage.number_unit_preservation must not regress."
        )
        failures.extend(safety_failures)
    if failures:
        return False, lines + ["REJECT — the trained adapter did not clear the bar:"] + [
            f"  - {line}" for line in failures
        ]
    return True, lines + ["ACCEPT — trained adapter matches or beats every baseline on every split."]


def _compare_safety_weighted(
    report: dict[str, Any],
    candidate: str,
    baselines: list[str],
    split: str,
) -> list[str]:
    issues: list[str] = []
    for category, metric in SAFETY_WEIGHTED_METRICS.items():
        category_report = report.get(category, {})
        candidate_metrics = category_report.get(candidate, {}).get(split)
        if candidate_metrics is None:
            issues.append(f"safety {category}: candidate has no metrics for {split}")
            continue
        for baseline in baselines:
            baseline_metrics = category_report.get(baseline, {}).get(split)
            if baseline_metrics is None:
                issues.append(f"safety {category}: baseline '{baseline}' has no metrics for {split}")
                continue
            if candidate_metrics[metric] + 1e-9 < baseline_metrics[metric]:
                issues.append(
                    f"safety {category}: {metric} {candidate_metrics[metric]:.4f} "
                    f"< {baseline} {baseline_metrics[metric]:.4f}"
                )
    return issues


def _compare(
    split: str,
    baseline_name: str,
    base: dict[str, Any],
    cand: dict[str, Any],
    number_unit_epsilon: float,
) -> list[str]:
    issues: list[str] = []
    tag = f"{split} vs {baseline_name}"
    if cand["wer"] > base["wer"] + 1e-9:
        issues.append(f"{tag}: WER {cand['wer']:.4f} > {base['wer']:.4f}")
    if cand["term_f1"] + 1e-9 < base["term_f1"]:
        issues.append(f"{tag}: term_f1 {cand['term_f1']:.4f} < {base['term_f1']:.4f}")
    if cand["number_unit_preservation"] + number_unit_epsilon < base["number_unit_preservation"]:
        issues.append(
            f"{tag}: number_unit_preservation {cand['number_unit_preservation']:.4f} "
            f"< {base['number_unit_preservation']:.4f} - {number_unit_epsilon}"
        )
    return issues
