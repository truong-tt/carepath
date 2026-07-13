"""Scribe post-ASR Generative Error Correction (DARAG).

A standalone, paper-faithful re-implementation of DARAG (Ghosh et al., *Failing
Forward: Improving Generative Error Correction for ASR with Synthetic Data and
Retrieval Augmentation*, Findings of ACL 2025) adapted to Vietnamese medical
code-switched ASR.

The package is the **offline training/data/eval layer** only — it never imports
from the FastAPI runtime correction path (``carepath.services.llm`` /
``carepath.services.retrieval``). It does reuse the ASR service
(``carepath.services.asr``) and ``carepath.config.Settings`` because those are
the *speech recognizer* and shared config, not the post-ASR corrector.

Pipeline (mirrors the paper):

1. ``datastore`` — extract named entities / code-switch terms into a datastore
   (paper §4.2 Step 1).
2. ``data.build_real_pairs`` — run Gipformer over real ViMedCSS audio to get
   ``raw_asr -> gold_text`` pairs (paper §3.1).
3. ``synthetic`` — few-shot LLM generation of new in-domain transcripts
   (paper §4.1 Step 1) with a leakage guard.
4. ``tts`` — voice-cloning TTS conditioned on in-domain reference speech
   (paper §4.1 Step 2 + Appendix D).
5. ``data.build_synthetic_pairs`` — Gipformer over the synthetic audio
   (paper §4.1 Step 3), then ``augment`` into the training set.
6. ``leakage`` — SentenceBERT cosine + BLEU report proving the synthetic data is
   not memorized (paper Appendix C / Table 6).
7. ``train`` — QLoRA fine-tune with the DARAG instruction template, including the
   ``w/o RAC`` / ``w/o Aug`` / ``only Synth`` ablation variants (paper §5).
8. ``predict`` / ``evaluate`` — adapter inference + WER and NE-F1 tables
   (paper Tables 3 & 4).
9. ``gate`` — accept the trained adapter only if it beats every baseline.

Heavy modules (``synthetic``, ``tts``, ``train``, ``predict`` and the semantic
retriever / leakage report) import torch/transformers/sentence-transformers
lazily, so the pure-python core (``prompts``, ``metrics``, ``leakage`` guards,
``datastore`` extraction, ``data`` validation, ``evaluate`` aggregation,
``gate``) imports with no ML dependencies.
"""

from gec.config import (
    DEFAULT_BASE_MODEL,
    DEFAULT_SYNTH_MODEL,
    FALLBACK_BASE_MODEL,
    GecRunConfig,
)

__all__ = [
    "DEFAULT_BASE_MODEL",
    "DEFAULT_SYNTH_MODEL",
    "FALLBACK_BASE_MODEL",
    "GecRunConfig",
]
