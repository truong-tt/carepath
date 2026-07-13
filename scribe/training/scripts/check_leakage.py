"""CLI: leakage / memorization report for synthetic data (paper App. C / Table 6).

    python scribe/training/scripts/check_leakage.py \
      --synthetic artifacts/synthetic/synthetic_clean_smoke.jsonl \
      --real artifacts/gec_pairs/vimedcss_gipformer_pairs_smoke.jsonl \
      --output artifacts/evaluations/leakage_smoke.json

Requires the training extras (sentence-transformers, sacrebleu).
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

from gec.data import read_jsonl  # noqa: E402
from gec.leakage import leakage_report  # noqa: E402
from gec.retrieval import DEFAULT_SEMANTIC_MODEL  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic", required=True, help="synthetic_clean.jsonl (clean_text).")
    parser.add_argument("--real", required=True, help="GEC pairs JSONL (gold_text/segment_text).")
    parser.add_argument("--model", default=DEFAULT_SEMANTIC_MODEL)
    parser.add_argument("--label", default="synthetic")
    parser.add_argument("--output", default="artifacts/evaluations/leakage.json")
    args = parser.parse_args()

    synthetic_texts = [
        r["clean_text"] for r in read_jsonl(Path(args.synthetic)) if r.get("clean_text")
    ]
    real_texts = [
        str(r.get("gold_text") or r.get("segment_text") or "").strip()
        for r in read_jsonl(Path(args.real))
        if str(r.get("gold_text") or r.get("segment_text") or "").strip()
    ]

    report = leakage_report(synthetic_texts, real_texts, model_name=args.model, dataset_label=args.label)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
