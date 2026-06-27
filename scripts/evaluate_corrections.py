from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate raw ASR/corrections against gold transcripts."
    )
    parser.add_argument("--input", required=True, help="JSONL with gold_text and prediction columns.")
    parser.add_argument(
        "--prediction-column",
        default="raw_asr",
        help="Column to compare against gold_text, e.g. raw_asr or corrected_text.",
    )
    return parser.parse_args()


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "apps" / "api"))

    from carepath.evaluation import average_metrics, score_correction, score_pair, split_terms

    args = parse_args()
    rows = [json.loads(line) for line in Path(args.input).read_text(encoding="utf-8").splitlines()]
    metrics_by_split: dict[str, list] = {}
    for row in rows:
        split = row.get("split", "unknown")
        terms = row.get("gold_terms") or split_terms(row.get("cs_terms_list"))
        if args.prediction_column != "raw_asr" and row.get("raw_asr"):
            metric = score_correction(
                reference=row["gold_text"],
                raw_hypothesis=row["raw_asr"],
                corrected_hypothesis=row[args.prediction_column],
                terms=terms,
            )
        else:
            metric = score_pair(
                reference=row["gold_text"],
                hypothesis=row[args.prediction_column],
                terms=terms,
            )
        metrics_by_split.setdefault(split, []).append(
            metric
        )

    print(json.dumps({"prediction_column": args.prediction_column}, indent=2))
    for split, metrics in sorted(metrics_by_split.items()):
        avg = average_metrics(metrics)
        print(
            json.dumps(
                {
                    "split": split,
                    "n": len(metrics),
                    "wer": round(avg.wer, 4),
                    "cer": round(avg.cer, 4),
                    "term_precision": round(avg.term_precision, 4),
                    "term_recall": round(avg.term_recall, 4),
                    "term_f1": round(avg.term_f1, 4),
                    "number_unit_preservation": round(avg.number_unit_preservation, 4),
                    "overcorrection_rate": round(avg.overcorrection_rate, 4),
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
