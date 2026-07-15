"""Train and evaluate the paid Colab-only PhoWhisper-small LoRA candidate."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scribe" / "training"))
sys.path.insert(0, str(ROOT / "scribe"))

from gec.asr_lora import NearMissNotImplementedError, run_phowhisper_lora  # noqa: E402
from gec.manifest import load_manifest  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--baseline-pairs", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--max-steps", required=True, type=int)
    parser.add_argument("--train-limit", type=int)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--cache-dir", type=Path, default=Path("/content/carepath_hf_cache"))
    parser.add_argument("--confirm-paid", action="store_true")
    parser.add_argument(
        "--require-near-miss",
        action="store_true",
        help="reproduction-only fail-closed request after the plain-LoRA gate",
    )
    args = parser.parse_args()
    manifest = load_manifest(args.manifest, require_approved=True)
    try:
        run_phowhisper_lora(
            dataset=args.dataset,
            manifest=manifest,
            manifest_path=args.manifest,
            baseline_pairs=args.baseline_pairs,
            output_dir=args.output_dir,
            predictions_path=args.predictions,
            report_path=args.report,
            max_steps=args.max_steps,
            train_limit=args.train_limit,
            seed=args.seed,
            cache_dir=args.cache_dir,
            confirm_paid=args.confirm_paid,
            require_near_miss=args.require_near_miss,
        )
    except NearMissNotImplementedError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
