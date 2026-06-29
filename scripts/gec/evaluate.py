"""CLI: WER comparison + NE-F1 ablation table (paper Tables 3 & 4).

    python scripts/gec/evaluate.py \
      --input artifacts/evaluations/darag_all_preds.jsonl \
      --prediction-columns raw_asr corrected_text gec_pred \
      --wer-output artifacts/evaluations/darag_wer.json \
      --ne-f1-output artifacts/evaluations/darag_ne_f1.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from carepath.gec.cliutil import configure_stdout  # noqa: E402

configure_stdout()

from carepath.gec.evaluate import build_reports, render_ne_f1_table  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--prediction-columns", nargs="+", default=["raw_asr", "corrected_text", "gec_pred"])
    parser.add_argument("--wer-output", default="artifacts/evaluations/darag_wer.json")
    parser.add_argument("--ne-f1-output", default="artifacts/evaluations/darag_ne_f1.json")
    args = parser.parse_args()

    reports = build_reports(
        input_path=Path(args.input),
        prediction_columns=args.prediction_columns,
        wer_output=Path(args.wer_output) if args.wer_output else None,
        ne_f1_output=Path(args.ne_f1_output) if args.ne_f1_output else None,
    )
    print("== WER / term-F1 (paper Table 3) ==")
    print(json.dumps(reports["wer"], ensure_ascii=False, indent=2))
    print("\n== NE micro-F1 ablation (paper Table 4) ==")
    print(render_ne_f1_table(reports["ne_f1"]))


if __name__ == "__main__":
    main()
