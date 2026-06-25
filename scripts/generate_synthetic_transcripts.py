from __future__ import annotations

import argparse
import json
import random
import sys
import uuid
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate clean DARAG synthetic transcripts with open-weight HF models."
    )
    parser.add_argument("--output", default="artifacts/synthetic/synthetic_clean.jsonl")
    parser.add_argument("--pairs", default=None, help="Optional GEC pair JSONL for few-shot examples.")
    parser.add_argument("--dataset", default="tensorxt/ViMedCSS")
    parser.add_argument("--split", default="train")
    parser.add_argument("--model", default="Qwen/Qwen3-4B-Instruct-2507")
    parser.add_argument(
        "--fallback-models",
        nargs="+",
        default=["Qwen/Qwen2.5-7B-Instruct", "google/gemma-3-4b-it"],
    )
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--examples-per-prompt", type=int, default=4)
    parser.add_argument("--limit-source", type=int, default=200)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--load-in-4bit", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "apps" / "api"))

    from hopegait.darag import (
        build_synthetic_generation_messages,
        duplicate_rejection_reason,
        parse_synthetic_transcripts,
        validate_synthetic_transcript,
    )

    args = parse_args()
    random.seed(args.seed)
    examples = load_examples(args)
    if not examples:
        raise SystemExit("No examples found for synthetic generation.")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    accepted_texts = [
        row["clean_text"] for row in read_jsonl(output_path) if row.get("clean_text")
    ]
    source_texts = [
        str(row.get("segment_text") or row.get("gold_text") or "").strip()
        for row in examples
        if str(row.get("segment_text") or row.get("gold_text") or "").strip()
    ]

    if args.dry_run:
        messages = build_synthetic_generation_messages(
            random.sample(examples, min(args.examples_per_prompt, len(examples))),
            count=min(args.batch_size, args.count),
        )
        print(json.dumps(messages, ensure_ascii=False, indent=2))
        return

    active_model, generator = load_generator(
        [args.model, *args.fallback_models],
        load_in_4bit=args.load_in_4bit,
    )
    written = 0
    with output_path.open("a", encoding="utf-8") as handle:
        while len(accepted_texts) < args.count:
            batch_target = min(args.batch_size, args.count - len(accepted_texts))
            seed_examples = random.sample(
                examples, min(args.examples_per_prompt, len(examples))
            )
            messages = build_synthetic_generation_messages(seed_examples, batch_target)
            response = generator.generate(messages)
            rows = parse_synthetic_transcripts(response)
            for row in rows:
                clean_text = str(row.get("clean_text", "")).strip()
                if not clean_text:
                    continue
                reject_reason = duplicate_rejection_reason(
                    clean_text, source_texts + accepted_texts
                )
                if reject_reason:
                    continue
                enriched = {
                    "source_kind": "darag_synthetic_clean",
                    "synthetic_id": str(uuid.uuid4()),
                    "clean_text": clean_text,
                    "topic": row.get("topic"),
                    "intended_terms": row.get("intended_terms", []),
                    "seed_example_ids": [
                        item.get("audio_id") or item.get("segment_id") for item in seed_examples
                    ],
                    "model": active_model,
                }
                validation = validate_synthetic_transcript(enriched)
                if not validation.ok:
                    continue
                handle.write(json.dumps(enriched, ensure_ascii=False) + "\n")
                handle.flush()
                accepted_texts.append(clean_text)
                written += 1
                if len(accepted_texts) >= args.count:
                    break
    print(f"Wrote {written} new synthetic transcripts to {output_path}")


class HFChatGenerator:
    def __init__(self, model_name: str, load_in_4bit: bool):
        import torch  # type: ignore
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig  # type: ignore

        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        quantization_config = None
        if load_in_4bit:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            trust_remote_code=True,
            quantization_config=quantization_config,
        )

    def generate(self, messages: list[dict[str, str]]) -> str:
        import torch  # type: ignore

        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=1200,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
            )
        generated = output[0][inputs["input_ids"].shape[-1] :]
        return self.tokenizer.decode(generated, skip_special_tokens=True)


def load_generator(
    model_names: list[str],
    load_in_4bit: bool,
) -> tuple[str, HFChatGenerator]:
    errors = []
    for model_name in model_names:
        try:
            return model_name, HFChatGenerator(model_name, load_in_4bit=load_in_4bit)
        except Exception as exc:
            errors.append(f"{model_name}: {exc}")
    raise RuntimeError("Could not load any synthetic generator model: " + " | ".join(errors))


def load_examples(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.pairs:
        rows = read_jsonl(Path(args.pairs))
        return rows[: args.limit_source]

    from datasets import load_dataset  # type: ignore

    dataset = load_dataset(args.dataset, split=args.split)
    if args.limit_source:
        dataset = dataset.select(range(min(args.limit_source, len(dataset))))
    return [dict(row) for row in dataset]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


if __name__ == "__main__":
    main()
