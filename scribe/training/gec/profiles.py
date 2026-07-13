"""Run profiles: one switch for the whole pipeline instead of scattered constants.

``SMOKE`` is the fast, dependency-light plumbing check (tiny limits, mock ASR,
single seed). ``FULL`` is the real ViMedCSS run that follows the paper's knobs
(N=5 N-best, nsyn=n, 3 seeds, all ablation variants). Stage notebooks read every
run-size value from the active profile so there is a single source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunProfile:
    name: str
    limit_per_split: int | None      # rows per split for ASR pairs (None = full)
    asr_provider: str                # "mock" (smoke) or "gipformer"
    retrieval_backend: str           # lexical / semantic / hybrid
    n_best: int                      # paper N=5; 1 disables the other-hypotheses channel
    synth_count: int | None          # synthetic transcripts (None = match real train size)
    synth_tts_limit: int | None      # how many to voice-clone (None = all)
    tts_provider: str                # xtts (clone) or mms (fallback)
    nsyn_factor: float               # synthetic pairs added = factor * |real train|
    max_steps: int
    seeds: tuple[int, ...]           # paper averages 3
    all_variants: bool               # train full + ablations


SMOKE = RunProfile(
    name="smoke",
    limit_per_split=20,
    asr_provider="mock",
    retrieval_backend="lexical",
    n_best=1,
    synth_count=10,
    synth_tts_limit=10,
    tts_provider="mms",
    nsyn_factor=1.0,
    max_steps=20,
    seeds=(13,),
    all_variants=False,
)

FULL = RunProfile(
    name="full",
    limit_per_split=None,
    asr_provider="gipformer",
    retrieval_backend="hybrid",
    n_best=5,
    synth_count=None,
    synth_tts_limit=None,
    tts_provider="xtts",
    nsyn_factor=1.0,
    max_steps=600,
    seeds=(13, 7, 42),
    all_variants=True,
)

PROFILES = {SMOKE.name: SMOKE, FULL.name: FULL}


def get_profile(name: str) -> RunProfile:
    if name not in PROFILES:
        raise ValueError(f"profile must be one of {sorted(PROFILES)}, got {name!r}")
    return PROFILES[name]
