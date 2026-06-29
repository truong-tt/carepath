"""CLI: merge real + synthetic GEC pairs into one augmented training file (paper §5).

Keeps the real validation/test/hard splits frozen and adds up to ``nsyn = factor * n``
synthetic pairs to the train split.

    python scripts/gec/augment.py \
      --real artifacts/gec_pairs/vimedcss_gipformer_pairs_smoke.jsonl \
      --synthetic artifacts/gec_pairs/darag_synthetic_pairs_smoke.jsonl \
      --output artifacts/gec_pairs/darag_augmented_smoke.jsonl --nsyn-factor 1.0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from carepath.gec.cliutil import configure_stdout  # noqa: E402

configure_stdout()

from carepath.gec.data import augment_training_pairs, read_jsonl, write_jsonl  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--real",
        required=True,
        nargs="+",
        help="Real GEC pairs JSONL(s) — ViMedCSS plus optional supplementary labeled pairs.",
    )
    parser.add_argument("--synthetic", default=None, help="Synthetic GEC pairs JSONL (train only).")
    parser.add_argument("--output", required=True)
    parser.add_argument("--nsyn-factor", type=float, default=1.0)
    args = parser.parse_args()

    real = [row for path in args.real for row in read_jsonl(Path(path))]
    synthetic = read_jsonl(Path(args.synthetic)) if args.synthetic else []
    merged = augment_training_pairs(real, synthetic, nsyn_factor=args.nsyn_factor)
    count = write_jsonl(Path(args.output), merged)
    n_synth = sum(1 for r in merged if r.get("source_kind") == "darag_synthetic_tts")
    print(f"Wrote {count} augmented pairs ({n_synth} synthetic train rows) to {args.output}")


if __name__ == "__main__":
    main()
