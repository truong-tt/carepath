from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate medical/code-switch term retrieval over GEC pair JSONL."
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--lexicon", default="data/medical_lexicon.json")
    parser.add_argument("--text-column", default="raw_asr")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--backend",
        choices=["lexical", "semantic", "hybrid"],
        default="lexical",
        help="Retrieval backend; semantic/hybrid use the Vietnamese bi-encoder.",
    )
    parser.add_argument(
        "--semantic-model",
        default="bkai-foundation-models/vietnamese-bi-encoder",
    )
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "apps" / "api"))

    from carepath.evaluation import split_terms
    from carepath.services.retrieval import (
        HybridTermRetriever,
        MedicalTermRetriever,
        SemanticTermRetriever,
    )

    args = parse_args()
    rows = read_jsonl(Path(args.input))
    if args.limit:
        rows = rows[: args.limit]

    lexicon = Path(args.lexicon)
    lexical = MedicalTermRetriever(lexicon, top_k=args.top_k)
    if args.backend == "lexical":
        retriever = lexical
    else:
        semantic = SemanticTermRetriever(
            lexicon, top_k=args.top_k, model_name=args.semantic_model
        )
        retriever = (
            semantic
            if args.backend == "semantic"
            else HybridTermRetriever(lexical, semantic, top_k=args.top_k)
        )
    details = []
    total_tp = total_fp = total_fn = 0
    for row in rows:
        expected = set(split_terms(row.get("cs_terms_list") or row.get("gold_terms")))
        predicted = {
            item.term for item in retriever.retrieve(str(row.get(args.text_column, "")), args.top_k)
        }
        tp = len(expected & predicted)
        fp = len(predicted - expected)
        fn = len(expected - predicted)
        total_tp += tp
        total_fp += fp
        total_fn += fn
        details.append(
            {
                "id": row.get("audio_id") or row.get("synthetic_id"),
                "expected": sorted(expected),
                "predicted": sorted(predicted),
                "false_positives": sorted(predicted - expected),
                "false_negatives": sorted(expected - predicted),
            }
        )

    precision = total_tp / (total_tp + total_fp) if total_tp + total_fp else 1.0
    recall = total_tp / (total_tp + total_fn) if total_tp + total_fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    report = {
        "n": len(rows),
        "backend": args.backend,
        "top_k": args.top_k,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "true_positives": total_tp,
        "false_positives": total_fp,
        "false_negatives": total_fn,
        "examples": details[:20],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    print(text)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


if __name__ == "__main__":
    main()
