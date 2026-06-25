from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a CarePath retrieval term datastore from lexicon and datasets."
    )
    parser.add_argument("--lexicon", default="data/medical_lexicon.json")
    parser.add_argument("--pairs", nargs="*", default=[])
    parser.add_argument("--dataset", default=None, help="Optional HF dataset, e.g. tensorxt/ViMedCSS.")
    parser.add_argument("--splits", nargs="+", default=["train", "validation", "test", "hard"])
    parser.add_argument("--limit-per-split", type=int, default=None)
    parser.add_argument("--output", default="artifacts/retrieval/term_datastore.json")
    return parser.parse_args()


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "apps" / "api"))

    from hopegait.evaluation import split_terms

    args = parse_args()
    terms: dict[str, dict[str, Any]] = {}
    counts: Counter[str] = Counter()

    for entry in load_lexicon(Path(args.lexicon)):
        key = normalize_key(entry["term"])
        terms[key] = {
            **entry,
            "source": entry.get("source", "curated_lexicon"),
            "allow_fuzzy": bool(entry.get("allow_fuzzy", False)),
        }

    for pair_path in args.pairs:
        for row in read_jsonl(Path(pair_path)):
            for term in split_terms(row.get("cs_terms_list") or row.get("gold_terms")):
                merge_term(terms, counts, term, source="gec_pairs")

    if args.dataset:
        from datasets import load_dataset  # type: ignore

        for split in args.splits:
            dataset = load_dataset(args.dataset, split=split)
            if args.limit_per_split:
                dataset = dataset.select(range(min(args.limit_per_split, len(dataset))))
            for row in dataset:
                for term in split_terms(row.get("cs_terms_list")):
                    merge_term(terms, counts, term, source=f"{args.dataset}:{split}")

    output = {
        "metadata": {
            "version": 1,
            "sources": {
                "lexicon": args.lexicon,
                "pairs": args.pairs,
                "dataset": args.dataset,
            },
            "term_count": len(terms),
        },
        "terms": sorted(terms.values(), key=lambda item: item["term"].lower()),
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(terms)} terms to {output_path}")


def load_lexicon(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["terms"] if isinstance(payload, dict) else payload
    return [dict(row) for row in rows]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def merge_term(
    terms: dict[str, dict[str, Any]],
    counts: Counter[str],
    term: str,
    source: str,
) -> None:
    clean = term.strip()
    if not clean:
        return
    key = normalize_key(clean)
    counts[key] += 1
    if key not in terms:
        terms[key] = {
            "term": clean,
            "category": "code_switch",
            "aliases": [],
            "vietnamese": None,
            "source": source,
            "allow_fuzzy": False,
            "frequency": 0,
        }
    terms[key]["frequency"] = int(counts[key])


def normalize_key(term: str) -> str:
    return " ".join(term.lower().split())


if __name__ == "__main__":
    main()

