"""Voice-cloning TTS for synthetic speech (paper §4.1 Step 2 + Appendix D).

The paper conditions the TTS model on *randomly selected in-domain utterances* so
the synthetic speech mimics real speakers, which makes the resulting ASR
hypotheses carry the same phonetic confusions the ASR model produces at test time.
Appendix D / Table 7 show this voice cloning is important — performance drops
sharply without it, especially OOD.

CarePath reproduces this with reference-conditioned (voice-cloning) TTS:

* ``XttsVoiceCloner`` — XTTS-v2 / viXTTS, cloned from a random ViMedCSS reference
  clip per utterance. This is the paper-faithful path.
* ``MmsSynthesizer`` — single-speaker ``facebook/mms-tts-vie``, kept only as an
  explicit, labeled fallback (``tts_provider="mms_no_clone"``) so any run that
  could not clone is visible in the manifest and downstream metadata.

``ReferenceClipSampler`` materializes reference wavs from the ViMedCSS audio (or a
local directory) once and serves a random clip per synthesis call. All ML imports
are lazy; ``synthesize_manifest`` orchestrates clean-transcript -> audio manifest.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any, Protocol

from carepath.gec.config import DEFAULT_MMS_MODEL, DEFAULT_TTS_MODEL


class Synthesizer(Protocol):
    provider: str

    def synthesize(self, text: str, output_path: Path, speaker_wav: str | None = None) -> None:
        ...


class ReferenceClipSampler:
    """Serves random in-domain reference clips for voice cloning."""

    def __init__(self, clips: list[Path], seed: int = 13):
        self.clips = list(clips)
        self._rng = random.Random(seed)

    def sample(self) -> str | None:
        if not self.clips:
            return None
        return str(self._rng.choice(self.clips))

    @classmethod
    def from_directory(cls, directory: Path, seed: int = 13) -> "ReferenceClipSampler":
        clips = sorted(directory.glob("*.wav"))
        return cls(clips, seed=seed)

    @classmethod
    def from_dataset(
        cls,
        dataset: str,
        split: str,
        count: int,
        cache_dir: Path,
        seed: int = 13,
    ) -> "ReferenceClipSampler":
        """Extract ``count`` reference wavs from an HF audio dataset split."""

        import soundfile as sf  # type: ignore
        from datasets import Audio, load_dataset  # type: ignore

        cache_dir.mkdir(parents=True, exist_ok=True)
        data = load_dataset(dataset, split=split).cast_column("audio", Audio(decode=True))
        count = min(count, len(data))
        data = data.select(range(count))
        clips: list[Path] = []
        for row in data:
            audio = row["audio"]
            clip_path = cache_dir / f"ref_{_safe(str(row.get('segment_id', len(clips))))}.wav"
            sf.write(str(clip_path), audio["array"], int(audio["sampling_rate"]))
            clips.append(clip_path)
        return cls(clips, seed=seed)


class XttsVoiceCloner:
    """XTTS-v2 / viXTTS reference-conditioned synthesizer (the cloning path)."""

    provider = "xtts_voice_clone"

    def __init__(self, model: str = DEFAULT_TTS_MODEL, language: str = "vi", use_gpu: bool = True):
        from TTS.api import TTS  # type: ignore

        self.language = language
        self.model_name = model
        model_path = Path(model)
        if model_path.exists():  # local viXTTS checkpoint dir
            self.tts = TTS(
                model_path=str(model_path),
                config_path=str(model_path / "config.json"),
            )
        else:
            self.tts = TTS(model)
        if use_gpu:
            try:
                self.tts.to("cuda")
            except Exception:
                pass

    def synthesize(self, text: str, output_path: Path, speaker_wav: str | None = None) -> None:
        if not speaker_wav:
            raise ValueError("XttsVoiceCloner requires a speaker_wav reference clip")
        self.tts.tts_to_file(
            text=text,
            speaker_wav=speaker_wav,
            language=self.language,
            file_path=str(output_path),
        )


class MmsSynthesizer:
    """Single-speaker MMS fallback (no voice cloning) — labeled as such."""

    provider = "mms_no_clone"

    def __init__(self, model: str = DEFAULT_MMS_MODEL):
        import torch  # type: ignore
        from transformers import AutoTokenizer, VitsModel  # type: ignore

        self.torch = torch
        self.model_name = model
        self.tokenizer = AutoTokenizer.from_pretrained(model)
        self.model = VitsModel.from_pretrained(model)
        self.model.eval()

    def synthesize(self, text: str, output_path: Path, speaker_wav: str | None = None) -> None:
        import soundfile as sf  # type: ignore

        inputs = self.tokenizer(text, return_tensors="pt")
        with self.torch.no_grad():
            waveform = self.model(**inputs).waveform[0].cpu().numpy()
        sf.write(str(output_path), waveform, self.model.config.sampling_rate)


def build_synthesizer(
    provider: str = "xtts",
    model: str | None = None,
    language: str = "vi",
    use_gpu: bool = True,
) -> Synthesizer:
    """Build the requested synthesizer, falling back to MMS if XTTS is unavailable."""

    if provider in {"xtts", "vixtts", "voice_clone"}:
        try:
            return XttsVoiceCloner(model or DEFAULT_TTS_MODEL, language=language, use_gpu=use_gpu)
        except Exception as exc:  # pragma: no cover - depends on optional dep
            print(f"[tts] XTTS unavailable ({exc}); falling back to single-speaker MMS.")
            return MmsSynthesizer(DEFAULT_MMS_MODEL)
    if provider == "mms":
        return MmsSynthesizer(model or DEFAULT_MMS_MODEL)
    raise ValueError(f"provider must be 'xtts' or 'mms', got {provider!r}")


def synthesize_manifest(
    clean_rows: list[dict[str, Any]],
    synthesizer: Synthesizer,
    audio_dir: Path,
    sampler: ReferenceClipSampler | None,
    output_path: Path,
    completed_ids: set[str] | None = None,
) -> int:
    """Synthesize audio for each clean transcript; append manifest rows."""

    audio_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed_ids = completed_ids or set()
    written = 0
    mode = "a" if output_path.exists() else "w"
    with output_path.open(mode, encoding="utf-8") as handle:
        for row in clean_rows:
            synthetic_id = row["synthetic_id"]
            if synthetic_id in completed_ids:
                continue
            speaker_wav = sampler.sample() if sampler else None
            audio_path = audio_dir / f"{_safe(synthetic_id)}.wav"
            synthesizer.synthesize(row["clean_text"], audio_path, speaker_wav=speaker_wav)
            handle.write(
                json.dumps(
                    {
                        **row,
                        "audio_path": str(audio_path),
                        "tts_provider": synthesizer.provider,
                        "tts_model": getattr(synthesizer, "model_name", None),
                        "speaker_reference": speaker_wav,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            handle.flush()
            written += 1
    return written


def load_completed_audio_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("synthetic_id") and row.get("audio_path"):
            ids.add(row["synthetic_id"])
    return ids


def _safe(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(value))
