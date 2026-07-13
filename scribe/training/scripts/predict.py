"""CLI: run a trained QLoRA GEC adapter over pairs to add a prediction column.

    python scribe/training/scripts/predict.py \
      --pairs artifacts/evaluations/ckey_rag_smoke.jsonl \
      --adapter-dir artifacts/gec_lora/qwen3_full \
      --output artifacts/evaluations/darag_all_preds.jsonl --column gec_pred
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scribe" / "training"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scribe"))

from gec.cliutil import configure_stdout  # noqa: E402

configure_stdout()

from gec.config import DEFAULT_BASE_MODEL, FALLBACK_BASE_MODEL  # noqa: E402
from gec.predict import predict_pairs  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", required=True)
    parser.add_argument("--adapter-dir", default="artifacts/gec_lora/qwen3_full")
    parser.add_argument("--output", required=True)
    parser.add_argument("--column", default="gec_pred")
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    parser.add_argument("--fallback-model", default=FALLBACK_BASE_MODEL)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--limit", type=int, default=None)
    retrieval = parser.add_mutually_exclusive_group()
    retrieval.add_argument("--use-retrieval", dest="use_retrieval", action="store_true", default=None,
                           help="Force NEs in the prompt (default: read the adapter's variant marker).")
    retrieval.add_argument("--no-retrieval", dest="use_retrieval", action="store_false",
                           help="Force NEs out of the prompt (matches a wo_rac adapter).")
    args = parser.parse_args()

    predict_pairs(
        pairs_path=Path(args.pairs),
        adapter_dir=Path(args.adapter_dir),
        output_path=Path(args.output),
        column=args.column,
        base_model=args.base_model,
        fallback_model=args.fallback_model,
        use_retrieval=args.use_retrieval,
        max_new_tokens=args.max_new_tokens,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
