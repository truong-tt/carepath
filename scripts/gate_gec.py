"""Acceptance gate for the trained GEC adapter.

Reads the JSON report produced by ``scripts/evaluate_gec_runs.py`` and decides
whether the trained model (``gec_pred``) has earned its place. The CarePath rule
(see README "GEC Methodology") is: the trained model is accepted only if, on the
frozen ``validation`` and ``hard`` splits, it is at least as good as each baseline
(raw Gipformer and, when present, the LLM/RAG correction) on WER and term-F1, and
does not regress number/unit preservation beyond a small tolerance.

Exit code is non-zero on REJECT so the notebook / CI can gate shipping on it.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gate a trained GEC adapter on its metrics.")
    parser.add_argument("--report", required=True, help="JSON from evaluate_gec_runs.py")
    parser.add_argument("--candidate", default="gec_pred")
    parser.add_argument(
        "--baselines",
        nargs="+",
        default=["raw_asr", "corrected_text"],
        help="Baselines the candidate must match-or-beat (absent ones are skipped).",
    )
    parser.add_argument("--splits", nargs="+", default=["validation", "hard"])
    parser.add_argument(
        "--number-unit-epsilon",
        type=float,
        default=0.02,
        help="Allowed drop in number/unit preservation vs a baseline.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report: dict[str, Any] = json.loads(Path(args.report).read_text(encoding="utf-8"))

    if args.candidate not in report:
        print(f"REJECT: report has no candidate column '{args.candidate}'.")
        return 1

    candidate = report[args.candidate]
    present_baselines = [b for b in args.baselines if b in report]
    skipped = [b for b in args.baselines if b not in report]
    for name in skipped:
        print(f"note: baseline '{name}' absent from report — skipping that comparison.")

    failures: list[str] = []
    checked_any = False

    for split in args.splits:
        cand = candidate.get(split)
        if cand is None:
            failures.append(f"{split}: candidate has no metrics for this split")
            continue
        for baseline_name in present_baselines:
            base = report[baseline_name].get(split)
            if base is None:
                continue
            checked_any = True
            failures.extend(
                _compare(split, baseline_name, base, cand, args.number_unit_epsilon)
            )

    print(f"\nGate: candidate='{args.candidate}' vs {present_baselines} on splits {args.splits}")
    if not checked_any:
        print("REJECT: no overlapping split/baseline metrics to evaluate.")
        return 1
    if failures:
        print("REJECT — the trained adapter did not clear the bar:")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("ACCEPT — trained adapter matches or beats every baseline on every split.")
    return 0


def _compare(
    split: str,
    baseline_name: str,
    base: dict[str, Any],
    cand: dict[str, Any],
    number_unit_epsilon: float,
) -> list[str]:
    issues: list[str] = []
    tag = f"{split} vs {baseline_name}"
    # WER: lower is better — candidate must not be worse.
    if cand["wer"] > base["wer"] + 1e-9:
        issues.append(f"{tag}: WER {cand['wer']:.4f} > {base['wer']:.4f}")
    # term-F1: higher is better — candidate must not be worse.
    if cand["term_f1"] + 1e-9 < base["term_f1"]:
        issues.append(f"{tag}: term_f1 {cand['term_f1']:.4f} < {base['term_f1']:.4f}")
    # number/unit preservation: allow a small regression only.
    if cand["number_unit_preservation"] + number_unit_epsilon < base["number_unit_preservation"]:
        issues.append(
            f"{tag}: number_unit_preservation {cand['number_unit_preservation']:.4f} "
            f"< {base['number_unit_preservation']:.4f} - {number_unit_epsilon}"
        )
    return issues


if __name__ == "__main__":
    raise SystemExit(main())
