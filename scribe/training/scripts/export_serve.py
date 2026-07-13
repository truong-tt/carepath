"""CLI: bundle a gated GEC adapter into a self-describing serve package.

The serving API must not import ``gec.*`` (research/serving stay
decoupled). So this offline script freezes everything serving needs into a
``serve_manifest.json``: base model, the variant's ``use_retrieval`` flag, and
the DARAG prompt strings. The bundle also carries the adapter, its tokenizer,
and the enriched datastore, so a server only needs the bundle directory.

    python scribe/training/scripts/export_serve.py \
      --adapter-dir artifacts/gec_lora/qwen3/full/seed-13 \
      --datastore artifacts/retrieval/term_datastore.json \
      --output artifacts/gec_serve

Set ``LLM_PROVIDER=gec_local`` and ``GEC_BUNDLE_PATH=<output>`` to serve it.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scribe" / "training"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scribe"))

from gec.cliutil import configure_stdout  # noqa: E402

configure_stdout()

from gec.config import DEFAULT_BASE_MODEL, FALLBACK_BASE_MODEL  # noqa: E402
from gec.prompts import IM_END, IM_START, SYSTEM_PROMPT  # noqa: E402


def _read_variant(adapter_dir: Path) -> dict:
    marker = adapter_dir / "darag_variant.json"
    if marker.exists():
        try:
            return json.loads(marker.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"variant": "full", "use_retrieval": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter-dir", required=True, help="trained LoRA adapter directory")
    parser.add_argument("--datastore", required=True, help="enriched term datastore JSON")
    parser.add_argument("--output", default="artifacts/gec_serve", help="bundle output dir")
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    parser.add_argument("--fallback-base-model", default=FALLBACK_BASE_MODEL)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--gate-report", default=None, help="optional WER report JSON to embed")
    args = parser.parse_args()

    adapter_dir = Path(args.adapter_dir)
    if not adapter_dir.exists():
        raise SystemExit(f"Adapter dir not found: {adapter_dir}. Train + gate one first.")
    datastore = Path(args.datastore)
    if not datastore.exists():
        raise SystemExit(f"Datastore not found: {datastore}. Build it first.")

    bundle = Path(args.output)
    bundle.mkdir(parents=True, exist_ok=True)
    # Copy the adapter (+ its tokenizer + darag_variant.json) and datastore in,
    # so the bundle is portable from Drive to a serving box on its own.
    adapter_out = bundle / "adapter"
    if adapter_out.exists():
        shutil.rmtree(adapter_out)
    shutil.copytree(adapter_dir, adapter_out)
    shutil.copy2(datastore, bundle / "term_datastore.json")

    variant = _read_variant(adapter_dir)
    manifest = {
        "schema": "carepath.gec.serve/1",
        "base_model": args.base_model,
        "fallback_base_model": args.fallback_base_model,
        "variant": variant.get("variant", "full"),
        "use_retrieval": bool(variant.get("use_retrieval", True)),
        "max_new_tokens": args.max_new_tokens,
        "adapter_dir": "adapter",
        "datastore": "term_datastore.json",
        # Frozen DARAG prompt so serving reproduces the training format with no
        # dependency on gec.prompts.
        "prompt": {
            "system": SYSTEM_PROMPT,
            "im_start": IM_START,
            "im_end": IM_END,
            "best_label": "Best hypothesis: ",
            "others_label": "Other hypotheses:",
            "entities_label": "Named entities: ",
        },
    }
    if args.gate_report and Path(args.gate_report).exists():
        manifest["gate_report"] = json.loads(Path(args.gate_report).read_text(encoding="utf-8"))

    (bundle / "serve_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote serve bundle -> {bundle}")
    print(f"  variant={manifest['variant']} use_retrieval={manifest['use_retrieval']} "
          f"base={manifest['base_model']}")
    print(f"Serve with: LLM_PROVIDER=gec_local GEC_BUNDLE_PATH={bundle}")


if __name__ == "__main__":
    main()
