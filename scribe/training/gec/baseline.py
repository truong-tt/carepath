"""Build and verify the committed, CPU-only frozen GEC baseline report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gec.evaluate import stratified_report, wer_report
from gec.manifest import load_manifest, sha256_file

REPO_ROOT = Path(__file__).resolve().parents[3]


def _repo_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def build_baseline_report(config_path: Path) -> dict[str, Any]:
    """Return a deterministic report for the configured text-only fixture."""

    config = json.loads(config_path.read_text(encoding="utf-8"))
    required = {"run_id", "fixture", "fixture_manifest", "prediction_columns"}
    missing = required - config.keys()
    if missing:
        raise ValueError(f"baseline config missing fields: {sorted(missing)}")
    fixture = _repo_path(config["fixture"])
    manifest_path = _repo_path(config["fixture_manifest"])
    manifest = load_manifest(manifest_path)
    checksum = sha256_file(fixture)
    if checksum != manifest["sha256"]:
        raise ValueError("frozen evaluation fixture hash does not match its manifest")
    columns = list(config["prediction_columns"])
    rows = [
        json.loads(line)
        for line in fixture.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    stratified = stratified_report(rows, columns)
    raw = stratified["drug_name"]["raw_asr"]["frozen"]
    dosage = stratified["dosage"]["raw_asr"]["frozen"]
    diacritics = stratified["diacritics"]["raw_asr"]["frozen"]
    return {
        "schema": "carepath.gec.baseline/1",
        "run_id": config["run_id"],
        "config": {"path": _display_path(config_path), "sha256": sha256_file(config_path)},
        "fixture": {
            "path": _display_path(fixture),
            "manifest": _display_path(manifest_path),
            "dataset_id": manifest["dataset_id"],
            "sha256": checksum,
        },
        "prediction_columns": columns,
        "metrics": {
            "wer": wer_report(rows, columns),
            "stratified": stratified,
            "safety": {
                "drug_name_accuracy": raw["term_recall"],
                "dosage_accuracy": dosage["number_unit_preservation"],
                "diacritics_accuracy": diacritics["exact_match_accuracy"],
            },
        },
    }
