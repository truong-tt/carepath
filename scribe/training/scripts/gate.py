"""CLI: acceptance gate for the trained GEC adapter (exit non-zero on REJECT).

Optional ``--safety-report`` enforces frozen-fixture drug-name and dosage
non-regression before a serving bundle may be exported.

    python scribe/training/scripts/gate.py --report artifacts/evaluations/darag_wer.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scribe" / "training"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scribe"))

from gec.cliutil import configure_stdout  # noqa: E402

configure_stdout()

from gec.config import GATE_SPLITS  # noqa: E402
from gec.gate import run_gate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, help="WER report JSON from evaluate.py")
    parser.add_argument("--candidate", default="gec_pred")
    parser.add_argument("--baselines", nargs="+", default=["raw_asr", "corrected_text"])
    parser.add_argument("--splits", nargs="+", default=list(GATE_SPLITS))
    parser.add_argument("--number-unit-epsilon", type=float, default=0.02)
    parser.add_argument("--safety-report", default=None, help="stratified frozen-eval JSON report")
    parser.add_argument("--safety-split", default="frozen")
    args = parser.parse_args()

    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    safety_report = (
        json.loads(Path(args.safety_report).read_text(encoding="utf-8"))
        if args.safety_report
        else None
    )
    accepted, lines = run_gate(
        report,
        candidate=args.candidate,
        baselines=tuple(args.baselines),
        splits=tuple(args.splits),
        number_unit_epsilon=args.number_unit_epsilon,
        safety_report=safety_report,
        safety_split=args.safety_split,
    )
    print("\n".join(lines))
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
