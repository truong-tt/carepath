from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare raw ASR, LLM/RAG, and trained GEC predictions."
    )
    parser.add_argument("--input", required=True)
    parser.add_argument(
        "--prediction-columns",
        nargs="+",
        default=["raw_asr", "corrected_text"],
    )
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "apps" / "api"))

    from carepath.evaluation import average_metrics, score_correction, score_pair, split_terms

    args = parse_args()
    rows = read_jsonl(Path(args.input))
    report = {}
    for column in args.prediction_columns:
        metrics_by_split = {}
        for row in rows:
            if column not in row:
                continue
            split = row.get("split", "unknown")
            terms = row.get("gold_terms") or split_terms(row.get("cs_terms_list"))
            if column != "raw_asr" and row.get("raw_asr"):
                metric = score_correction(row["gold_text"], row["raw_asr"], row[column], terms)
            else:
                metric = score_pair(row["gold_text"], row[column], terms)
            metrics_by_split.setdefault(split, []).append(metric)
        report[column] = {
            split: summarize(average_metrics(metrics), len(metrics))
            for split, metrics in sorted(metrics_by_split.items())
        }

    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    print(text)


def summarize(metrics, count: int) -> dict:
    return {
        "n": count,
        "wer": round(metrics.wer, 4),
        "cer": round(metrics.cer, 4),
        "term_precision": round(metrics.term_precision, 4),
        "term_recall": round(metrics.term_recall, 4),
        "term_f1": round(metrics.term_f1, 4),
        "number_unit_preservation": round(metrics.number_unit_preservation, 4),
        "overcorrection_rate": round(metrics.overcorrection_rate, 4),
    }


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


if __name__ == "__main__":
    main()
