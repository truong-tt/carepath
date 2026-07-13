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
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gec.config import DEFAULT_BASE_MODEL, FALLBACK_BASE_MODEL, GecRunConfig
from gec.data import eval_split_rows, read_jsonl, select_variant_rows, validate_gec_pair
from gec.env import latest_checkpoint
from gec.prompts import format_training_prompt


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
        print(f"Primary model failed ({exc}); retrying fallback {args.fallback_model}")
        _train(args, model_name=args.fallback_model)


def _train(args: TrainArgs, model_name: str) -> None:
    import torch  # type: ignore
    from datasets import Dataset  # type: ignore
    from peft import LoraConfig, prepare_model_for_kbit_training  # type: ignore
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

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
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
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
    )

    def to_dataset(split_rows: list[dict[str, Any]]) -> "Dataset":
        return Dataset.from_list(
            [{"text": format_training_prompt(row, use_retrieval=use_retrieval)} for row in split_rows]
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
        bf16=torch.cuda.is_available(),
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
        peft_config=lora_config,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        packing=False,
    )
    trainer_params = inspect.signature(SFTTrainer.__init__).parameters
    if "processing_class" in trainer_params:
        trainer_kwargs["processing_class"] = tokenizer
    else:
        trainer_kwargs["tokenizer"] = tokenizer

    trainer = SFTTrainer(**supported(SFTTrainer, trainer_kwargs))
    resume_ckpt = latest_checkpoint(args.output_dir) if args.resume else None
    if resume_ckpt:
        print(f"Resuming from checkpoint {resume_ckpt}")
    trainer.train(resume_from_checkpoint=resume_ckpt)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))
    # Record how to prompt this adapter at inference (variant -> use_retrieval).
    (args.output_dir / "darag_variant.json").write_text(
        f'{{"variant": "{args.variant}", "use_retrieval": {str(use_retrieval).lower()}, '
        f'"seed": {args.seed}}}',
        encoding="utf-8",
    )
    print(f"Saved {args.variant} GEC adapter to {args.output_dir}")
