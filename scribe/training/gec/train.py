"""QLoRA fine-tuning for DARAG GEC, with the paper's ablation variants (§5).

Fine-tunes LoRA adapters only (paper §4.3) on the DARAG instruction template.
``variant`` selects one of the four configurations the paper compares:

* ``full``       — augmented (real + synthetic) train rows, NEs in the prompt.
* ``wo_rac``     — augmented rows, NEs removed from the prompt (no RAC).
* ``wo_aug``     — real train rows only, NEs in the prompt (no synthetic aug).
* ``only_synth`` — synthetic train rows only.

Evaluation rows are always the frozen real ``validation`` split, formatted with
the same ``use_retrieval`` as training so train/eval prompts agree.

All heavy imports are local so the module imports without torch/transformers.
"""

from __future__ import annotations

import inspect
import json
import os
import time
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
from typing import Any

from gec.config import DEFAULT_BASE_MODEL, FALLBACK_BASE_MODEL, GecRunConfig
from gec.data import eval_split_rows, read_jsonl, select_variant_rows, validate_gec_pair
from gec.env import latest_checkpoint
from gec.prompts import format_training_prompt


_BACKENDS = ("unsloth", "hf")
_LORA_TARGET_MODULES = (
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
)
_TRAINING_RUN_SCHEMA = "carepath.qlora.training-run/1"
_VERSION_PACKAGES = (
    "torch",
    "transformers",
    "trl",
    "datasets",
    "peft",
    "bitsandbytes",
    "unsloth",
    "unsloth-zoo",
)


@dataclass
class TrainArgs:
    pairs: Path
    output_dir: Path
    variant: str = "full"
    base_model: str = DEFAULT_BASE_MODEL
    fallback_model: str = FALLBACK_BASE_MODEL
    max_steps: int = 300
    per_device_train_batch_size: int = 1
    gradient_accumulation_steps: int = 8
    learning_rate: float = 2e-4
    max_seq_length: int = 768
    seed: int = 13  # paper averages over 3 seeds; set per-run for multi-seed eval
    # Resume from the newest checkpoint in output_dir if one exists, so an
    # interrupted run (Colab disconnect, closed laptop) continues instead of
    # restarting. Set False to force a fresh run.
    resume: bool = True
    config: GecRunConfig = None  # type: ignore[assignment]


def train(args: TrainArgs) -> None:
    """Train with the primary base model, retrying the fallback on CUDA OOM."""

    try:
        _train(args, model_name=args.base_model)
    except RuntimeError as exc:
        message = str(exc).lower()
        if "out of memory" not in message and "cuda" not in message:
            raise
        if latest_checkpoint(args.output_dir):
            raise RuntimeError(
                "cannot switch base model after a checkpoint exists; use a fresh output directory"
            ) from exc
        _clear_attempt_locks(args.output_dir)
        print(f"Primary model failed ({exc}); retrying fallback {args.fallback_model}")
        _train(args, model_name=args.fallback_model)


def _qlora_backend() -> str:
    backend = os.environ.get("CAREPATH_QLORA_BACKEND", "unsloth")
    if backend not in _BACKENDS:
        raise ValueError(
            "CAREPATH_QLORA_BACKEND must be exactly 'unsloth' or 'hf', "
            f"got {backend!r}"
        )
    return backend


def _unsloth_fast_language_model():
    try:
        from unsloth import FastLanguageModel  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "CAREPATH_QLORA_BACKEND=unsloth requires the Unsloth package; "
            "install it or explicitly set CAREPATH_QLORA_BACKEND=hf"
        ) from exc
    return FastLanguageModel


