"""Named run profiles for the Colab-first transcript pipeline.

The default is deliberately cheap.  Every paid profile needs an explicit
confirmation, and only the paper-reproduction profile enables synthetic TTS or
the perturbation hypotheses used by the historical DARAG reproduction.
Production Gipformer remains a single-best decoder.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunProfile:
    name: str
    limit_per_split: int | None
    asr_provider: str
    retrieval_backend: str
    n_best: int
    synth_count: int | None
    synth_tts_limit: int | None
    tts_provider: str
    nsyn_factor: float
    max_steps: int
    seeds: tuple[int, ...]
    all_variants: bool
    paid: bool = False
    enable_synthetic: bool = False
    enable_tts: bool = False
    train_mode: str = "qlora"
    candidate_variant: str = "full"
    candidate_seed: int = 13
    asr_experiment: str = "gipformer_single_best"
    enable_direct_asr: bool = False
    enable_phonetic: bool = False
    enable_near_miss: bool = False


SMOKE = RunProfile(
    name="smoke",
    limit_per_split=20,
    asr_provider="mock",
    retrieval_backend="lexical",
    n_best=1,
    synth_count=0,
    synth_tts_limit=0,
    tts_provider="none",
    nsyn_factor=0.0,
    max_steps=20,
    seeds=(13,),
    all_variants=False,
    train_mode="mock",
    asr_experiment="mock_single_best",
)

PILOT = RunProfile(
    name="pilot",
    limit_per_split=1_000,
    asr_provider="gipformer",
    retrieval_backend="hybrid",
    n_best=1,
    synth_count=0,
    synth_tts_limit=0,
    tts_provider="none",
    nsyn_factor=0.0,
    max_steps=200,
    seeds=(13,),
    all_variants=False,
    paid=True,
    asr_experiment="phowhisper_lora",
    enable_direct_asr=True,
    enable_phonetic=True,
    candidate_variant="phonetic",
)

RESEARCH_FULL = RunProfile(
    name="research-full",
    limit_per_split=None,
    asr_provider="gipformer",
    retrieval_backend="hybrid",
    n_best=1,
    synth_count=0,
    synth_tts_limit=0,
    tts_provider="none",
    nsyn_factor=0.0,
    max_steps=600,
    seeds=(13,),
    all_variants=False,
    paid=True,
    asr_experiment="phowhisper_lora",
    enable_direct_asr=True,
    enable_phonetic=True,
    candidate_variant="phonetic",
)

REPLICATE = RunProfile(
    name="replicate",
    limit_per_split=None,
    asr_provider="gipformer",
    retrieval_backend="hybrid",
    n_best=1,
    synth_count=0,
    synth_tts_limit=0,
    tts_provider="none",
    nsyn_factor=0.0,
    max_steps=600,
    seeds=(13, 7, 42),
    all_variants=False,
    paid=True,
    candidate_seed=13,
    asr_experiment="phowhisper_lora",
    enable_direct_asr=True,
    enable_phonetic=True,
    candidate_variant="phonetic",
)

REPRODUCTION = RunProfile(
    name="reproduction",
    limit_per_split=None,
    asr_provider="gipformer",
    retrieval_backend="hybrid",
    # These are deterministic acoustic variants, not decoder beam N-best.
    n_best=5,
    synth_count=None,
    synth_tts_limit=None,
    tts_provider="xtts",
    nsyn_factor=1.0,
    max_steps=600,
    seeds=(13, 7, 42),
    all_variants=True,
    paid=True,
    enable_synthetic=True,
    enable_tts=True,
    candidate_seed=13,
    asr_experiment="phowhisper_plain_lora_near_miss_not_implemented",
    enable_direct_asr=True,
    enable_phonetic=True,
    candidate_variant="phonetic",
    enable_near_miss=True,
)

PROFILES = {
    profile.name: profile
    for profile in (SMOKE, PILOT, RESEARCH_FULL, REPLICATE, REPRODUCTION)
}


def get_profile(name: str) -> RunProfile:
    if name not in PROFILES:
        raise ValueError(f"profile must be one of {sorted(PROFILES)}, got {name!r}")
    return PROFILES[name]
