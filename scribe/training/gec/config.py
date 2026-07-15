"""Knobs and defaults for the DARAG GEC pipeline.

Values mirror the paper's hyper-parameters only in the explicit reproduction
profile. Production Gipformer exposes one transcript, so normal profiles use a
single-best input; deterministic acoustic variants are not decoder beam N-best.

Model choices deviate from the paper on purpose: the paper fine-tunes LLaMA-2-7B
(English); CarePath targets Vietnamese code-switched medical speech, so the base
GEC model and the synthetic-transcript generator default to multilingual Qwen3
checkpoints that fit a single L4 in 4-bit. The paper is explicitly
language-agnostic, so this is a faithful port rather than a change in method.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# GEC model fine-tuned with QLoRA (paper §4.3 fine-tunes LoRA adapters only).
DEFAULT_BASE_MODEL = "Qwen/Qwen3-4B-Instruct-2507"
FALLBACK_BASE_MODEL = "Qwen/Qwen2.5-3B-Instruct"

# Open-weight generator for synthetic transcripts (paper §4.1 Step 1 uses an
# instruction-tuned LLM with few-shot in-context examples).
DEFAULT_SYNTH_MODEL = "Qwen/Qwen3-4B-Instruct-2507"
FALLBACK_SYNTH_MODELS = ("Qwen/Qwen2.5-7B-Instruct", "google/gemma-3-4b-it")

# Voice-cloning TTS (paper §4.1 Step 2 conditions TTS on in-domain speakers).
# viXTTS is an XTTS-v2 checkpoint fine-tuned for Vietnamese that supports
# reference-clip voice cloning; MMS is the single-speaker labeled fallback.
DEFAULT_TTS_MODEL = "capleaf/viXTTS"
DEFAULT_MMS_MODEL = "facebook/mms-tts-vie"

# Frozen evaluation protocol. "hard" is CarePath's in-corpus OOD analog (paper's
# OOD is a second corpus; we expose nsmall for a future cross-corpus run).
DEFAULT_SPLITS = ("train", "validation", "test", "hard")
ID_SPLITS = ("validation", "test")
OOD_SPLITS = ("hard",)
GATE_SPLITS = ("validation", "hard")

# DARAG configurations plus CarePath's PiDA-inspired text-only candidate.
VARIANTS = ("full", "phonetic", "wo_rac", "wo_aug", "only_synth")


@dataclass(frozen=True)
class GecRunConfig:
    """Run-size + method knobs shared across the pipeline."""

    top_k_ne: int = 5            # paper k=5 (Appendix J.1: 5 is optimal)
    n_best: int = 1              # compatibility name; >1 means acoustic variants
    nsyn_factor: float = 1.0     # paper nsyn = n
    nsmall: int = 100            # paper OOD low-resource budget

    base_model: str = DEFAULT_BASE_MODEL
    fallback_base_model: str = FALLBACK_BASE_MODEL
    synth_model: str = DEFAULT_SYNTH_MODEL
    fallback_synth_models: tuple[str, ...] = FALLBACK_SYNTH_MODELS
    tts_model: str = DEFAULT_TTS_MODEL
    mms_model: str = DEFAULT_MMS_MODEL

    # QLoRA (paper §5: LoRA rank 8 worked; we use 16 for the larger Vietnamese
    # vocabulary surface — both are reported as roughly equivalent).
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05

    splits: tuple[str, ...] = field(default_factory=lambda: DEFAULT_SPLITS)
    variants: tuple[str, ...] = field(default_factory=lambda: VARIANTS)


def variant_uses_retrieval(variant: str) -> bool:
    """Whether the DARAG instruction should include retrieved NEs for ``variant``.

    Only ``wo_rac`` strips retrieval-augmented correction (paper §5 ablation
    "w/o RAC"); every other variant keeps the NE list in the prompt.
    """

    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {VARIANTS}, got {variant!r}")
    return variant != "wo_rac"
