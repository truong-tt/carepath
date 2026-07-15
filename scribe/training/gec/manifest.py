"""Dataset-manifest validation for reproducible, consent-gated training."""

from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = {"dataset_id", "source_description", "consent_status", "sha256"}
APPROVED_CONSENT_STATUS = "approved_research_only"
APPROVED_SPLITS = ("train", "validation", "test", "hard")
HEX_40 = re.compile(r"[0-9a-f]{40}")
HEX_64 = re.compile(r"[0-9a-f]{64}")


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
    if (
        not isinstance(payload["source_description"], str)
        or not payload["source_description"].strip()
    ):
        raise ValueError("dataset manifest source_description must be non-empty")
    if require_approved and payload["consent_status"] != APPROVED_CONSENT_STATUS:
        raise ValueError(
            "dataset manifest requires owner-approved consent before training"
        )
    checksum = payload["sha256"]
    if not isinstance(checksum, str) or not HEX_64.fullmatch(checksum.lower()):
        raise ValueError("dataset manifest sha256 must be a SHA-256 hex digest")
    if checksum == "0" * 64:
        raise ValueError("dataset manifest sha256 must not be a placeholder")
    if require_approved:
        revision = payload.get("source_revision")
        if not isinstance(revision, str) or not HEX_40.fullmatch(revision.lower()):
            raise ValueError(
                "approved dataset manifest requires an exact 40-character HF revision"
            )
        approved_splits = tuple(payload.get("approved_splits", APPROVED_SPLITS))
        if not approved_splits or not all(
            isinstance(split, str) for split in approved_splits
        ):
            raise ValueError(
                "approved dataset manifest requires non-empty approved_splits"
            )
        fingerprints = payload.get("split_fingerprints")
        if not isinstance(fingerprints, dict) or any(
            not isinstance(fingerprints.get(split), str)
            or not HEX_64.fullmatch(fingerprints[split].lower())
            for split in approved_splits
        ):
            raise ValueError(
                "approved dataset manifest requires fingerprints for every frozen split"
            )
        expected_lock = source_lock_sha256(
            payload["dataset_id"], revision, fingerprints
        )
        if checksum != expected_lock:
            raise ValueError(
                "dataset manifest sha256 does not match its immutable source lock"
            )
    return payload


def source_lock_sha256(
    dataset: str,
    revision: str,
    split_fingerprints: dict[str, str],
) -> str:
    descriptor = {
        "dataset": dataset,
        "revision": revision,
        "split_fingerprints": dict(sorted(split_fingerprints.items())),
    }
    payload = json.dumps(descriptor, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def split_artifact_fingerprints(
    entries: list[dict[str, Any]],
    splits: tuple[str, ...],
) -> dict[str, str]:
    """Hash exact Hub LFS artifacts per split without downloading their contents."""

    fingerprints: dict[str, str] = {}
    for split in splits:
        pattern = re.compile(rf"^data/{re.escape(split)}-.*\.parquet$")
        artifacts = []
        for entry in entries:
            if entry.get("type") != "file" or not pattern.match(
                str(entry.get("path", ""))
            ):
                continue
            lfs = entry.get("lfs") or {}
            digest = str(lfs.get("oid", "")).lower()
            if not HEX_64.fullmatch(digest):
                raise ValueError(
                    f"Hub split artifact lacks a SHA-256 LFS oid: {entry.get('path')}"
                )
            artifacts.append(
                {
                    "path": str(entry["path"]),
                    "sha256": digest,
                    "size": int(entry["size"]),
                }
            )
        if not artifacts:
            raise ValueError(
                f"Hub revision exposes no immutable parquet artifacts for split {split!r}"
            )
        payload = json.dumps(
            sorted(artifacts, key=lambda item: item["path"]),
            sort_keys=True,
            separators=(",", ":"),
        )
        fingerprints[split] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return fingerprints


@lru_cache(maxsize=8)
def hub_split_fingerprints(
    dataset: str,
    revision: str,
    splits: tuple[str, ...],
) -> dict[str, str]:
    encoded_dataset = urllib.parse.quote(dataset, safe="/")
    url = (
        f"https://huggingface.co/api/datasets/{encoded_dataset}/tree/{revision}/data"
        "?recursive=true&expand=true"
    )
    request = urllib.request.Request(
        url, headers={"User-Agent": "CarePath-research-lock/1"}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - fixed HTTPS host
            entries = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise ValueError(
            "could not verify the pinned Hugging Face source artifacts"
        ) from exc
    if not isinstance(entries, list):
        raise ValueError("Hugging Face source tree response is invalid")
    return split_artifact_fingerprints(entries, splits)


def verify_hf_source(manifest: dict[str, Any]) -> None:
    splits = tuple(manifest.get("approved_splits", APPROVED_SPLITS))
    actual = hub_split_fingerprints(
        manifest["dataset_id"], manifest["source_revision"], splits
    )
    expected = {split: manifest["split_fingerprints"][split] for split in splits}
    if actual != expected:
        raise ValueError(
            "pinned Hugging Face split artifacts no longer match the manifest"
        )


def load_approved_hf_split(
    dataset: str,
    split: str,
    manifest: dict[str, Any],
    **kwargs: Any,
):
    """Load an exact Hub revision and reject split fingerprint drift."""

    from datasets import load_dataset  # type: ignore

    if dataset != manifest["dataset_id"]:
        raise ValueError(
            f"dataset id mismatch: manifest approves {manifest['dataset_id']!r}, got {dataset!r}"
        )
    approved_splits = tuple(manifest.get("approved_splits", APPROVED_SPLITS))
    if split not in approved_splits:
        raise ValueError(f"split must be one of {approved_splits}, got {split!r}")

    verify_hf_source(manifest)

    data = load_dataset(
        dataset,
        split=split,
        revision=manifest["source_revision"],
        **kwargs,
    )
    return data
