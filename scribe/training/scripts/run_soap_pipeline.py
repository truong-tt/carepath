"""Run the governed research-only SOAP pipeline from data through bundle export."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scribe" / "training"))

from soap.config import load_config  # noqa: E402
from soap.data import load_manifest, load_terminology, prepare_examples, write_jsonl  # noqa: E402
from soap.evaluate import evaluate, export_bundle  # noqa: E402
from soap.predict import predict  # noqa: E402
from soap.teacher import build_teacher  # noqa: E402
from soap.train import train  # noqa: E402

STAGES = ("all", "data", "train", "eval", "export")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--stage", choices=STAGES, default="all")
    parser.add_argument("--confirm-paid", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config)
    manifest = load_manifest(config.manifest, require_approved=True)
    root = config.run_root
    prepared = root / "prepared.jsonl"
    rejected = root / "rejected.jsonl"
    adapters = root / "adapters"
    selected_adapter = adapters / f"seed-{config.selected_seed}"
    predictions = root / "predictions.jsonl"
    report_path = root / "evaluation.json"
    bundle = root / "bundle"
    teacher = build_teacher(config.teacher)
    wanted = STAGES[1:] if args.stage == "all" else (args.stage,)

    for stage in wanted:
        print(f"===== SOAP {stage} ({config.run_id}, profile={config.profile_name}) =====")
        if stage == "data":
            rows, rejected_rows = prepare_examples(config, manifest, teacher)
            write_jsonl(prepared, rows)
            write_jsonl(rejected, rejected_rows)
            print(f"prepared={len(rows)} rejected={len(rejected_rows)}")
        elif stage == "train":
            _require_input(prepared, "run SOAP data stage first")
            paid_confirmed = args.confirm_paid or os.environ.get("CAREPATH_CONFIRM_PAID") == "1"
            if config.trainer == "qlora" and not paid_confirmed:
                raise SystemExit(
                    "Pass --confirm-paid or set CAREPATH_CONFIRM_PAID=1 to confirm the paid Colab QLoRA run"
                )
            outputs = train(config, prepared, adapters)
            print("adapters:", ", ".join(map(str, outputs)))
        elif stage == "eval":
            _require_input(prepared, "run SOAP data stage first")
            _require_input(selected_adapter / "adapter_config.json", "run SOAP train stage first")
            predict(config, prepared, selected_adapter, predictions, teacher)
            report = evaluate(
                predictions,
                load_terminology(config.canonical_terms, config.medev_terms),
            )
            report_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
            )
            print(json.dumps(report["gate"], ensure_ascii=False))
        elif stage == "export":
            _require_input(report_path, "run SOAP eval stage first")
            export_bundle(config, selected_adapter, report_path, bundle)
            print("bundle:", bundle)


def _require_input(path: Path, message: str) -> None:
    if not path.exists():
        raise SystemExit(f"Missing {path}; {message}.")


if __name__ == "__main__":
    main()
