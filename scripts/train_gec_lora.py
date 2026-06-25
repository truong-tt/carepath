from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_MODEL = "Qwen/Qwen3-4B-Instruct-2507"
FALLBACK_MODEL = "Qwen/Qwen2.5-3B-Instruct"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a QLoRA GEC adapter on audited Gipformer ASR -> gold pairs."
    )
    parser.add_argument("--pairs", required=True, help="JSONL from create_gec_pairs.py")
    parser.add_argument("--output-dir", default="artifacts/gec_lora/qwen_gec")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--fallback-model", default=FALLBACK_MODEL)
    parser.add_argument("--max-steps", type=int, default=300)
    parser.add_argument("--per-device-train-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--max-seq-length", type=int, default=768)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        train(args, model_name=args.model)
    except RuntimeError as exc:
        if "out of memory" not in str(exc).lower() and "cuda" not in str(exc).lower():
            raise
        print(f"Primary model failed with GPU memory/runtime error: {exc}")
        print(f"Retrying with fallback model: {args.fallback_model}")
        train(args, model_name=args.fallback_model)


def train(args: argparse.Namespace, model_name: str) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "apps" / "api"))

    import torch  # type: ignore
    from datasets import Dataset  # type: ignore
    from hopegait.darag import format_darag_training_prompt, validate_gec_pair
    from peft import LoraConfig, prepare_model_for_kbit_training  # type: ignore
    from transformers import (  # type: ignore
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
    )
    from trl import SFTTrainer  # type: ignore

    rows = load_rows(Path(args.pairs))
    invalid = [
        (idx, validation.errors)
        for idx, row in enumerate(rows)
        if not (validation := validate_gec_pair(row)).ok
    ]
    if invalid:
        raise ValueError(f"Invalid DARAG pair rows: {invalid[:5]}")
    train_rows = [row for row in rows if row["split"] == "train"]
    validation_rows = [row for row in rows if row["split"] == "validation"]
    if not train_rows or not validation_rows:
        raise ValueError("Pairs file must contain frozen train and validation splits")

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
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
    )

    train_dataset = Dataset.from_list(
        [{"text": format_darag_training_prompt(row)} for row in train_rows]
    )
    eval_dataset = Dataset.from_list(
        [{"text": format_darag_training_prompt(row)} for row in validation_rows]
    )

    training_args = TrainingArguments(
        output_dir=args.output_dir,
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
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        peft_config=lora_config,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        packing=False,
    )
    trainer.train()
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"Saved GEC adapter to {args.output_dir}")


def load_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


if __name__ == "__main__":
    main()
