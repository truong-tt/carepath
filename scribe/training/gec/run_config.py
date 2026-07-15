"""Versioned JSON configuration for deterministic DARAG pipeline runs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from gec.config import VARIANTS
from gec.profiles import PROFILES, RunProfile


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
    if profile.name not in PROFILES:
        raise ValueError(f"run config profile must be one of {sorted(PROFILES)}")
    if profile.candidate_seed not in profile.seeds:
        raise ValueError("run config candidate_seed must be one of profile.seeds")
    if profile.candidate_variant not in VARIANTS:
        raise ValueError(f"run config candidate_variant must be one of {VARIANTS}")
    if profile.n_best < 1:
        raise ValueError("run config n_best must be at least 1")
    if profile.enable_tts and not profile.enable_synthetic:
        raise ValueError("run config cannot enable TTS without synthetic data")
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
