"""CLI: build the NE / code-switch term datastore (paper §4.2 Step 1).

    python scribe/training/scripts/build_datastore.py \
      --dataset tensorxt/ViMedCSS --limit-per-split 20 \
      --output artifacts/retrieval/term_datastore_smoke.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scribe" / "training"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scribe"))

from gec.cliutil import configure_stdout  # noqa: E402

configure_stdout()

from gec.datastore import build_datastore, write_datastore  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lexicon", default="data/medical_lexicon.json")
    parser.add_argument("--pairs", nargs="*", default=[])
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--splits", nargs="+", default=["train", "validation", "test", "hard"])
    parser.add_argument("--limit-per-split", type=int, default=None)
    parser.add_argument("--output", default="artifacts/retrieval/term_datastore.json")
    args = parser.parse_args()

    payload = build_datastore(
        lexicon_path=Path(args.lexicon),
        pair_paths=[Path(p) for p in args.pairs],
        dataset=args.dataset,
        splits=tuple(args.splits),
        limit_per_split=args.limit_per_split,
    )
    write_datastore(payload, Path(args.output))
    print(f"Wrote {payload['metadata']['term_count']} terms to {args.output}")


if __name__ == "__main__":
    main()
