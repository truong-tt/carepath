"""CLI: QLoRA fine-tune a DARAG GEC adapter, optionally per ablation variant (paper §5).

    # full DARAG:
    python scribe/training/scripts/train.py \
      --pairs artifacts/gec_pairs/darag_augmented.jsonl \
      --output-dir artifacts/gec_lora/qwen3_full --variant full --max-steps 300

    # train every ablation into <output-dir>/<variant>:
    python scribe/training/scripts/train.py --pairs ... --output-dir artifacts/gec_lora/qwen3 --all-variants
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scribe" / "training"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scribe"))

from gec.cliutil import configure_stdout  # noqa: E402

configure_stdout()

from gec.config import DEFAULT_BASE_MODEL, FALLBACK_BASE_MODEL, VARIANTS  # noqa: E402
from gec.train import TrainArgs, train  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", required=True, help="Augmented GEC pairs JSONL.")
    parser.add_argument("--output-dir", default="artifacts/gec_lora/qwen3_gec")
    parser.add_argument("--variant", default="full", choices=list(VARIANTS))
    parser.add_argument("--all-variants", action="store_true",
                        help="Train full + every ablation into <output-dir>/<variant>.")
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    parser.add_argument("--fallback-model", default=FALLBACK_BASE_MODEL)
    parser.add_argument("--max-steps", type=int, default=300)
    parser.add_argument("--per-device-train-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--max-seq-length", type=int, default=768)
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[13],
        help="One or more seeds (paper averages 3). >1 writes <dir>/<variant>/seed-<s>.",
    )
    parser.add_argument(
        "--no-resume",
        dest="resume",
        action="store_false",
        help="Ignore any existing checkpoint and train from scratch.",
    )
    parser.set_defaults(resume=True)
    args = parser.parse_args()

    variants = list(VARIANTS) if args.all_variants else [args.variant]
    multi_seed = len(args.seeds) > 1
    for variant in variants:
        variant_dir = Path(args.output_dir) / variant if args.all_variants else Path(args.output_dir)
        for seed in args.seeds:
            # Single seed keeps the flat layout the predict/gate steps expect;
            # multi-seed nests each run so per-seed metrics can be averaged.
            output_dir = variant_dir / f"seed-{seed}" if multi_seed else variant_dir
            print(f"\n=== Training variant '{variant}' seed={seed} -> {output_dir} ===")
            train(
                TrainArgs(
                    pairs=Path(args.pairs),
                    output_dir=output_dir,
                    variant=variant,
                    base_model=args.base_model,
                    fallback_model=args.fallback_model,
                    max_steps=args.max_steps,
                    per_device_train_batch_size=args.per_device_train_batch_size,
                    gradient_accumulation_steps=args.gradient_accumulation_steps,
                    learning_rate=args.learning_rate,
                    max_seq_length=args.max_seq_length,
                    seed=seed,
                    resume=args.resume,
                )
            )


if __name__ == "__main__":
    main()
