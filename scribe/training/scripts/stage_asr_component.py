"""Colab-only fresh-runtime smoke for an accepted PhoWhisper ASR component."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scribe" / "training"))
sys.path.insert(0, str(ROOT / "scribe"))

from gec.asr_lora import MODEL_ID, validate_asr_runtime  # noqa: E402
from gec.candidates import asr_benchmark  # noqa: E402
from gec.data import write_jsonl  # noqa: E402
from gec.manifest import load_approved_hf_split, load_manifest  # noqa: E402
from gec.metrics import split_terms  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--component", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--dataset", default="tensorxt/ViMedCSS")
    parser.add_argument("--split", default="hard", choices=["validation", "test", "hard"])
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--cache-dir", type=Path, default=Path("/content/carepath_hf_cache"))
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--confirm-paid", action="store_true")
    args = parser.parse_args()
    validate_asr_runtime(confirm_paid=args.confirm_paid, cache_dir=args.cache_dir)
    component = _validate_component(args.component)
    manifest = load_manifest(args.manifest, require_approved=True)
    if component.get("dataset_revision") != manifest["source_revision"]:
        raise SystemExit("component and approved dataset revisions differ")

    import torch  # type: ignore
    from datasets import Audio  # type: ignore
    from peft import PeftModel  # type: ignore
    from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor  # type: ignore

    revision = component["revision"]
    bf16 = bool(torch.cuda.is_bf16_supported())
    dtype = torch.bfloat16 if bf16 else torch.float16
    processor = AutoProcessor.from_pretrained(args.component)
    base = AutoModelForSpeechSeq2Seq.from_pretrained(
        MODEL_ID,
        revision=revision,
        torch_dtype=dtype,
        cache_dir=str(args.cache_dir),
    )
    model = PeftModel.from_pretrained(base, args.component).to("cuda").eval()
    data = load_approved_hf_split(
        args.dataset,
        args.split,
        manifest,
        cache_dir=str(args.cache_dir),
    )
    data = data.select(range(min(args.limit, len(data)))).cast_column(
        "audio", Audio(sampling_rate=16_000, decode=True)
    )
    rows = []
    elapsed = 0.0
    duration = 0.0
    for row in data:
        audio = row["audio"]
        inputs = processor(
            audio["array"],
            sampling_rate=audio["sampling_rate"],
            return_tensors="pt",
        ).input_features.to(device="cuda", dtype=dtype)
        started = time.perf_counter()
        with torch.no_grad():
            tokens = model.generate(inputs, language="vi", task="transcribe")
        elapsed += time.perf_counter() - started
        duration += float(row.get("duration_seconds") or 0.0)
        rows.append(
            {
                "split": args.split,
                "audio_id": str(row["segment_id"]),
                "gold_text": row["segment_text"],
                "gold_terms": split_terms(row.get("cs_terms_list")),
                "phowhisper_pred": processor.batch_decode(
                    tokens, skip_special_tokens=True
                )[0],
                "duration_seconds": row.get("duration_seconds"),
                "prediction_provider": "phowhisper_lora_fresh_runtime",
            }
        )
    write_jsonl(args.predictions, rows)
    report = asr_benchmark(rows, ("phowhisper_pred",), manifest)
    report.update(
        {
            "schema": "carepath.asr.staging-smoke/1",
            "component_schema": component["schema"],
            "component_model": component["model"],
            "component_revision": revision,
            "adapter_loaded": True,
            "split_fingerprint": manifest["split_fingerprints"][args.split],
            "real_time_factor": round(elapsed / duration, 4) if duration else None,
            "gpu": torch.cuda.get_device_name(0),
            "dtype": "bfloat16" if bf16 else "float16",
            "status": "passed",
            "real_gpu": True,
        }
    )
    if report["real_time_factor"] is None or report["real_time_factor"] > 1:
        raise SystemExit("fresh-runtime direct ASR real-time factor is missing or above 1")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _record_staging_evidence(args.component, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def _validate_component(path: Path) -> dict:
    manifest_path = path / "asr_component.json"
    try:
        component = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid ASR component manifest: {manifest_path}") from exc
    if component.get("schema") != "carepath.asr.component/1":
        raise SystemExit("unsupported ASR component schema")
    if component.get("gate_accepted") is not True:
        raise SystemExit("direct ASR component is not independently gate-accepted")
    if component.get("selected_for_serving") is not True:
        raise SystemExit("direct ASR component did not win final transcript selection")
    if component.get("model") != MODEL_ID or len(str(component.get("revision", ""))) != 40:
        raise SystemExit("direct ASR identity or exact revision is invalid")
    for relative, expected in component.get("files", {}).items():
        file_path = path / relative
        if not file_path.is_file() or hashlib.sha256(file_path.read_bytes()).hexdigest() != expected:
            raise SystemExit(f"ASR component file hash mismatch: {relative}")
    return component


def _record_staging_evidence(component_path: Path, report: dict) -> None:
    evidence = component_path / "staging_evidence.json"
    evidence.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest_path = component_path / "asr_component.json"
    component = json.loads(manifest_path.read_text(encoding="utf-8"))
    component["staging_evidence"] = evidence.name
    component.setdefault("files", {})[evidence.name] = hashlib.sha256(
        evidence.read_bytes()
    ).hexdigest()
    temporary = manifest_path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(component, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(manifest_path)


if __name__ == "__main__":
    main()
