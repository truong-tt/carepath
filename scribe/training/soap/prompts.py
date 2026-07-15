"""Two grounded tasks trained into one SOAP LoRA adapter."""

from __future__ import annotations

import json
from typing import Any

from soap.schemas import stable_json

SYSTEM = (
    "Bạn hỗ trợ ghi chép bệnh án. Chỉ dùng dữ kiện có trong hội thoại và luôn trả về JSON. "
    "Không tự thêm chẩn đoán, thuốc, liều, số liệu hoặc phủ định."
)


def extract_prompt(transcript: str, answer: list[dict[str, Any]] | None = None) -> str:
    request = {
        "task": "extract_grounded_facts",
        "transcript": transcript,
        "requirements": "Each fact cites an exact source_span and records negation and uncertainty.",
    }
    return _chat(request, answer)


def write_prompt(
    transcript: str,
    facts: list[dict[str, Any]],
    answer: dict[str, Any] | None = None,
) -> str:
    request = {
        "task": "write_grounded_soap",
        "transcript": transcript,
        "supported_facts": facts,
        "requirements": (
            "Use semicolon-separated exact supported fact values only; fixed missing-section text is allowed; "
            "preserve numbers and negation; review_required=true."
        ),
    }
    return _chat(request, answer)


def training_texts(row: dict[str, Any]) -> list[str]:
    return [
        extract_prompt(row["transcript"], row["facts"]),
        write_prompt(row["transcript"], row["facts"], row["soap"]),
    ]


def _chat(request: dict[str, Any], answer: Any | None) -> str:
    text = f"<|im_start|>system\n{SYSTEM}<|im_end|>\n<|im_start|>user\n{stable_json(request)}<|im_end|>"
    if answer is not None:
        text += f"\n<|im_start|>assistant\n{json.dumps(answer, ensure_ascii=False)}<|im_end|>"
    else:
        text += "\n<|im_start|>assistant\n"
    return text
