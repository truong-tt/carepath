"""CPU mock trainer and Colab QLoRA trainer for the shared two-task adapter."""

from __future__ import annotations

import inspect
import json
import os
import re
import time
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from soap.data import read_jsonl
from soap.prompts import training_texts

QLORA_BACKENDS = {"hf", "unsloth"}
TARGET_MODULES = [
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
]


def train(config, prepared: Path, adapters_root: Path) -> list[Path]:
    rows = read_jsonl(prepared)
    train_rows = [row for row in rows if row["split"] == "train"]
    validation_rows = [row for row in rows if row["split"] == "validation"]
    if not train_rows or not validation_rows:
        raise ValueError("SOAP training requires internal train and validation rows")
    outputs = []
    for seed in config.seeds:
        output = adapters_root / f"seed-{seed}"
        if config.trainer == "mock":
            _train_mock(config, output, seed, len(train_rows), len(validation_rows))
        else:
            _train_qlora(config, output, seed, train_rows, validation_rows)
        outputs.append(output)
    return outputs


def _train_mock(config, output: Path, seed: int, train_rows: int, validation_rows: int) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "adapter_config.json").write_text(
        json.dumps(
            {
                "base_model_name_or_path": config.base_model,
                "revision": config.base_revision,
                "peft_type": "MOCK_LORA",
                "tasks": ["extract_grounded_facts", "write_grounded_soap"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (output / "adapter_model.mock.json").write_text(
        json.dumps({"seed": seed, "train_rows": train_rows, "validation_rows": validation_rows}),
        encoding="utf-8",
    )
    (output / "training_run.json").write_text(
        json.dumps({"device": "cpu", "compute_dtype": "mock", "vram_gb": 0.0}),
        encoding="utf-8",
    )


def _train_qlora(config, output: Path, seed: int, train_rows, validation_rows) -> None:
    started = time.perf_counter()
    backend = _qlora_backend()
    checkpoint = _locked_checkpoint(output, backend)
    output.mkdir(parents=True, exist_ok=True)
    run_path = output / "training_run.json"
    run = {
        "schema": "carepath.qlora.training-run/1",
        "completion_status": "running",
        "backend": backend,
        "package_versions": _package_versions(),
        "model": config.base_model,
        "revision": config.base_revision,
        "seed": seed,
        "device": None,
        "compute_dtype": None,
        "resumed_checkpoint": checkpoint,
        "wall_runtime_seconds": None,
        "trainer_runtime_seconds": None,
        "trainer_steps_per_second": None,
        "peak_vram_gb": None,
        "vram_gb": None,
    }
    _write_training_run(run_path, run)
    torch_module = None
    device = None
    try:
        if backend == "unsloth":
            try:
                from unsloth import FastLanguageModel  # type: ignore
            except ImportError as exc:
                raise RuntimeError(
                    "CAREPATH_QLORA_BACKEND=unsloth requires the 'unsloth' package; "
                    "install it or explicitly set CAREPATH_QLORA_BACKEND=hf"
                ) from exc

        _require_transformers_451()
        import torch  # type: ignore
        from datasets import Dataset  # type: ignore
        from transformers import TrainingArguments  # type: ignore
        from trl import SFTTrainer  # type: ignore

        torch_module = torch
        if not torch.cuda.is_available():
            raise RuntimeError(
                "SOAP QLoRA training requires a CUDA GPU; use Google Colab GPU"
            )
        bf16_supported = bool(torch.cuda.is_bf16_supported())
        compute_dtype = torch.bfloat16 if bf16_supported else torch.float16
        device = torch.cuda.current_device()
        vram_gb = torch.cuda.get_device_properties(device).total_memory / 1e9
        run.update(
            device=torch.cuda.get_device_name(device),
            compute_dtype="bfloat16" if bf16_supported else "float16",
            vram_gb=round(vram_gb, 3),
        )
        _write_training_run(run_path, run)
        lora = None
        if backend == "unsloth":
            model, tokenizer = FastLanguageModel.from_pretrained(
                model_name=config.base_model,
                revision=config.base_revision,
                use_exact_model_name=True,
                max_seq_length=2048,
                dtype=compute_dtype,
                load_in_4bit=True,
                trust_remote_code=True,
            )
            model = FastLanguageModel.get_peft_model(
                model,
                r=16,
                lora_alpha=32,
                lora_dropout=0.05,
                bias="none",
                target_modules=TARGET_MODULES,
                random_state=seed,
                use_gradient_checkpointing="unsloth",
            )
        else:
            from peft import LoraConfig, prepare_model_for_kbit_training  # type: ignore
            from transformers import (  # type: ignore
                AutoModelForCausalLM,
                AutoTokenizer,
                BitsAndBytesConfig,
            )

            tokenizer = AutoTokenizer.from_pretrained(
                config.base_model,
                revision=config.base_revision,
                trust_remote_code=True,
            )
            model = AutoModelForCausalLM.from_pretrained(
                config.base_model,
                revision=config.base_revision,
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
            lora = LoraConfig(
                r=16,
                lora_alpha=32,
                lora_dropout=0.05,
                bias="none",
                task_type="CAUSAL_LM",
                target_modules=TARGET_MODULES,
            )
        tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token

        def dataset(rows: list[dict[str, Any]]):
            return Dataset.from_list(
                [
                    {"text": text}
                    for row in rows
                    for text in training_texts(row)
                ]
            )

        try:
            from trl import SFTConfig  # type: ignore

            args_type = SFTConfig
        except ImportError:
            args_type = TrainingArguments
        args = _supported(
            args_type,
            {
                "output_dir": str(output),
                "seed": seed,
                "max_steps": config.max_steps,
                "per_device_train_batch_size": 1,
                "gradient_accumulation_steps": 8,
                "learning_rate": 2e-4,
                "logging_steps": 10,
                "eval_strategy": "steps",
                "eval_steps": max(20, config.max_steps // 5),
                "save_steps": max(20, config.max_steps // 5),
                "save_total_limit": 2,
                "bf16": bf16_supported,
                "fp16": not bf16_supported,
                "optim": "paged_adamw_8bit",
                "report_to": "none",
                "max_seq_length": 2048,
                "dataset_text_field": "text",
                "packing": False,
            },
        )
        trainer_kwargs = {
            "model": model,
            "args": args,
            "train_dataset": dataset(train_rows),
            "eval_dataset": dataset(validation_rows),
            "processing_class": tokenizer,
            "dataset_text_field": "text",
            "max_seq_length": 2048,
            "packing": False,
        }
        if lora is not None:
            trainer_kwargs["peft_config"] = lora
        trainer = SFTTrainer(**_supported_kwargs(SFTTrainer, trainer_kwargs))
        torch.cuda.reset_peak_memory_stats(device)
        result = trainer.train(resume_from_checkpoint=checkpoint)
        trainer.save_model(str(output))
        tokenizer.save_pretrained(str(output))
        (output / "soap_adapter.json").write_text(
            json.dumps(
                {
                    "schema": "carepath.soap.adapter/1",
                    "seed": seed,
                    "tasks": ["extract_grounded_facts", "write_grounded_soap"],
                    "usage_scope": "research_only",
                }
            ),
            encoding="utf-8",
        )
    except BaseException as exc:
        run.update(
            completion_status="failed",
            error=f"{type(exc).__name__}: {exc}",
            wall_runtime_seconds=round(time.perf_counter() - started, 3),
            peak_vram_gb=_peak_vram_gb(torch_module, device),
        )
        _write_training_run(run_path, run)
        raise
    metrics = getattr(result, "metrics", {}) or {}
    run.update(
        completion_status="completed",
        wall_runtime_seconds=round(time.perf_counter() - started, 3),
        trainer_runtime_seconds=_float_metric(metrics, "train_runtime"),
        trainer_steps_per_second=_float_metric(metrics, "train_steps_per_second"),
        peak_vram_gb=_peak_vram_gb(torch_module, device),
    )
    _write_training_run(run_path, run)


def _qlora_backend() -> str:
    backend = os.environ.get("CAREPATH_QLORA_BACKEND", "unsloth")
    if backend not in QLORA_BACKENDS:
        raise RuntimeError("CAREPATH_QLORA_BACKEND must be exactly 'unsloth' or 'hf'")
    return backend


def _locked_checkpoint(output: Path, backend: str) -> str | None:
    checkpoint = _latest_checkpoint(output)
    if checkpoint is None:
        return None
    run_path = output / "training_run.json"
    if not run_path.exists():
        recorded_backend = "hf"
    else:
        try:
            payload = json.loads(run_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"cannot verify QLoRA backend for checkpoint {checkpoint}"
            ) from exc
        recorded_backend = payload.get("backend") if isinstance(payload, dict) else None
        if recorded_backend not in QLORA_BACKENDS:
            raise RuntimeError(
                f"checkpoint {checkpoint} has missing or invalid QLoRA backend metadata"
            )
    if recorded_backend != backend:
        raise RuntimeError(
            f"cannot resume {recorded_backend!r} checkpoint with {backend!r} backend; "
            "use the recorded backend or a fresh adapters directory"
        )
    return checkpoint


def _package_versions() -> dict[str, str | None]:
    packages = [
        "torch",
        "transformers",
        "trl",
        "datasets",
        "peft",
        "bitsandbytes",
        "unsloth",
        "unsloth-zoo",
    ]
    return {package: _package_version(package) for package in packages}


def _package_version(package: str) -> str | None:
    try:
        return version(package)
    except PackageNotFoundError:
        return None


def _float_metric(metrics: dict[str, Any], key: str) -> float | None:
    value = metrics.get(key)
    return float(value) if value is not None else None


def _peak_vram_gb(torch_module, device) -> float | None:
    if torch_module is None or device is None:
        return None
    try:
        return round(torch_module.cuda.max_memory_reserved(device) / 1e9, 3)
    except Exception:
        return None


def _write_training_run(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _require_transformers_451() -> None:
    numbers = tuple(int(value) for value in re.findall(r"\d+", version("transformers"))[:2])
    if numbers < (4, 51):
        raise RuntimeError("Qwen3-4B SOAP training requires transformers>=4.51")


def _supported(cls, kwargs: dict[str, Any]):
    return cls(**_supported_kwargs(cls, kwargs))


def _supported_kwargs(cls, kwargs: dict[str, Any]) -> dict[str, Any]:
    params = inspect.signature(cls.__init__).parameters
    if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in params.values()):
        return kwargs
    return {key: value for key, value in kwargs.items() if key in params}


def _latest_checkpoint(output: Path) -> str | None:
    checkpoints = [
        (int(path.name.removeprefix("checkpoint-")), path)
        for path in output.glob("checkpoint-*")
        if path.is_dir() and path.name.removeprefix("checkpoint-").isdigit()
    ]
    return str(max(checkpoints)[1]) if checkpoints else None
