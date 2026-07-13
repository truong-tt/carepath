"""Versioned JSON configuration for deterministic DARAG pipeline runs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from gec.profiles import RunProfile


@dataclass(frozen=True)
class PipelineConfig:
    run_id: str
    dataset: str
    manifest: Path
    frozen_eval_fixture: Path
    frozen_eval_manifest: Path
    artifact_root: Path
    suffix: str
    profile: RunProfile


def load_pipeline_config(path: Path) -> PipelineConfig:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "run_id",
        "dataset",
        "manifest",
        "frozen_eval_fixture",
        "frozen_eval_manifest",
        "artifact_root",
        "suffix",
        "profile",
    }
    missing = required - payload.keys()
    if missing:
        raise ValueError(f"run config missing fields: {sorted(missing)}")
    profile_data = dict(payload["profile"])
    profile_data["seeds"] = tuple(profile_data.get("seeds", ()))
    profile = RunProfile(**profile_data)
    if not profile.seeds or len(set(profile.seeds)) != len(profile.seeds):
        raise ValueError("run config must define unique fixed seeds")
    return PipelineConfig(
        run_id=str(payload["run_id"]),
        dataset=str(payload["dataset"]),
        manifest=Path(str(payload["manifest"])),
        frozen_eval_fixture=Path(str(payload["frozen_eval_fixture"])),
        frozen_eval_manifest=Path(str(payload["frozen_eval_manifest"])),
        artifact_root=Path(str(payload["artifact_root"])),
        suffix=str(payload["suffix"]),
        profile=profile,
    )
