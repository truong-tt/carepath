"""Synthetic in-domain transcript generation (paper §4.1 Step 1).

Few-shot prompts an open-weight instruction model with real in-domain examples
and collects new, diverse transcripts, rejecting near-duplicates with the n-gram
guard so the model cannot simply echo the training set (paper App. C). The HF
generator imports torch/transformers lazily so ``build_generation_messages`` and
the accept/reject bookkeeping stay importable for tests.
"""

from __future__ import annotations

import random
import uuid
from pathlib import Path
from typing import Any, Callable

from carepath.gec.config import DEFAULT_SYNTH_MODEL, FALLBACK_SYNTH_MODELS
from carepath.gec.data import read_jsonl, validate_synthetic_transcript
from carepath.gec.leakage import duplicate_rejection_reason
from carepath.gec.prompts import (
    build_synthetic_generation_messages,
    parse_synthetic_transcripts,
)


def generate_synthetic_transcripts(
    examples: list[dict[str, Any]],
    count: int,
    generate_fn: Callable[[list[dict[str, str]]], str],
    existing_texts: list[str] | None = None,
    examples_per_prompt: int = 4,
    batch_size: int = 5,
    model_label: str = DEFAULT_SYNTH_MODEL,
    seed: int = 13,
    max_iterations: int | None = None,
) -> list[dict[str, Any]]:
    """Drive the few-shot generation loop until ``count`` transcripts are accepted.

    ``generate_fn`` maps chat messages -> raw model text; injecting it keeps this
    loop unit-testable with a stub and lets the CLI plug in the real HF generator.
    """

    rng = random.Random(seed)
    source_texts = [
        str(ex.get("segment_text") or ex.get("gold_text") or "").strip()
        for ex in examples
        if str(ex.get("segment_text") or ex.get("gold_text") or "").strip()
    ]
    accepted_texts = list(existing_texts or [])
    accepted_rows: list[dict[str, Any]] = []
    cap = max_iterations if max_iterations is not None else max(count * 5, 20)

    iteration = 0
    while len(accepted_rows) < count and iteration < cap:
        iteration += 1
        batch_target = min(batch_size, count - len(accepted_rows))
        seed_examples = rng.sample(examples, min(examples_per_prompt, len(examples)))
        messages = build_synthetic_generation_messages(seed_examples, batch_target)
        rows = parse_synthetic_transcripts(generate_fn(messages))
        for row in rows:
            clean_text = str(row.get("clean_text", "")).strip()
            if not clean_text:
                continue
            if duplicate_rejection_reason(clean_text, source_texts + accepted_texts):
                continue
            enriched = {
                "source_kind": "darag_synthetic_clean",
                "synthetic_id": str(uuid.uuid4()),
                "clean_text": clean_text,
                "topic": row.get("topic"),
                "intended_terms": row.get("intended_terms", []),
                "seed_example_ids": [
                    ex.get("audio_id") or ex.get("segment_id") for ex in seed_examples
                ],
                "model": model_label,
            }
            if not validate_synthetic_transcript(enriched).ok:
                continue
            accepted_rows.append(enriched)
            accepted_texts.append(clean_text)
            if len(accepted_rows) >= count:
                break
    return accepted_rows


def load_examples(
    pairs_path: Path | None,
    dataset: str | None,
    split: str,
    limit: int,
) -> list[dict[str, Any]]:
    if pairs_path:
        return read_jsonl(pairs_path)[:limit]
    if not dataset:
        return []
    from datasets import load_dataset  # type: ignore

    data = load_dataset(dataset, split=split)
    if limit:
        data = data.select(range(min(limit, len(data))))
    return [dict(row) for row in data]


class HFChatGenerator:
    """Lazy HF chat generator with model fallback (used by the CLI)."""

    def __init__(self, model_name: str, load_in_4bit: bool = False):
        import torch  # type: ignore
        from transformers import (  # type: ignore
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
        )

        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        quant = None
        if load_in_4bit:
            quant = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            trust_remote_code=True,
            quantization_config=quant,
        )

    def __call__(self, messages: list[dict[str, str]]) -> str:
        import torch  # type: ignore

        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            output = self.model.generate(
                **inputs, max_new_tokens=1200, do_sample=True, temperature=0.7, top_p=0.9
            )
        generated = output[0][inputs["input_ids"].shape[-1] :]
        return self.tokenizer.decode(generated, skip_special_tokens=True)


def load_generator(
    model_names: list[str] | None = None,
    load_in_4bit: bool = False,
) -> tuple[str, HFChatGenerator]:
    candidates = model_names or [DEFAULT_SYNTH_MODEL, *FALLBACK_SYNTH_MODELS]
    errors = []
    for name in candidates:
        try:
            return name, HFChatGenerator(name, load_in_4bit=load_in_4bit)
        except Exception as exc:  # pragma: no cover - depends on local GPU/model
            errors.append(f"{name}: {exc}")
    raise RuntimeError("Could not load any synthetic generator model: " + " | ".join(errors))
