"""Versioned configuration for the research-only SOAP pipeline."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BASE_MODEL = "Qwen/Qwen3-4B-Instruct-2507"
PROFILE_RULES = {
    "smoke": {"max_rows": 20, "max_steps": 20, "seeds": (13,), "trainer": "mock"},
    "pilot": {"max_rows": 500, "max_steps": 200, "seeds": (13,), "trainer": "qlora"},
    "research-full": {"max_rows": None, "max_steps": None, "seeds": (13,), "trainer": "qlora"},
    "replicate": {"max_rows": None, "max_steps": None, "seeds": (13, 7, 42), "trainer": "qlora"},
}


@dataclass(frozen=True)
class SoapConfig:
    run_id: str
    manifest: Path
    artifact_root: Path
    canonical_terms: Path
    medev_terms: Path | None
    medev_source_id: str | None
    sources: tuple[dict[str, Any], ...]
    profile_name: str
    max_rows: int | None
    max_steps: int
    seeds: tuple[int, ...]
    selected_seed: int
    trainer: str
    teacher: str
    base_model: str
    base_revision: str

    @property
    def run_root(self) -> Path:
        return self.artifact_root / self.run_id


def load_config(path: Path) -> SoapConfig:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "run_id",
        "manifest",
        "artifact_root",
        "canonical_terms",
        "sources",
        "profile",
    }
    missing = required - payload.keys()
    if missing:
        raise ValueError(f"SOAP config missing fields: {sorted(missing)}")
    profile = dict(payload["profile"])
    name = str(profile.get("name", ""))
    if name not in PROFILE_RULES:
        raise ValueError(f"SOAP profile must be one of {sorted(PROFILE_RULES)}")
    rule = PROFILE_RULES[name]
    max_rows = profile.get("max_rows")
    max_steps = int(profile.get("max_steps", 0))
    seeds = tuple(int(seed) for seed in profile.get("seeds", ()))
    trainer = str(profile.get("trainer", ""))
    if not seeds or len(seeds) != len(set(seeds)):
        raise ValueError("SOAP profile requires unique fixed seeds")
    if seeds != rule["seeds"]:
        raise ValueError(f"SOAP profile {name!r} requires seeds {rule['seeds']}")
    if trainer != rule["trainer"]:
        raise ValueError(f"SOAP profile {name!r} requires trainer {rule['trainer']!r}")
    if rule["max_rows"] is not None and (not max_rows or int(max_rows) > rule["max_rows"]):
        raise ValueError(f"SOAP profile {name!r} allows at most {rule['max_rows']} rows")
    if rule["max_steps"] is not None and (max_steps <= 0 or max_steps > rule["max_steps"]):
        raise ValueError(f"SOAP profile {name!r} allows at most {rule['max_steps']} steps")
    selected_seed = int(profile.get("selected_seed", seeds[0]))
    if selected_seed not in seeds:
        raise ValueError("selected_seed must be one of the profile seeds")
    teacher = str(profile.get("teacher", ""))
    if teacher not in {"synthetic", "ckey"}:
        raise ValueError("SOAP teacher must be 'synthetic' or 'ckey'")
    base_revision = str(payload.get("base_revision", "main"))
    if trainer == "qlora" and not re.fullmatch(r"[0-9a-f]{40}", base_revision):
        raise ValueError("paid SOAP profiles require an exact 40-character base/tokenizer revision")
    return SoapConfig(
        run_id=str(payload["run_id"]),
        manifest=Path(str(payload["manifest"])),
        artifact_root=Path(os.environ.get("CAREPATH_ARTIFACT_ROOT", str(payload["artifact_root"]))),
        canonical_terms=Path(str(payload["canonical_terms"])),
        medev_terms=Path(str(payload["medev_terms"])) if payload.get("medev_terms") else None,
        medev_source_id=str(payload["medev_source_id"]) if payload.get("medev_source_id") else None,
        sources=tuple(dict(item) for item in payload["sources"]),
        profile_name=name,
        max_rows=int(max_rows) if max_rows is not None else None,
        max_steps=max_steps,
        seeds=seeds,
        selected_seed=selected_seed,
        trainer=trainer,
        teacher=teacher,
        base_model=str(payload.get("base_model", BASE_MODEL)),
        base_revision=base_revision,
    )
