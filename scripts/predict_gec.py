"""Run a trained QLoRA GEC adapter over GEC pairs to produce a prediction column.

This is the inference counterpart to ``scripts/train_gec_lora.py``. It loads the
frozen base model in 4-bit, attaches the trained LoRA adapter, and generates a
corrected transcript for every row, writing the result back as a new column
(default ``gec_pred``). Running it on the output of ``run_llm_rag_baseline.py``
yields a single JSONL carrying ``raw_asr`` + ``gold_text`` + ``corrected_text``
(LLM/RAG) + ``gec_pred`` (trained), which ``evaluate_gec_runs.py`` then scores
three ways and ``gate_gec.py`` accepts or rejects.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_BASE_MODEL = "Qwen/Qwen3-4B-Instruct-2507"
FALLBACK_BASE_MODEL = "Qwen/Qwen2.5-3B-Instruct"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate GEC predictions with a trained QLoRA adapter."
    )
    parser.add_argument("--pairs", required=True, help="JSONL with raw_asr (+ optional columns)")
    parser.add_argument(
        "--adapter-dir",
        default="artifacts/gec_lora/qwen3_gec",
        help="Directory saved by train_gec_lora.py (LoRA adapter + tokenizer).",
    )
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    parser.add_argument("--fallback-model", default=FALLBACK_BASE_MODEL)
    parser.add_argument("--output", required=True)
    parser.add_argument("--column", default="gec_pred")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        predict(args, base_model=args.base_model)
    except RuntimeError as exc:
        message = str(exc).lower()
        if "out of memory" not in message and "cuda" not in message:
            raise
        print(f"Primary base model failed with GPU memory/runtime error: {exc}")
        print(f"Retrying with fallback base model: {args.fallback_model}")
        predict(args, base_model=args.fallback_model)


def predict(args: argparse.Namespace, base_model: str) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "apps" / "api"))

    import torch  # type: ignore
    from peft import PeftModel  # type: ignore
    from transformers import (  # type: ignore
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
    )

    from carepath.darag import format_darag_inference_prompt

    adapter_dir = Path(args.adapter_dir)
    if not adapter_dir.exists():
        raise SystemExit(
            f"Adapter dir not found: {adapter_dir}. Train one with scripts/train_gec_lora.py first."
        )

    rows = load_rows(Path(args.pairs))
    if args.limit:
        rows = rows[: args.limit]

    # Tokenizer is saved alongside the adapter by train_gec_lora.py; fall back to
    # the base model's tokenizer if an older adapter dir lacks it.
    tokenizer_source = str(adapter_dir) if (adapter_dir / "tokenizer_config.json").exists() else base_model
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_source, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    base = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(base, str(adapter_dir))
    model.eval()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for index, row in enumerate(rows, start=1):
            prediction = generate_one(
                model, tokenizer, torch, row, max_new_tokens=args.max_new_tokens
            )
            handle.write(
                json.dumps({**row, args.column: prediction}, ensure_ascii=False) + "\n"
            )
            handle.flush()
            if index % 25 == 0:
                print(f"  predicted {index}/{len(rows)}", flush=True)
    print(f"Wrote {len(rows)} predictions ({args.column}) to {output_path}")


def generate_one(model, tokenizer, torch, row: dict[str, Any], max_new_tokens: int) -> str:
    prompt = format_darag_inference_prompt(row)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,  # greedy: deterministic, comparable across runs
            num_beams=1,
            pad_token_id=tokenizer.pad_token_id,
        )
    generated = output[0][inputs["input_ids"].shape[-1] :]
    text = tokenizer.decode(generated, skip_special_tokens=True)
    # The model is trained to stop with <|im_end|>; strip any trailing marker/turn.
    return text.split("<|im_end|>")[0].strip()


def load_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


if __name__ == "__main__":
    main()
