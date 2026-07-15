"""Teacher/base/adapter prediction comparison for SOAP evaluation."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from soap.data import read_jsonl, write_jsonl
from soap.prompts import extract_prompt, write_prompt


def predict(config, prepared: Path, adapter_dir: Path, output: Path, teacher) -> None:
    rows = [row for row in read_jsonl(prepared) if row["split"] == "validation"]
    if config.trainer == "mock":
        predictions = [_mock_prediction(row, teacher.provenance()) for row in rows]
    else:
        predictions = _model_predictions(config, rows, adapter_dir, teacher)
    write_jsonl(output, predictions)


def _mock_prediction(row: dict[str, Any], teacher_provenance: dict[str, Any]) -> dict[str, Any]:
    reference = {"facts": copy.deepcopy(row["facts"]), "soap": copy.deepcopy(row["soap"])}
    base = copy.deepcopy(reference)
    if base["facts"]:
        base["facts"] = base["facts"][1:]
    return {
        "example_id": row["example_id"],
        "transcript": row["transcript"],
        "demographics": row.get("demographics", {}),
        "reference": reference,
        "teacher_oracle_smoke": copy.deepcopy(reference),
        "base": base,
        "adapter": copy.deepcopy(reference),
        "system_provenance": {
            "teacher_oracle_smoke": {**teacher_provenance, "comparison": "fixture_oracle"},
            "base": {"provider": "deterministic_mock_base"},
            "adapter": {"provider": "deterministic_mock_adapter"},
        },
    }


def _model_predictions(config, rows: list[dict[str, Any]], adapter_dir: Path, teacher) -> list[dict[str, Any]]:
    import torch  # type: ignore
    from peft import PeftModel  # type: ignore
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig  # type: ignore

    if not torch.cuda.is_available():
        raise RuntimeError("SOAP inference requires a CUDA GPU; use Google Colab GPU")
    compute_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    tokenizer = AutoTokenizer.from_pretrained(
        config.base_model, revision=config.base_revision, trust_remote_code=True
    )
    base = AutoModelForCausalLM.from_pretrained(
        config.base_model,
        revision=config.base_revision,
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=compute_dtype,
        ),
        device_map="auto",
        trust_remote_code=True,
    )
    results = []
    base_predictions = [_predict_one(base, tokenizer, row["transcript"]) for row in rows]
    adapter_model = PeftModel.from_pretrained(base, str(adapter_dir))
    adapter_predictions = [_predict_one(adapter_model, tokenizer, row["transcript"]) for row in rows]
    for row, base_prediction, adapter_prediction in zip(
        rows, base_predictions, adapter_predictions, strict=True
    ):
        reference = {"facts": row["facts"], "soap": row["soap"]}
        results.append(
            {
                "example_id": row["example_id"],
                "transcript": row["transcript"],
                "demographics": row.get("demographics", {}),
                "reference": reference,
                "teacher": teacher.predict(row["transcript"]),
                "base": base_prediction,
                "adapter": adapter_prediction,
                "system_provenance": {
                    "teacher": {**teacher.provenance(), "comparison": "independent_inference"},
                    "base": {"provider": "base_model", "model": config.base_model},
                    "adapter": {"provider": "soap_adapter", "path": str(adapter_dir)},
                },
            }
        )
    return results


def _predict_one(model, tokenizer, transcript: str) -> dict[str, Any]:
    facts = _generate_json(model, tokenizer, extract_prompt(transcript))
    if not isinstance(facts, list):
        facts = []
    soap = _generate_json(model, tokenizer, write_prompt(transcript, facts))
    return {"facts": facts, "soap": soap if isinstance(soap, dict) else {}}


def _generate_json(model, tokenizer, prompt: str) -> Any:
    encoded = tokenizer(prompt, return_tensors="pt").to(model.device)
    output = model.generate(
        **encoded,
        max_new_tokens=1200,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
    )
    generated = tokenizer.decode(output[0][encoded["input_ids"].shape[1] :], skip_special_tokens=True)
    generated = re.sub(r"^```(?:json)?|```$", "", generated.strip(), flags=re.IGNORECASE).strip()
    starts = [index for index in (generated.find("["), generated.find("{")) if index >= 0]
    if not starts:
        return {}
    start = min(starts)
    end = max(generated.rfind("]"), generated.rfind("}"))
    try:
        return json.loads(generated[start : end + 1])
    except json.JSONDecodeError:
        return {}
