"""CLI: acceptance gate for the trained GEC adapter (exit non-zero on REJECT).

    python scripts/gec/gate.py --report artifacts/evaluations/darag_wer.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from carepath.gec.cliutil import configure_stdout  # noqa: E402

configure_stdout()

from carepath.gec.config import GATE_SPLITS  # noqa: E402
from carepath.gec.gate import run_gate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, help="WER report JSON from evaluate.py")
    parser.add_argument("--candidate", default="gec_pred")
    parser.add_argument("--baselines", nargs="+", default=["raw_asr", "corrected_text"])
    parser.add_argument("--splits", nargs="+", default=list(GATE_SPLITS))
    parser.add_argument("--number-unit-epsilon", type=float, default=0.02)
    args = parser.parse_args()

    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    accepted, lines = run_gate(
        report,
        candidate=args.candidate,
        baselines=tuple(args.baselines),
        splits=tuple(args.splits),
        number_unit_epsilon=args.number_unit_epsilon,
    )
    print("\n".join(lines))
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
