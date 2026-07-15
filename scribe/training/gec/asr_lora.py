"""Colab-only PhoWhisper-small LoRA training and frozen-split evaluation."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gec.candidates import (
    asr_benchmark,
    direct_asr_safety_report,
    plain_asr_lora_gate,
    select_transcript_candidate,
)
from gec.data import read_jsonl, write_jsonl
from gec.env import latest_checkpoint
from gec.manifest import load_approved_hf_split, load_manifest, sha256_file
from gec.metrics import split_terms

MODEL_ID = "vinai/PhoWhisper-small"
EVAL_SPLITS = ("validation", "test", "hard")


class NearMissNotImplementedError(RuntimeError):
    """Raised only when an accepted plain adapter makes near-miss mandatory."""


def near_miss_status(*, requested: bool, plain_gate_accepted: bool) -> dict[str, Any]:
    """Return an explicit, fail-closed status for the unimplemented paper stage."""

    contract = {
        "genuine_beam_n_best": 10,
        "poi_local_replacements": True,
        "filters": {
            "acoustic_teacher_forced_score_margin": 4.0,
            "minimum_normalized_text_distance": 0.4,
            "maximum_phonetic_distance": 0.6,
        },
        "objective": {
            "poi_weighted_cross_entropy_alpha": 2.0,
            "info_nce_max_negatives": 5,
            "info_nce_beta": 1.0,
            "ranking_lambda": 0.1,
        },
        "offline_pool_cache_required": True,
        "inference": "standard_asr_only",
        "optional_llm_expansion": {
            "enabled": False,
            "provenance": "none",
        },
    }
    if not requested:
        return {
            "status": "not_requested",
            "blocking": False,
            "executed": False,
            "contract": contract,
        }
    if not plain_gate_accepted:
        return {
            "status": "blocked_plain_lora_gate",
            "blocking": True,
            "executed": False,
            "reason": "plain LoRA did not clear the required 5% WER and term-error gate",
            "contract": contract,
        }
    return {
        "status": "not_implemented",
        "blocking": True,
        "executed": False,
        "reason": (
            "Repository has no validated Whisper teacher-forced sequence-ranking trainer; "
            "approximating this objective would falsely claim near-miss paper replication"
        ),
        "contract": contract,
    }


def validate_asr_runtime(
    *,
    confirm_paid: bool,
    cache_dir: Path,
    in_colab: bool | None = None,
    cuda_available: bool | None = None,
) -> None:
    """Fail before downloads unless this is an explicitly paid Colab GPU run."""

    if not confirm_paid:
        raise ValueError("PhoWhisper LoRA requires explicit paid-profile confirmation")
    if in_colab is None:
        in_colab = (
            bool(os.environ.get("COLAB_RELEASE_TAG")) or Path("/content").exists()
        )
    if not in_colab:
        raise ValueError(
            "PhoWhisper LoRA is Colab-only; CPU/local execution is blocked"
        )
    if cuda_available is None:
        import torch  # type: ignore

        cuda_available = torch.cuda.is_available()
    if not cuda_available:
        raise ValueError("PhoWhisper LoRA requires a Colab CUDA runtime")
    resolved = cache_dir.expanduser().resolve()
    if str(resolved).startswith("/content/drive/"):
        raise ValueError(
            "public research audio/cache must stay ephemeral, not on Drive"
        )


@dataclass
class WhisperDataCollator:
    processor: Any

    def __call__(self, features: list[dict[str, Any]]) -> dict[str, Any]:
        inputs = [{"input_features": item["input_features"]} for item in features]
        batch = self.processor.feature_extractor.pad(inputs, return_tensors="pt")
        labels = self.processor.tokenizer.pad(
            [{"input_ids": item["labels"]} for item in features],
            return_tensors="pt",
        )
        label_ids = labels["input_ids"].masked_fill(labels.attention_mask.ne(1), -100)
        if (label_ids[:, 0] == self.processor.tokenizer.bos_token_id).all().item():
            label_ids = label_ids[:, 1:]
        batch["labels"] = label_ids
        return batch


def run_phowhisper_lora(
    *,
    dataset: str,
    manifest: dict[str, Any],
    manifest_path: Path,
    baseline_pairs: Path,
    output_dir: Path,
    predictions_path: Path,
    report_path: Path,
    max_steps: int,
    train_limit: int | None,
    seed: int,
    cache_dir: Path,
    confirm_paid: bool,
    require_near_miss: bool = False,
) -> dict[str, Any]:
    """Train on ViMedCSS train only; predict untouched validation/test/hard."""

    validate_asr_runtime(confirm_paid=confirm_paid, cache_dir=cache_dir)

    import torch  # type: ignore
    from huggingface_hub import model_info  # type: ignore
    from peft import LoraConfig, get_peft_model  # type: ignore
    from transformers import (  # type: ignore
        AutoModelForSpeechSeq2Seq,
        AutoProcessor,
        Seq2SeqTrainer,
        Seq2SeqTrainingArguments,
        set_seed,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    set_seed(seed)
    torch.cuda.reset_peak_memory_stats()
    bf16 = bool(torch.cuda.is_bf16_supported())
    dtype = torch.bfloat16 if bf16 else torch.float16
    model_revision = _model_revision(output_dir, str(model_info(MODEL_ID).sha or ""))

    processor = AutoProcessor.from_pretrained(
        MODEL_ID,
        revision=model_revision,
        language="vi",
        task="transcribe",
        cache_dir=str(cache_dir),
    )
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        MODEL_ID,
        revision=model_revision,
        torch_dtype=dtype,
        cache_dir=str(cache_dir),
    )
    model.config.use_cache = False
    model.generation_config.language = "vi"
    model.generation_config.task = "transcribe"
    model = get_peft_model(
        model,
        LoraConfig(
            r=16,
            lora_alpha=32,
            target_modules=["q_proj", "v_proj"],
            lora_dropout=0.05,
            bias="none",
        ),
    )

    raw_datasets: dict[str, Any] = {}
    metadata: dict[str, list[dict[str, Any]]] = {}
    for split in ("train", *EVAL_SPLITS):
        raw = load_approved_hf_split(
            dataset,
            split,
            manifest,
            cache_dir=str(cache_dir),
        )
        if split == "train" and train_limit:
            raw = raw.select(range(min(train_limit, len(raw))))
        metadata[split] = _metadata(raw, split)
        raw_datasets[split] = _prepare_dataset(raw, processor, cache_dir, split)

    save_steps = max(10, min(50, max_steps))
    args = Seq2SeqTrainingArguments(
        output_dir=str(output_dir),
        max_steps=max_steps,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        gradient_accumulation_steps=2,
        learning_rate=1e-3,
        warmup_steps=min(20, max_steps // 10),
        eval_strategy="steps",
        eval_steps=save_steps,
        save_strategy="steps",
        save_steps=save_steps,
        save_total_limit=2,
        logging_steps=5,
        predict_with_generate=True,
        generation_max_length=225,
        remove_unused_columns=False,
        label_names=["labels"],
        fp16=not bf16,
        bf16=bf16,
        gradient_checkpointing=True,
        report_to=[],
        seed=seed,
        data_seed=seed,
    )
    trainer = Seq2SeqTrainer(
        model=model,
        args=args,
        train_dataset=raw_datasets["train"],
        eval_dataset=raw_datasets["validation"],
        data_collator=WhisperDataCollator(processor),
        processing_class=processor,
    )

    baseline_predictions: dict[str, list[str]] = {}
    for split in EVAL_SPLITS:
        baseline_predictions[split], _ = _predict(
            trainer, raw_datasets[split], processor, split
        )

    checkpoint = latest_checkpoint(output_dir)
    trainer.train(resume_from_checkpoint=str(checkpoint) if checkpoint else None)
    trainer.save_model(str(output_dir))
    processor.save_pretrained(str(output_dir))

    candidate_predictions: dict[str, list[str]] = {}
    split_rtf: dict[str, float | None] = {}
    for split in EVAL_SPLITS:
        predictions, elapsed = _predict(trainer, raw_datasets[split], processor, split)
        candidate_predictions[split] = predictions
        duration = sum(
            float(row.get("duration_seconds") or 0.0) for row in metadata[split]
        )
        split_rtf[split] = round(elapsed / duration, 4) if duration > 0 else None

    rows = _prediction_rows(
        metadata,
        baseline_predictions,
        candidate_predictions,
        baseline_pairs,
    )
    write_jsonl(predictions_path, rows)
    benchmark = asr_benchmark(
        rows,
        ("raw_asr", "phowhisper_base", "phowhisper_pred"),
        manifest,
    )
    gate = plain_asr_lora_gate(benchmark["metrics"], baseline="phowhisper_base")
    near_miss = near_miss_status(
        requested=require_near_miss,
        plain_gate_accepted=gate["accepted"],
    )
    direct_safety = direct_asr_safety_report(
        rows, ("raw_asr", "phowhisper_base", "phowhisper_pred")
    )
    total_duration = sum(float(row.get("duration_seconds") or 0.0) for row in rows)
    weighted_rtf = (
        round(
            sum(
                (split_rtf[split] or 0.0)
                * sum(
                    float(row.get("duration_seconds") or 0.0) for row in metadata[split]
                )
                for split in EVAL_SPLITS
            )
            / total_duration,
            4,
        )
        if total_duration > 0
        else None
    )
    final_selection = select_transcript_candidate(
        benchmark["metrics"],
        {},
        candidates=("raw_asr", "phowhisper_pred"),
        latency_seconds={"phowhisper_pred": weighted_rtf},
        direct_safety_report=direct_safety,
    )
    candidate_gate = final_selection["decisions"]["phowhisper_pred"]
    candidate_gate["evidence_source"] = "untouched ViMedCSS hard split"
    candidate_gate["safety_metrics"] = [
        "annotated medical-term recall",
        "number/unit preservation",
        "real-time factor",
    ]
    vietmed_manifest_path = Path("scribe/training/manifests/vietmed-test-v1.json")
    vietmed_manifest = load_manifest(vietmed_manifest_path, require_approved=True)
    report = {
        **benchmark,
        "schema": "carepath.phowhisper-lora-report/1",
        "dataset_id": dataset,
        "dataset_revision": manifest["source_revision"],
        "split_fingerprints": manifest["split_fingerprints"],
        "dataset_manifest_sha256": sha256_file(manifest_path),
        "model_id": MODEL_ID,
        "model_revision": model_revision,
        "tokenizer_revision": model_revision,
        "seed": seed,
        "max_steps": max_steps,
        "train_rows": len(raw_datasets["train"]),
        "train_split_only": True,
        "evaluation_splits_untouched": list(EVAL_SPLITS),
        "near_miss_gate": gate,
        "near_miss": near_miss,
        "near_miss_executed": near_miss["executed"],
        "candidate_gate": candidate_gate,
        "direct_safety": direct_safety,
        "runtime": {
            "gpu": torch.cuda.get_device_name(0),
            "dtype": "bfloat16" if bf16 else "float16",
            "peak_vram_gib": round(torch.cuda.max_memory_allocated() / (1024**3), 3),
            "real_time_factor": weighted_rtf,
            "real_time_factor_by_split": split_rtf,
        },
        "usage_scope": "research_only",
        "promotion_status": "blocked_research_only",
        "out_of_domain": {
            "VietMed-test": {
                "status": "approved_not_run",
                "manifest": str(vietmed_manifest_path),
                "source_revision": vietmed_manifest["source_revision"],
                "split_fingerprint": vietmed_manifest["split_fingerprints"]["test"],
                "training_allowed": False,
                "retrieval_allowed": False,
                "reason": "VietMed adapter evaluation remains Colab evidence; it is never training data.",
            }
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    _write_component_manifest(output_dir, report, report_path, predictions_path)
    if near_miss["status"] == "not_implemented":
        raise NearMissNotImplementedError(
            "near-miss reproduction is fail-closed: plain LoRA passed, but the validated "
            "beam/POI/contrastive training stage is not implemented; see the saved report"
        )
    return report


def _prepare_dataset(raw: Any, processor: Any, cache_dir: Path, split: str):
    from datasets import Audio  # type: ignore

    decoded = raw.cast_column("audio", Audio(sampling_rate=16_000, decode=True))

    def prepare(row: dict[str, Any]) -> dict[str, Any]:
        audio = row["audio"]
        return {
            "input_features": processor.feature_extractor(
                audio["array"], sampling_rate=audio["sampling_rate"]
            ).input_features[0],
            "labels": processor.tokenizer(row["segment_text"]).input_ids,
        }

    return decoded.map(
        prepare,
        remove_columns=decoded.column_names,
        cache_file_name=str(
            cache_dir
            / f"phowhisper_{split}_{str(raw._fingerprint)[:12]}_features.arrow"
        ),
        desc=f"PhoWhisper features: {split}",
    )


def _metadata(raw: Any, split: str) -> list[dict[str, Any]]:
    columns = [
        name
        for name in ("segment_id", "segment_text", "cs_terms_list", "duration_seconds")
        if name in raw.column_names
    ]
    return [
        {
            "split": split,
            "audio_id": str(row["segment_id"]),
            "gold_text": str(row["segment_text"]),
            "gold_terms": split_terms(row.get("cs_terms_list")),
            "duration_seconds": row.get("duration_seconds"),
        }
        for row in raw.select_columns(columns)
    ]


def _predict(
    trainer: Any, dataset: Any, processor: Any, split: str
) -> tuple[list[str], float]:
    started = time.perf_counter()
    output = trainer.predict(dataset, metric_key_prefix=f"predict_{split}")
    elapsed = time.perf_counter() - started
    token_ids = (
        output.predictions[0]
        if isinstance(output.predictions, tuple)
        else output.predictions
    )
    return processor.batch_decode(token_ids, skip_special_tokens=True), elapsed


def _prediction_rows(
    metadata: dict[str, list[dict[str, Any]]],
    baseline_predictions: dict[str, list[str]],
    candidate_predictions: dict[str, list[str]],
    baseline_pairs: Path,
) -> list[dict[str, Any]]:
    gipformer = {
        (str(row.get("split")), str(row.get("audio_id"))): row
        for row in read_jsonl(baseline_pairs)
    }
    rows: list[dict[str, Any]] = []
    for split in EVAL_SPLITS:
        for index, meta in enumerate(metadata[split]):
            key = (split, meta["audio_id"])
            if key not in gipformer:
                raise ValueError(f"missing frozen Gipformer baseline row: {key}")
            rows.append(
                {
                    **meta,
                    "raw_asr": gipformer[key]["raw_asr"],
                    "phowhisper_base": baseline_predictions[split][index],
                    "phowhisper_pred": candidate_predictions[split][index],
                    "source_kind": "vimedcss_real",
                    "prediction_provider": "phowhisper_lora",
                }
            )
    return rows


def _model_revision(output_dir: Path, current_revision: str) -> str:
    if len(current_revision) != 40:
        raise ValueError("Hugging Face did not return an exact model commit revision")
    lock = output_dir / "revision_lock.json"
    if lock.exists():
        locked = json.loads(lock.read_text(encoding="utf-8"))
        revision = str(locked.get("model_revision", ""))
        if len(revision) != 40:
            raise ValueError(
                "invalid PhoWhisper revision lock; refuse incompatible resume"
            )
        component = output_dir / "asr_component.json"
        if component.exists():
            previous = json.loads(component.read_text(encoding="utf-8"))
            if previous.get("revision") != revision:
                raise ValueError(
                    "component/model revision lock mismatch; refuse resume"
                )
        return revision
    lock.write_text(
        json.dumps(
            {
                "model": MODEL_ID,
                "model_revision": current_revision,
                "tokenizer_revision": current_revision,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return current_revision


def _write_component_manifest(
    output_dir: Path,
    report: dict[str, Any],
    report_path: Path,
    predictions_path: Path,
) -> None:
    metrics_copy = output_dir / "evaluation_metrics.json"
    metrics_copy.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    files = {
        str(path.relative_to(output_dir)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output_dir.rglob("*"))
        if path.is_file() and path.name != "asr_component.json"
    }
    payload = {
        "schema": "carepath.asr.component/1",
        "component": "phowhisper_small_lora",
        "model": report["model_id"],
        "revision": report["model_revision"],
        "tokenizer_revision": report["tokenizer_revision"],
        "dataset_id": report["dataset_id"],
        "dataset_revision": report["dataset_revision"],
        "dataset_manifest_sha256": report["dataset_manifest_sha256"],
        "metrics_sha256": sha256_file(metrics_copy),
        "external_report_sha256": sha256_file(report_path),
        "predictions_sha256": sha256_file(predictions_path),
        "files": files,
        "adapter": next(
            (
                name
                for name in files
                if name in {"adapter_model.safetensors", "adapter_model.bin"}
            ),
            None,
        ),
        "tokenizer": "tokenizer_config.json"
        if "tokenizer_config.json" in files
        else None,
        "metrics": "evaluation_metrics.json",
        "staging_evidence": None,
        "plain_lora_gate_accepted": report["near_miss_gate"]["accepted"],
        "gate_accepted": report["candidate_gate"]["eligible"],
        "selected_for_serving": False,
        "usage_scope": "research_only",
        "promotion_status": "blocked_research_only",
    }
    (output_dir / "asr_component.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
