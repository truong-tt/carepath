"""Run a trained QLoRA GEC adapter over pairs to produce a prediction column.

Inference counterpart to ``train``. Loads the frozen base model in 4-bit, attaches
the LoRA adapter, and greedily decodes a corrected transcript for every row. The
prompt's ``use_retrieval`` is read from the adapter's ``darag_variant.json`` (so a
``wo_rac`` adapter is prompted without NEs, matching how it was trained) unless
overridden. Writing the result as a new column lets ``evaluate`` score raw vs
LLM/RAG vs trained side by side.
"""

from __future__ import annotations

import json
from pathlib import Path

from gec.config import DEFAULT_BASE_MODEL, FALLBACK_BASE_MODEL
from gec.data import read_jsonl, write_jsonl
from gec.prompts import format_inference_prompt, strip_generated


def predict_pairs(
    pairs_path: Path,
    adapter_dir: Path,
    output_path: Path,
    column: str = "gec_pred",
    base_model: str = DEFAULT_BASE_MODEL,
    fallback_model: str = FALLBACK_BASE_MODEL,
    use_retrieval: bool | None = None,
    max_new_tokens: int = 256,
    limit: int | None = None,
) -> None:
    try:
        _predict(pairs_path, adapter_dir, output_path, column, base_model,
                 use_retrieval, max_new_tokens, limit)
    except RuntimeError as exc:
        message = str(exc).lower()
        if "out of memory" not in message and "cuda" not in message:
            raise
        print(f"Primary base model failed ({exc}); retrying fallback {fallback_model}")
        _predict(pairs_path, adapter_dir, output_path, column, fallback_model,
                 use_retrieval, max_new_tokens, limit)


def _predict(
    pairs_path: Path,
    adapter_dir: Path,
    output_path: Path,
    column: str,
    base_model: str,
    use_retrieval: bool | None,
    max_new_tokens: int,
    limit: int | None,
) -> None:
    import torch  # type: ignore
    from peft import PeftModel  # type: ignore
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig  # type: ignore

    if not adapter_dir.exists():
        raise SystemExit(f"Adapter dir not found: {adapter_dir}. Train one first.")

    if use_retrieval is None:
        use_retrieval = _read_use_retrieval(adapter_dir)

    rows = read_jsonl(pairs_path)
    if limit:
        rows = rows[:limit]

    tokenizer_source = (
        str(adapter_dir)
        if (adapter_dir / "tokenizer_config.json").exists()
        else base_model
    )
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

    predictions = []
    for index, row in enumerate(rows, start=1):
        prompt = format_inference_prompt(row, use_retrieval=use_retrieval)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                num_beams=1,
                pad_token_id=tokenizer.pad_token_id,
            )
        generated = output[0][inputs["input_ids"].shape[-1] :]
        text = strip_generated(tokenizer.decode(generated, skip_special_tokens=True))
        predictions.append({**row, column: text})
        if index % 25 == 0:
            print(f"  predicted {index}/{len(rows)}", flush=True)

    write_jsonl(output_path, predictions)
    print(f"Wrote {len(predictions)} predictions ({column}, use_retrieval={use_retrieval}) "
          f"to {output_path}")


def _read_use_retrieval(adapter_dir: Path) -> bool:
    marker = adapter_dir / "darag_variant.json"
    if not marker.exists():
        return True
    try:
        return bool(json.loads(marker.read_text(encoding="utf-8")).get("use_retrieval", True))
    except (json.JSONDecodeError, OSError):
        return True