def _train(args: TrainArgs, model_name: str) -> None:
    backend = _qlora_backend()
    resume_ckpt = _resume_checkpoint(args.output_dir, backend, args.resume)
    FastLanguageModel = _unsloth_fast_language_model() if backend == "unsloth" else None

    import torch  # type: ignore
    from datasets import Dataset  # type: ignore
    from huggingface_hub import model_info  # type: ignore
    from transformers import (  # type: ignore
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
    )
    from trl import SFTTrainer  # type: ignore

    cfg = args.config or GecRunConfig()
    rows = read_jsonl(args.pairs)
    invalid = [
        (idx, result.errors)
        for idx, row in enumerate(rows)
        if not (result := validate_gec_pair(row)).ok
    ]
    if invalid:
        raise ValueError(f"Invalid DARAG pair rows: {invalid[:5]}")

    train_rows, use_retrieval = select_variant_rows(rows, args.variant)
    validation_rows = eval_split_rows(rows, "validation")
    if not train_rows:
        raise ValueError(f"No training rows for variant '{args.variant}'")
    if not validation_rows:
        raise ValueError("Pairs file must contain a frozen 'validation' split")
    print(
        f"variant={args.variant} use_retrieval={use_retrieval} "
        f"train_rows={len(train_rows)} val_rows={len(validation_rows)}"
    )

    revision = _locked_revision(
        args.output_dir, model_name, str(model_info(model_name).sha or "")
    )
    bf16 = bool(torch.cuda.is_bf16_supported())
    compute_dtype = torch.bfloat16 if bf16 else torch.float16
    cuda_available = bool(torch.cuda.is_available())
    device = (
        torch.cuda.get_device_name(torch.cuda.current_device())
        if cuda_available
        else "cpu"
    )
    if cuda_available:
        torch.cuda.reset_peak_memory_stats()
    run = {
        "schema": _TRAINING_RUN_SCHEMA,
        "completion_status": "running",
        "backend": backend,
        "package_versions": _package_versions(),
        "model": model_name,
        "revision": revision,
        "seed": args.seed,
        "device": device,
        "compute_dtype": "bfloat16" if bf16 else "float16",
        "resumed_checkpoint": resume_ckpt,
        "wall_runtime_seconds": None,
        "trainer_runtime_seconds": None,
        "trainer_steps_per_second": None,
        "peak_vram_gb": None,
        "error": None,
    }
    _write_training_run(args.output_dir, run)
    started_at = time.perf_counter()
    trainer_metrics: dict[str, Any] = {}

    try:
        if backend == "unsloth":
            assert FastLanguageModel is not None
            model, tokenizer = FastLanguageModel.from_pretrained(
                model_name=model_name,
                revision=revision,
                use_exact_model_name=True,
                max_seq_length=args.max_seq_length,
                dtype=compute_dtype,
                load_in_4bit=True,
                trust_remote_code=True,
            )
            model = FastLanguageModel.get_peft_model(
                model,
                r=cfg.lora_r,
                lora_alpha=cfg.lora_alpha,
                lora_dropout=cfg.lora_dropout,
                target_modules=list(_LORA_TARGET_MODULES),
                bias="none",
                use_gradient_checkpointing="unsloth",
                random_state=args.seed,
            )
            lora_config = None
        else:
            from peft import LoraConfig, prepare_model_for_kbit_training  # type: ignore

            tokenizer = AutoTokenizer.from_pretrained(
                model_name, revision=revision, trust_remote_code=True
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                revision=revision,
                quantization_config=BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=compute_dtype,
                    bnb_4bit_use_double_quant=True,
                ),
                device_map="auto",
                trust_remote_code=True,
            )
            model = prepare_model_for_kbit_training(model)
            lora_config = LoraConfig(
                r=cfg.lora_r,
                lora_alpha=cfg.lora_alpha,
                lora_dropout=cfg.lora_dropout,
                bias="none",
                task_type="CAUSAL_LM",
                target_modules=list(_LORA_TARGET_MODULES),
            )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        def to_dataset(split_rows: list[dict[str, Any]]) -> "Dataset":
            return Dataset.from_list(
                [
                    {"text": format_training_prompt(row, use_retrieval=use_retrieval)}
                    for row in split_rows
                ]
            )

        train_dataset = to_dataset(train_rows)
        eval_dataset = to_dataset(validation_rows)

        # trl/transformers churn their SFT API across versions; introspect and pass
        # only kwargs the installed classes actually accept.
        try:
            from trl import SFTConfig  # type: ignore

            config_cls = SFTConfig
        except ImportError:
            config_cls = TrainingArguments

        def supported(cls, kwargs: dict) -> dict:
            params = inspect.signature(cls.__init__).parameters
            if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()):
                return dict(kwargs)
            return {k: v for k, v in kwargs.items() if k in params}

        config_kwargs = dict(
            output_dir=str(args.output_dir),
            seed=args.seed,
            max_steps=args.max_steps,
            per_device_train_batch_size=args.per_device_train_batch_size,
            gradient_accumulation_steps=args.gradient_accumulation_steps,
            learning_rate=args.learning_rate,
            logging_steps=10,
            eval_strategy="steps",
            eval_steps=max(50, args.max_steps // 5),
            save_steps=max(50, args.max_steps // 5),
            save_total_limit=2,
            bf16=bf16,
            fp16=cuda_available and not bf16,
            optim="paged_adamw_8bit",
            report_to="none",
            max_seq_length=args.max_seq_length,
            dataset_text_field="text",
            packing=False,
        )
        training_args = config_cls(**supported(config_cls, config_kwargs))

        trainer_kwargs = dict(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            dataset_text_field="text",
            max_seq_length=args.max_seq_length,
            packing=False,
        )
        if lora_config is not None:
            trainer_kwargs["peft_config"] = lora_config
        trainer_params = inspect.signature(SFTTrainer.__init__).parameters
        if "processing_class" in trainer_params:
            trainer_kwargs["processing_class"] = tokenizer
        else:
            trainer_kwargs["tokenizer"] = tokenizer

        trainer = SFTTrainer(**supported(SFTTrainer, trainer_kwargs))
        if resume_ckpt:
            print(f"Resuming from checkpoint {resume_ckpt}")
        result = trainer.train(resume_from_checkpoint=resume_ckpt)
        trainer_metrics = getattr(result, "metrics", {}) or {}
        trainer.save_model(str(args.output_dir))
        tokenizer.save_pretrained(str(args.output_dir))
        # Record how to prompt this adapter at inference (variant -> use_retrieval).
        (args.output_dir / "darag_variant.json").write_text(
            f'{{"variant": "{args.variant}", "use_retrieval": '
            f'{str(use_retrieval).lower()}, "seed": {args.seed}}}',
            encoding="utf-8",
        )
    except BaseException as exc:
        _finalize_training_run(
            args.output_dir,
            run,
            "failed",
            started_at,
            trainer_metrics,
            torch,
            error=f"{type(exc).__name__}: {exc}",
        )
        raise
    _finalize_training_run(
        args.output_dir, run, "completed", started_at, trainer_metrics, torch
    )
    print(f"Saved {args.variant} GEC adapter to {args.output_dir}")


def _resume_checkpoint(output_dir: Path, backend: str, resume: bool) -> str | None:
    checkpoint = latest_checkpoint(output_dir) if resume else None
    if not checkpoint:
        return None
    run_file = output_dir / "training_run.json"
    checkpoint_backend = "hf"
    if run_file.exists():
        try:
            payload = json.loads(run_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"cannot verify GEC checkpoint backend from {run_file}; refuse resume"
            ) from exc
        if not isinstance(payload, dict) or payload.get("backend") not in _BACKENDS:
            raise RuntimeError(
                f"{run_file} must record backend 'unsloth' or 'hf'; refuse resume"
            )
        checkpoint_backend = payload["backend"]
    if checkpoint_backend != backend:
        raise RuntimeError(
            f"cannot resume {checkpoint_backend} GEC checkpoint with {backend} backend"
        )
    return checkpoint


def _clear_attempt_locks(output_dir: Path) -> None:
    for name in ("base_revision.json", "training_run.json"):
        (output_dir / name).unlink(missing_ok=True)


def _package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for package in _VERSION_PACKAGES:
        try:
            versions[package] = package_version(package)
        except PackageNotFoundError:
            versions[package] = None
    return versions


def _write_training_run(output_dir: Path, payload: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "training_run.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _metric(metrics: dict[str, Any], name: str) -> float | None:
    try:
        return round(float(metrics[name]), 3)
    except (KeyError, TypeError, ValueError):
        return None


def _peak_vram_gb(torch) -> float:
    if not torch.cuda.is_available():
        return 0.0
    return round(float(torch.cuda.max_memory_reserved()) / 1e9, 3)


def _finalize_training_run(
    output_dir: Path,
    run: dict[str, Any],
    completion_status: str,
    started_at: float,
    trainer_metrics: dict[str, Any],
    torch,
    *,
    error: str | None = None,
) -> None:
    run.update(
        completion_status=completion_status,
        wall_runtime_seconds=round(time.perf_counter() - started_at, 3),
        trainer_runtime_seconds=_metric(trainer_metrics, "train_runtime"),
        trainer_steps_per_second=_metric(trainer_metrics, "train_steps_per_second"),
        peak_vram_gb=_peak_vram_gb(torch),
        error=error,
    )
    _write_training_run(output_dir, run)


def _locked_revision(output_dir: Path, model_name: str, revision: str) -> str:
    lock = output_dir / "base_revision.json"
    if lock.exists():
        payload = json.loads(lock.read_text(encoding="utf-8"))
        if payload.get("model") != model_name:
            raise ValueError("GEC checkpoint base model differs from immutable revision lock")
        locked = str(payload.get("revision", ""))
        if len(locked) != 40:
            raise ValueError("invalid GEC base revision lock")
        return locked
    if len(revision) != 40:
        raise ValueError("Hugging Face did not return an exact GEC base revision")
    output_dir.mkdir(parents=True, exist_ok=True)
    lock.write_text(
        json.dumps(
            {"model": model_name, "revision": revision, "tokenizer_revision": revision},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return revision
