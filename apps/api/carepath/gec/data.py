"""GEC pair schema, dataset construction, augmentation, and ablation selection.

A *pair* is one ``raw_asr -> gold_text`` example carrying the retrieved NEs and
provenance. Real pairs come from running Gipformer over ViMedCSS audio
(paper §3.1); synthetic pairs come from running Gipformer over voice-cloned TTS
audio (paper §4.1 Step 3). ``augment_training_pairs`` merges them (paper §5:
``nsyn = n``), and ``select_variant_rows`` carves out the four ablation
configurations (paper §5 "Comparison Methods").

Pure-python (validation, jsonl IO, augmentation, variant selection) imports with
no ML deps; ``build_real_pairs`` / ``build_synthetic_pairs`` lazily import
``datasets`` and the ASR service.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from carepath.gec.config import variant_uses_retrieval
from carepath.gec.metrics import split_terms

REAL_SOURCE = "vimedcss_real"
SYNTHETIC_SOURCE = "darag_synthetic_tts"
VALID_SOURCES = {REAL_SOURCE, SYNTHETIC_SOURCE}

GEC_PAIR_REQUIRED_FIELDS = {
    "split",
    "source_kind",
    "audio_id",
    "raw_asr",
    "gold_text",
    "gold_terms",
    "retrieved_terms",
    "asr_model",
}
SYNTHETIC_REQUIRED_FIELDS = {
    "source_kind",
    "synthetic_id",
    "clean_text",
    "topic",
    "seed_example_ids",
    "model",
}


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[str]


def validate_gec_pair(row: dict[str, Any]) -> ValidationResult:
    errors = _missing(row, GEC_PAIR_REQUIRED_FIELDS)
    if row.get("source_kind") not in VALID_SOURCES:
        errors.append(f"source_kind must be one of {sorted(VALID_SOURCES)}")
    if not str(row.get("raw_asr", "")).strip():
        errors.append("raw_asr must be non-empty")
    if not str(row.get("gold_text", "")).strip():
        errors.append("gold_text must be non-empty")
    if not isinstance(row.get("gold_terms"), list):
        errors.append("gold_terms must be a list")
    if not isinstance(row.get("retrieved_terms"), list):
        errors.append("retrieved_terms must be a list")
    return ValidationResult(ok=not errors, errors=errors)


def validate_synthetic_transcript(row: dict[str, Any]) -> ValidationResult:
    errors = _missing(row, SYNTHETIC_REQUIRED_FIELDS)
    clean = str(row.get("clean_text", "")).strip()
    if not clean:
        errors.append("clean_text must be non-empty")
    elif len(clean.split()) < 5:
        errors.append("clean_text is too short for ASR/GEC training")
    if row.get("source_kind") != "darag_synthetic_clean":
        errors.append("source_kind must be darag_synthetic_clean")
    return ValidationResult(ok=not errors, errors=errors)


# --------------------------------------------------------------------------- IO


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


# ------------------------------------------------------------- augment / select


def augment_training_pairs(
    real_pairs: list[dict[str, Any]],
    synthetic_pairs: list[dict[str, Any]],
    nsyn_factor: float = 1.0,
) -> list[dict[str, Any]]:
    """Merge real ``train`` pairs with up to ``nsyn_factor * n`` synthetic pairs.

    Only the real ``train`` split is augmented; validation/test/hard stay frozen
    and real (paper keeps evaluation splits untouched). Synthetic pairs are forced
    onto the ``train`` split.
    """

    real_train = [r for r in real_pairs if r.get("split") == "train"]
    held_out = [r for r in real_pairs if r.get("split") != "train"]
    budget = int(round(nsyn_factor * len(real_train))) if real_train else len(synthetic_pairs)
    chosen = [{**r, "split": "train"} for r in synthetic_pairs[:budget]]
    return real_train + chosen + held_out


def select_variant_rows(
    augmented_pairs: list[dict[str, Any]],
    variant: str,
) -> tuple[list[dict[str, Any]], bool]:
    """Return (training rows, use_retrieval) for a DARAG ablation variant.

    * ``full``       — real + synthetic train rows, NEs in prompt.
    * ``wo_rac``     — same rows, NEs stripped from the prompt (use_retrieval=False).
    * ``wo_aug``     — real train rows only (drop synthetic), NEs in prompt.
    * ``only_synth`` — synthetic train rows only, NEs in prompt.

    Validation rows (real ``validation`` split) are returned separately by
    ``eval_split_rows`` and are never altered by the variant.
    """

    use_retrieval = variant_uses_retrieval(variant)
    train_rows = [r for r in augmented_pairs if r.get("split") == "train"]
    if variant == "wo_aug":
        train_rows = [r for r in train_rows if r.get("source_kind") == REAL_SOURCE]
    elif variant == "only_synth":
        train_rows = [r for r in train_rows if r.get("source_kind") == SYNTHETIC_SOURCE]
    return train_rows, use_retrieval


def eval_split_rows(pairs: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    return [r for r in pairs if r.get("split") == split]


# ----------------------------------------------------- build pairs (lazy/heavy)


def build_real_pairs(
    dataset: str,
    splits: list[str],
    retriever,
    asr,
    limit_per_split: int | None = None,
    completed_ids: set[str] | None = None,
):
    """Yield real GEC pairs by running ``asr`` over each ``dataset`` audio clip.

    ``retriever`` and ``asr`` are injected so this stays testable; the CLI wires
    in the gec NE retriever and ``carepath.services.asr``.
    """

    import soundfile as sf  # type: ignore
    from datasets import Audio, load_dataset  # type: ignore

    completed_ids = completed_ids or set()
    for split in splits:
        data = load_dataset(dataset, split=split).cast_column("audio", Audio(decode=True))
        if limit_per_split:
            data = data.select(range(min(limit_per_split, len(data))))
        for row in data:
            audio_id = f"{split}:{row['segment_id']}"
            if audio_id in completed_ids:
                continue
            audio = row["audio"]
            with tempfile.TemporaryDirectory(prefix="carepath_gec_") as temp_dir:
                wav_path = Path(temp_dir) / f"{row['segment_id']}.wav"
                sf.write(str(wav_path), audio["array"], int(audio["sampling_rate"]))
                result = asr.transcribe(wav_path)
            gold_terms = split_terms(row.get("cs_terms_list", ""))
            retrieval_text = " ".join(p for p in (result.text, row["segment_text"]) if p)
            retrieved = [item.term for item in retriever.retrieve(retrieval_text)]
            yield {
                "split": split,
                "source_kind": REAL_SOURCE,
                "audio_id": row["segment_id"],
                "raw_asr": result.text,
                "gold_text": row["segment_text"],
                "gold_terms": gold_terms,
                "retrieved_terms": retrieved,
                "cs_terms_list": row.get("cs_terms_list", ""),
                "topic": row.get("topic"),
                "duration_seconds": row.get("duration_seconds"),
                "asr_model": result.model,
                "asr_metadata": result.metadata,
            }


def build_synthetic_pairs(
    manifest_rows: list[dict[str, Any]],
    retriever,
    asr,
    completed_ids: set[str] | None = None,
):
    """Yield synthetic GEC pairs by running ``asr`` over voice-cloned TTS audio."""

    completed_ids = completed_ids or set()
    for row in manifest_rows:
        synthetic_id = row["synthetic_id"]
        if synthetic_id in completed_ids:
            continue
        result = asr.transcribe(Path(row["audio_path"]))
        retrieval_text = f"{result.text} {row['clean_text']}"
        retrieved = [item.term for item in retriever.retrieve(retrieval_text)]
        yield {
            "split": row.get("split", "train"),
            "source_kind": SYNTHETIC_SOURCE,
            "audio_id": synthetic_id,
            "synthetic_id": synthetic_id,
            "raw_asr": result.text,
            "gold_text": row["clean_text"],
            "gold_terms": row.get("intended_terms", []),
            "retrieved_terms": retrieved,
            "topic": row.get("topic"),
            "duration_seconds": result.metadata.get("duration_seconds"),
            "asr_model": result.model,
            "asr_metadata": result.metadata,
            "tts_model": row.get("tts_model"),
            "tts_provider": row.get("tts_provider"),
            "speaker_reference": row.get("speaker_reference"),
            "audio_path": row.get("audio_path"),
        }


def _missing(row: dict[str, Any], required: set[str]) -> list[str]:
    return [f"missing required field: {f}" for f in sorted(required) if f not in row]
