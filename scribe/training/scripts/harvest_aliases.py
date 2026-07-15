"""CLI: enrich the datastore with real ASR confusions, then refresh retrievals.

Replaces a hand-built phonetic table (paper Limitation #1): we read how the
deployed ASR actually mangles each term from the (gold_text, raw_asr) pairs,
write those renderings back as datastore aliases, and — with ``--refresh`` —
re-retrieve over every pair's ``raw_asr`` so the corrected NE shows up in the
GEC prompt. Run after the pairs exist (real + labeled + synthetic).

    python scribe/training/scripts/harvest_aliases.py \
      --datastore artifacts/retrieval/term_datastore.json \
      --pairs artifacts/pairs/real.jsonl artifacts/pairs/synth.jsonl \
      --refresh --backend lexical
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

from gec.data import read_jsonl, write_jsonl  # noqa: E402
from gec.harvest import enrich_datastore, rows_for_alias_mining  # noqa: E402
from gec.retrieval import build_ne_retriever  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datastore", required=True, help="datastore JSON (updated in place)")
    parser.add_argument("--pairs", nargs="+", required=True, help="pair JSONL files to mine")
    parser.add_argument("--min-count", type=int, default=1,
                        help="min times a rendering must occur to become an alias")
    parser.add_argument("--max-aliases", type=int, default=4)
    parser.add_argument(
        "--mine-split",
        default="train",
        help="only this split may teach confusion aliases; refresh may still read raw held-out ASR",
    )
    parser.add_argument("--refresh", action="store_true",
                        help="re-retrieve retrieved_terms over raw_asr with the enriched datastore")
    parser.add_argument("--backend", default="lexical", choices=["lexical", "semantic", "hybrid"])
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    datastore_path = Path(args.datastore)
    payload = json.loads(datastore_path.read_text(encoding="utf-8"))

    all_rows: list[dict] = []
    for pair_file in args.pairs:
        all_rows.extend(read_jsonl(Path(pair_file)))

    mining_rows = rows_for_alias_mining(all_rows, args.mine_split)
    enrich_datastore(payload, mining_rows, min_count=args.min_count, max_aliases=args.max_aliases)
    datastore_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    harvested = payload.get("metadata", {}).get("harvested_terms", 0)
    print(f"Enriched {harvested} term(s) with harvested ASR-confusion aliases -> {datastore_path}")

    if not args.refresh:
        return

    retriever = build_ne_retriever(datastore_path, backend=args.backend, top_k=args.top_k)
    for pair_file in args.pairs:
        path = Path(pair_file)
        rows = read_jsonl(path)
        changed = 0
        for row in rows:
            raw = row.get("raw_asr")
            if not raw:
                continue
            terms = [t.term for t in retriever.retrieve(str(raw))]
            if terms != row.get("retrieved_terms"):
                row["retrieved_terms"] = terms
                changed += 1
        write_jsonl(path, rows)
        print(f"  refreshed retrieved_terms on {changed}/{len(rows)} rows in {path.name}")


if __name__ == "__main__":
    main()
