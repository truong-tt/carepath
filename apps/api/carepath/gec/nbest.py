"""Perturbation-based N-best hypotheses for GEC (paper §3.1/§4.3, N=5).

The paper trains the corrector to revise the best hypothesis *using cues from the
other N-1 hypotheses* obtained by beam-search decoding. CarePath's runtime ASR is
sherpa-onnx Gipformer, whose offline ``OfflineRecognitionResult`` exposes only the
single best path — beam search runs internally but the alternative hypotheses are
never surfaced. So we approximate N-best the only model-agnostic way available:
re-decode the *same* Gipformer over light, deterministic audio perturbations and
collect the distinct transcripts. Most ASR errors that matter here (mangled
code-switched medical terms) flip under small acoustic changes, so the perturbed
decodes expose exactly the alternative spellings the corrector needs.

Crucially this same recipe must run at inference time too, so the trained model
always sees an ``Other hypotheses`` block consistent with training (no train/serve
skew). ``dedupe_keep_order`` is pure-python and unit-testable; ``diverse_hypotheses``
lazily imports numpy/soundfile.
"""

from __future__ import annotations

import re
import tempfile
import unicodedata
from pathlib import Path
from typing import Any, Callable

# Deterministic perturbation recipe. Each entry is (label, kind, amount); the
# acoustic transform is applied in ``_apply`` so the list stays import-cheap and
# the order is stable (best-first ranking depends on it).
PERTURBATIONS: tuple[tuple[str, str, float], ...] = (
    ("speed_down", "speed", 0.97),
    ("speed_up", "speed", 1.03),
    ("gain_down", "gain", 0.85),
    ("noise", "noise", 0.005),
    ("gain_up", "gain", 1.18),
)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", str(text)).lower().strip()
    return re.sub(r"\s+", " ", text)


def dedupe_keep_order(texts: list[str]) -> list[str]:
    """Drop empties and case/whitespace-duplicates, preserving first-seen order.

    The first element is treated as the best hypothesis, so ranking is the caller's
    responsibility (``diverse_hypotheses`` puts the un-perturbed decode first).
    """

    seen: set[str] = set()
    out: list[str] = []
    for text in texts:
        norm = _normalize(text)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        out.append(str(text).strip())
    return out


def _apply(np, samples, sample_rate: int, kind: str, amount: float, rng):
    """Return perturbed ``samples`` for one recipe entry (numpy float array)."""

    if kind == "gain":
        return np.clip(samples * amount, -1.0, 1.0)
    if kind == "noise":
        noise = rng.normal(0.0, amount, size=samples.shape).astype("float32")
        return np.clip(samples + noise, -1.0, 1.0)
    if kind == "speed":
        # Resample to change duration/pitch slightly (cheap linear interp); the
        # decoder still runs at the file's declared sample_rate.
        dst_len = max(1, int(round(len(samples) / amount)))
        src_index = np.linspace(0, len(samples) - 1, num=dst_len)
        return np.interp(src_index, np.arange(len(samples)), samples).astype("float32")
    return samples


def diverse_hypotheses(
    asr: Any,
    audio_path: Path,
    n: int = 5,
    seed: int = 13,
    best_text: str | None = None,
) -> list[str]:
    """Return up to ``n`` distinct hypotheses, best-first, for one clip.

    ``best_text`` (the already-computed 1-best) seeds the list so the original is
    never re-decoded. ``asr`` only needs ``transcribe(path) -> result.text``. When
    ``n <= 1`` this is just ``[best_text]`` and no perturbation work happens.
    """

    audio_path = Path(audio_path)
    best = (best_text if best_text is not None else asr.transcribe(audio_path).text) or ""
    if n <= 1:
        return dedupe_keep_order([best])

    import numpy as np  # type: ignore
    import soundfile as sf  # type: ignore

    samples, sample_rate = sf.read(str(audio_path), dtype="float32", always_2d=False)
    if getattr(samples, "ndim", 1) > 1:  # mix to mono
        samples = samples.mean(axis=1)
    rng = np.random.default_rng(seed)

    texts = [best]
    with tempfile.TemporaryDirectory(prefix="carepath_nbest_") as temp_dir:
        for label, kind, amount in PERTURBATIONS:
            if len(dedupe_keep_order(texts)) >= n:
                break
            perturbed = _apply(np, samples, sample_rate, kind, amount, rng)
            clip_path = Path(temp_dir) / f"{label}.wav"
            sf.write(str(clip_path), perturbed, int(sample_rate))
            try:
                texts.append(asr.transcribe(clip_path).text or "")
            except Exception:
                continue  # a failed perturbation must never lose the real hypotheses
    return dedupe_keep_order(texts)[:n]


def other_hypotheses(
    asr: Any,
    audio_path: Path,
    best_text: str,
    n_best: int,
    seed: int = 13,
) -> list[str]:
    """The non-best hypotheses (``hypotheses[1:]``) for the GEC prompt's other-hyps.

    Returns ``[]`` when ``n_best <= 1`` so callers keep the cheap single-decode path
    unless they explicitly ask for N-best.
    """

    if n_best <= 1:
        return []
    ranked = diverse_hypotheses(asr, audio_path, n=n_best, seed=seed, best_text=best_text)
    return ranked[1:]
