"""Write or verify the committed GEC frozen-fixture baseline report.

    python scribe/training/scripts/baseline_report.py --write
    python scribe/training/scripts/baseline_report.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scribe" / "training"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scribe"))

from gec.baseline import build_baseline_report  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("scribe/training/configs/frozen-baseline-v1.json"))
    parser.add_argument("--output", type=Path, default=Path("scribe/training/reports/gec-frozen-baseline-v1.json"))
    parser.add_argument("--write", action="store_true", help="write the deterministic report")
    parser.add_argument("--check", action="store_true", help="verify without rewriting (default)")
    args = parser.parse_args()

    if args.write and args.check:
        parser.error("--write and --check are mutually exclusive")

    expected = build_baseline_report(args.config)
    if args.write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(expected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote frozen baseline report -> {args.output}")
        return
    if not args.output.is_file():
        raise SystemExit(f"baseline report not found: {args.output}; run with --write")
    actual = json.loads(args.output.read_text(encoding="utf-8"))
    if actual != expected:
        raise SystemExit("baseline report drifted; regenerate with scribe/training/scripts/baseline_report.py --write")
    print(f"Frozen baseline report verified -> {args.output}")


if __name__ == "__main__":
    main()
