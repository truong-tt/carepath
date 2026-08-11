"""Vietnamese speech synthesis for the patient-facing side of a visit.

Why this exists: the browser's SpeechSynthesis has no Vietnamese voice on a
default Windows or macOS install, so the English-patient to Vietnamese-clinician
direction is silent or read with English phonemes. That is half of a bilingual
visit.

No new dependency: sherpa-onnx already ships in this project for Gipformer ASR
and its OfflineTts covers Piper/VITS voices. The model is a 63 MB ONNX file that
runs on CPU at roughly four times real time.
"""

from __future__ import annotations

import io
import logging
import threading
import wave
from array import array
from pathlib import Path

logger = logging.getLogger("carepath.tts")

# Piper vi_VN voice, packaged for sherpa-onnx. VAIS-1000 corpus, CC BY 4.0.
DEFAULT_TTS_REPO = "csukuangfj/vits-piper-vi_VN-vais1000-medium"
MAX_TTS_CHARS = 800


class TTSError(RuntimeError):
    """Raised when speech synthesis is unavailable or fails."""


def _to_wav_bytes(samples: list[float], sample_rate: int) -> bytes:
    pcm = array("h", (int(max(-1.0, min(1.0, value)) * 32767) for value in samples))
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())
    return buffer.getvalue()


class VietnameseTTS:
    """Lazily loaded Piper/VITS voice. Thread-safe; the model loads once."""

    def __init__(self, model_dir: Path, repo_id: str = DEFAULT_TTS_REPO, num_threads: int = 2):
        self.model_dir = Path(model_dir)
        self.repo_id = repo_id
        self.num_threads = num_threads
        self._engine = None
        self._lock = threading.Lock()

    def readiness(self) -> tuple[bool, dict[str, object]]:
        return self.model_dir.is_dir(), {
            "provider": "piper_vits",
            "repo_id": self.repo_id,
            "model_dir": str(self.model_dir),
            "downloaded": self.model_dir.is_dir(),
            "loaded": self._engine is not None,
        }

    def ensure_model(self) -> Path:
        """Download the voice once. Returns the directory holding the ONNX file."""
        if (self.model_dir / "tokens.txt").exists():
            return self.model_dir
        try:
            from huggingface_hub import snapshot_download  # type: ignore
        except ImportError as exc:  # pragma: no cover - declared dependency
            raise TTSError("huggingface-hub is required to download the Vietnamese voice") from exc

        self.model_dir.parent.mkdir(parents=True, exist_ok=True)
        logger.info("downloading Vietnamese TTS voice %s", self.repo_id)
        # local_dir (not the HF cache) keeps the path short: espeak-ng reads its
        # data with a native call that fails past the Windows MAX_PATH limit,
        # and the default cache path is already ~250 characters.
        snapshot_download(
            repo_id=self.repo_id,
            local_dir=str(self.model_dir),
            allow_patterns=["*.onnx", "*.json", "tokens.txt", "espeak-ng-data/*", "MODEL_CARD"],
        )
        return self.model_dir

    def _load(self):
        if self._engine is not None:
            return self._engine
        with self._lock:
            if self._engine is not None:
                return self._engine
            try:
                import sherpa_onnx  # type: ignore
            except ImportError as exc:  # pragma: no cover - declared dependency
                raise TTSError("sherpa-onnx is required for Vietnamese speech") from exc

            root = self.ensure_model()
            models = sorted(root.glob("*.onnx"))
            if not models:
                raise TTSError(f"no ONNX voice found in {root}")
            espeak = root / "espeak-ng-data"
            if not espeak.is_dir():
                raise TTSError(f"espeak-ng-data missing from {root}")

            config = sherpa_onnx.OfflineTtsConfig(
                model=sherpa_onnx.OfflineTtsModelConfig(
                    vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                        model=str(models[0]),
                        tokens=str(root / "tokens.txt"),
                        data_dir=str(espeak),
                    ),
                    num_threads=self.num_threads,
                    provider="cpu",
                )
            )
            self._engine = sherpa_onnx.OfflineTts(config)
            logger.info("Vietnamese TTS voice loaded from %s", models[0].name)
        return self._engine

    def warmup(self) -> dict[str, object]:
        try:
            self._load()
            return {"tts": "ready", "model_dir": str(self.model_dir)}
        except Exception as exc:
            logger.warning("Vietnamese TTS warmup failed: %s", exc)
            return {"tts": "unavailable", "error": str(exc)}

    def synthesize(self, text: str, speed: float = 1.0) -> tuple[bytes, int]:
        """Return (wav_bytes, sample_rate) for a Vietnamese utterance."""
        cleaned = (text or "").strip()
        if not cleaned:
            raise TTSError("nothing to speak")
        if len(cleaned) > MAX_TTS_CHARS:
            raise TTSError(f"text longer than {MAX_TTS_CHARS} characters")
        engine = self._load()
        try:
            audio = engine.generate(cleaned, sid=0, speed=speed)
        except Exception as exc:
            raise TTSError(f"speech synthesis failed: {exc}") from exc
        return _to_wav_bytes(list(audio.samples), audio.sample_rate), audio.sample_rate


class DisabledTTS:
    """No-op used when TTS_PROVIDER is off; the browser voice remains the path."""

    def readiness(self) -> tuple[bool, dict[str, object]]:
        return False, {"provider": "disabled"}

    def warmup(self) -> dict[str, object]:
        return {"tts": "disabled"}

    def synthesize(self, text: str, speed: float = 1.0) -> tuple[bytes, int]:
        del text, speed
        raise TTSError("server-side speech is disabled (set TTS_PROVIDER=piper)")


def build_tts(settings) -> VietnameseTTS | DisabledTTS:
    if getattr(settings, "tts_provider", "piper") not in {"piper", "vits"}:
        return DisabledTTS()
    return VietnameseTTS(
        model_dir=settings.tts_model_dir,
        repo_id=settings.tts_repo_id,
        num_threads=settings.gipformer_num_threads,
    )
