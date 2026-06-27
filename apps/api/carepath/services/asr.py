from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from carepath.config import Settings


class ASRError(RuntimeError):
    """Raised when ASR inference fails."""


@dataclass(frozen=True)
class ASRResult:
    text: str
    model: str
    metadata: dict[str, object]


class ASRService(Protocol):
    def transcribe(self, audio_path: Path) -> ASRResult:
        ...

    def readiness(self) -> tuple[bool, dict[str, object]]:
        ...


class GipformerASR:
    repo_id = "g-group-ai-lab/gipformer-65M-rnnt"
    sample_rate = 16000
    feature_dim = 80
    onnx_files = {
        "fp32": {
            "encoder": "encoder-epoch-35-avg-6.onnx",
            "decoder": "decoder-epoch-35-avg-6.onnx",
            "joiner": "joiner-epoch-35-avg-6.onnx",
        },
        "int8": {
            "encoder": "encoder-epoch-35-avg-6.int8.onnx",
            "decoder": "decoder-epoch-35-avg-6.int8.onnx",
            "joiner": "joiner-epoch-35-avg-6.int8.onnx",
        },
    }

    def __init__(self, settings: Settings):
        if settings.gipformer_quantize not in self.onnx_files:
            raise ValueError("GIPFORMER_QUANTIZE must be 'fp32' or 'int8'")
        self.settings = settings
        self._recognizer = None
        self._model_paths: dict[str, str] | None = None

    def readiness(self) -> tuple[bool, dict[str, object]]:
        missing: list[str] = []
        for module_name in ("sherpa_onnx", "huggingface_hub", "soundfile"):
            try:
                __import__(module_name)
            except ImportError:
                missing.append(module_name)
        return (
            len(missing) == 0,
            {
                "repo_id": self.repo_id,
                "quantize": self.settings.gipformer_quantize,
                "chunk_seconds": self.settings.gipformer_chunk_seconds,
                "missing_modules": missing,
            },
        )

    def transcribe(self, audio_path: Path) -> ASRResult:
        recognizer = self._get_recognizer()
        try:
            import soundfile as sf  # type: ignore
        except ImportError as exc:  # pragma: no cover - exercised by readiness
            raise ASRError("soundfile is required for Gipformer ASR") from exc

        try:
            samples, sample_rate = sf.read(str(audio_path), dtype="float32")
            if getattr(samples, "ndim", 1) > 1:
                samples = samples.mean(axis=1)
            chunk_size = max(1, int(sample_rate * self.settings.gipformer_chunk_seconds))
            transcripts: list[str] = []
            chunk_count = 0
            for start in range(0, len(samples), chunk_size):
                chunk = samples[start : start + chunk_size]
                if len(chunk) == 0:
                    continue
                chunk_count += 1
                stream = recognizer.create_stream()
                stream.accept_waveform(sample_rate, chunk)
                recognizer.decode_streams([stream])
                chunk_text = stream.result.text.strip()
                if chunk_text:
                    transcripts.append(chunk_text)
            text = " ".join(transcripts).strip()
        except Exception as exc:  # pragma: no cover - requires ASR runtime
            raise ASRError(f"Gipformer transcription failed: {exc}") from exc

        duration_seconds = len(samples) / sample_rate if sample_rate else 0.0
        return ASRResult(
            text=text,
            model=f"gipformer-65M-rnnt/{self.settings.gipformer_quantize}",
            metadata={
                "repo_id": self.repo_id,
                "decoding_method": self.settings.gipformer_decoding_method,
                "chunk_seconds": self.settings.gipformer_chunk_seconds,
                "duration_seconds": round(duration_seconds, 3),
                "chunk_count": chunk_count,
            },
        )

    def _get_recognizer(self):
        if self._recognizer is not None:
            return self._recognizer

        try:
            import sherpa_onnx  # type: ignore
            from huggingface_hub import hf_hub_download  # type: ignore
        except ImportError as exc:
            raise ASRError(
                "Install Gipformer runtime dependencies: "
                "pip install sherpa-onnx huggingface-hub soundfile numpy"
            ) from exc

        model_paths: dict[str, str] = {}
        for key, filename in self.onnx_files[self.settings.gipformer_quantize].items():
            model_paths[key] = hf_hub_download(repo_id=self.repo_id, filename=filename)
        model_paths["tokens"] = hf_hub_download(repo_id=self.repo_id, filename="tokens.txt")

        self._recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
            encoder=model_paths["encoder"],
            decoder=model_paths["decoder"],
            joiner=model_paths["joiner"],
            tokens=model_paths["tokens"],
            num_threads=self.settings.gipformer_num_threads,
            sample_rate=self.sample_rate,
            feature_dim=self.feature_dim,
            decoding_method=self.settings.gipformer_decoding_method,
        )
        self._model_paths = model_paths
        return self._recognizer


class MockASR:
    """Debug-only ASR for frontend integration before audio runtime is installed."""

    def __init__(self, allow: bool):
        self.allow = allow

    def readiness(self) -> tuple[bool, dict[str, object]]:
        return self.allow, {"warning": "mock ASR is for local frontend/debug only"}

    def transcribe(self, audio_path: Path) -> ASRResult:
        if not self.allow:
            raise ASRError("Mock ASR requested but ALLOW_MOCK_ASR is false")
        return ASRResult(
            text=(
                "Bệnh nhân đau ngực nhẹ, SpO2 98 phần trăm, huyết áp "
                "120 trên 80 mmHg, cần bác sĩ kiểm tra thêm."
            ),
            model="mock-asr",
            metadata={"audio_path": str(audio_path)},
        )


def build_asr_service(settings: Settings) -> ASRService:
    if settings.asr_provider == "mock":
        return MockASR(allow=settings.allow_mock_asr)
    if settings.asr_provider == "gipformer":
        return GipformerASR(settings)
    raise ValueError("ASR_PROVIDER must be 'gipformer' or 'mock'")
