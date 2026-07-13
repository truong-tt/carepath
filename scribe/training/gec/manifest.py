"""Dataset-manifest validation for reproducible, consent-gated training."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = {"dataset_id", "source_description", "consent_status", "sha256"}
APPROVED_CONSENT_STATUS = "approved"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(path: Path, *, require_approved: bool = False) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"dataset manifest not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    missing = REQUIRED_FIELDS - payload.keys()
    if missing:
        raise ValueError(f"dataset manifest missing fields: {sorted(missing)}")
    if not isinstance(payload["dataset_id"], str) or not payload["dataset_id"].strip():
        raise ValueError("dataset manifest dataset_id must be non-empty")
    if not isinstance(payload["source_description"], str) or not payload["source_description"].strip():
        raise ValueError("dataset manifest source_description must be non-empty")
    if require_approved and payload["consent_status"] != APPROVED_CONSENT_STATUS:
        raise ValueError("dataset manifest requires owner-approved consent before training")
    checksum = payload["sha256"]
    if not isinstance(checksum, str) or len(checksum) != 64 or any(c not in "0123456789abcdef" for c in checksum.lower()):
        raise ValueError("dataset manifest sha256 must be a SHA-256 hex digest")
    if checksum == "0" * 64:
        raise ValueError("dataset manifest sha256 must not be a placeholder")
    return payload
