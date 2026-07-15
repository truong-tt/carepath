"""Shared validation for private research-bundle staging and publishing."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def validate_bundle(bundle: Path, *, allow_mock: bool = False) -> dict[str, Any]:
    manifest_path = bundle / "scribe_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid Scribe bundle manifest: {manifest_path}") from exc
    if manifest.get("schema") != "carepath.scribe.bundle/1":
        raise ValueError("unsupported Scribe bundle schema")
    if manifest.get("usage_scope") != "research_only":
        raise ValueError("Scribe bundle must be research_only")
    if manifest.get("promotion_status") != "blocked_research_only":
        raise ValueError("Scribe bundle promotion must remain blocked_research_only")
    adapters = manifest.get("adapters")
    if not isinstance(adapters, dict) or "soap" not in adapters:
        raise ValueError("Scribe bundle requires a SOAP adapter")
    if manifest.get("correction_mode") == "adapter" and "gec" not in adapters:
        raise ValueError("adapter correction mode requires a GEC adapter")
    for relative, expected in manifest.get("files", {}).items():
        path = bundle / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Scribe bundle file hash mismatch: {relative}")
    evaluation = json.loads((bundle / manifest["evaluation"]).read_text(encoding="utf-8"))
    if evaluation.get("gate", {}).get("accepted") is not True:
        raise ValueError("Scribe bundle evaluation gate is not accepted")
    for name, relative in adapters.items():
        adapter_dir = bundle / relative
        if not adapter_dir.is_dir():
            raise ValueError(f"Scribe {name} adapter directory is missing")
        if not allow_mock and (
            (adapter_dir / "adapter_model.mock.json").exists()
            or _adapter_type(adapter_dir / "adapter_config.json") == "MOCK_LORA"
            or _training_dtype(adapter_dir / "training_run.json") == "mock"
        ):
            raise ValueError(f"mock {name} adapter is not valid real-GPU acceptance evidence")
    if not allow_mock and (
        not re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("base_revision", "")))
        or manifest.get("tokenizer_revision") != manifest.get("base_revision")
    ):
        raise ValueError("real Scribe bundle requires exact matching base/tokenizer revisions")
    return manifest


def _adapter_type(path: Path) -> str:
    try:
        return str(json.loads(path.read_text(encoding="utf-8")).get("peft_type", ""))
    except (OSError, json.JSONDecodeError):
        return ""


def _training_dtype(path: Path) -> str:
    try:
        return str(json.loads(path.read_text(encoding="utf-8")).get("compute_dtype", ""))
    except (OSError, json.JSONDecodeError):
        return ""
