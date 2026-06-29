from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from carepath.config import Settings

logger = logging.getLogger("carepath.asr")


class ASRError(RuntimeError):
    """Raised when ASR inference fails."""


def _plan_windows(
    n_samples: int, window_samples: int, overlap_samples: int
) -> list[tuple[int, int]]:
    """Split ``n_samples`` into ``[start, end)`` windows.

    ``overlap_samples == 0`` gives disjoint fixed windows (legacy behavior);
    a positive overlap makes adjacent windows share audio so a word cut at one
    boundary is recovered whole in the neighbor and de-duplicated on merge.
    """

    if n_samples <= 0:
        return []
    window_samples = max(1, window_samples)
    overlap_samples = max(0, min(overlap_samples, window_samples - 1))
    step = window_samples - overlap_samples  # >= 1
    windows: list[tuple[int, int]] = []
    start = 0
    while start < n_samples:
        end = min(start + window_samples, n_samples)
        windows.append((start, end))
        if end >= n_samples:
            break
        start += step
    return windows


def _merge_overlapping_text(prev: str, nxt: str) -> str:
    """Concatenate two overlapping-window transcripts, dropping the repeated seam.

    Finds the longest run of words that ends ``prev`` and starts ``nxt`` (compared
    case-insensitively) and keeps only one copy. When there is no shared run we
    plain-join, so the worst case is a little duplication, never a lost word.
    """

    prev = prev.strip()
    nxt = nxt.strip()
    if not prev:
        return nxt
    if not nxt:
        return prev
    prev_tokens = prev.split()
    nxt_tokens = nxt.split()
    max_k = min(len(prev_tokens), len(nxt_tokens))
    for k in range(max_k, 0, -1):
        tail = [token.lower() for token in prev_tokens[-k:]]
        head = [token.lower() for token in nxt_tokens[:k]]
        if tail == head:
            return " ".join(prev_tokens + nxt_tokens[k:])
    return " ".join(prev_tokens + nxt_tokens)


def _merge_text_windows(texts: list[str]) -> str:
    merged = ""
    for text in texts:
        merged = _merge_overlapping_text(merged, text)
    return merged.strip()


def _resample_linear(np, samples, src_rate: int, dst_rate: int):
    """Cheap linear resample (numpy-only) so VAD can run at its required 16 kHz."""

    if src_rate == dst_rate or len(samples) == 0:
        return samples
    dst_len = max(1, int(round(len(samples) / src_rate * dst_rate)))
    src_index = np.linspace(0, len(samples) - 1, num=dst_len)
    return np.interp(src_index, np.arange(len(samples)), samples).astype("float32")


@dataclass(frozen=True)
class ASRResult:
    text: str
    model: str
    metadata: dict[str, object]
    # Optional N-best hypotheses, best-first, when a caller decoded them (see
    # ``carepath.gec.nbest``). Empty for the default single-decode path; consumers
    # should fall back to ``(text,)`` when this is empty.
    hypotheses: tuple[str, ...] = ()


class ASRService(Protocol):
    def transcribe(self, audio_path: Path) -> ASRResult:
        ...

    def readiness(self) -> tuple[bool, dict[str, object]]:
        ...

    def warmup(self) -> dict[str, object]:
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

    def warmup(self) -> dict[str, object]:
        """Download ONNX artifacts and build the recognizer ahead of demo time."""

        self._get_recognizer()
        return {
            "provider": "gipformer",
            "ready": True,
            "repo_id": self.repo_id,
            "quantize": self.settings.gipformer_quantize,
        }

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
            text, segmentation, segment_count = self._transcribe_samples(
                recognizer, samples, sample_rate
            )
        except ASRError:
            raise
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
                "segmentation": segmentation,
                "segment_count": segment_count,
                "duration_seconds": round(duration_seconds, 3),
                # ``chunk_count`` retained for backward compatibility with older
                # manifests/metrics; it now equals segment_count.
                "chunk_count": segment_count,
            },
        )

    def _transcribe_samples(self, recognizer, samples, sample_rate) -> tuple[str, str, int]:
        """Decode ``samples`` using the configured segmentation strategy.

        Returns ``(text, segmentation_used, segment_count)``. ``vad`` degrades to
        ``overlap`` whenever the VAD model/deps are unavailable, so a missing
        silero model never breaks transcription.
        """

        mode = self.settings.gipformer_segmentation
        window_samples = max(1, int(sample_rate * self.settings.gipformer_chunk_seconds))

        if mode == "vad":
            segments = self._segments_from_vad(samples, sample_rate)
            if segments is not None:
                max_seg = max(
                    1, int(sample_rate * self.settings.gipformer_max_segment_seconds)
                )
                overlap_samples = int(
                    sample_rate * self.settings.gipformer_overlap_seconds
                )
                texts: list[str] = []
                for start, end in segments:
                    seg = samples[start:end]
                    if len(seg) > max_seg:
                        sub = _plan_windows(len(seg), max_seg, overlap_samples)
                        texts.append(
                            _merge_text_windows(
                                [
                                    self._decode_window(recognizer, sample_rate, seg[s:e])
                                    for s, e in sub
                                ]
                            )
                        )
                    else:
                        texts.append(self._decode_window(recognizer, sample_rate, seg))
                text = " ".join(part for part in texts if part).strip()
                return text, "vad", len(segments)
            mode = "overlap"  # degrade

        if mode == "fixed":
            windows = _plan_windows(len(samples), window_samples, 0)
            texts = [
                self._decode_window(recognizer, sample_rate, samples[s:e])
                for s, e in windows
            ]
            return " ".join(part for part in texts if part).strip(), "fixed", len(windows)

        # Default: overlap-and-merge.
        overlap_samples = int(sample_rate * self.settings.gipformer_overlap_seconds)
        windows = _plan_windows(len(samples), window_samples, overlap_samples)
        texts = [
            self._decode_window(recognizer, sample_rate, samples[s:e]) for s, e in windows
        ]
        return _merge_text_windows(texts), "overlap", len(windows)

    def _decode_window(self, recognizer, sample_rate, chunk) -> str:
        if len(chunk) == 0:
            return ""
        stream = recognizer.create_stream()
        stream.accept_waveform(sample_rate, chunk)
        recognizer.decode_streams([stream])
        return stream.result.text.strip()

    def _segments_from_vad(self, samples, sample_rate) -> list[tuple[int, int]] | None:
        """Return ``[(start_sample, end_sample), ...]`` speech regions, or ``None``.

        Returns ``None`` (so the caller degrades to overlap windows) when VAD is
        not configured or anything in the VAD path fails. Set ``GIPFORMER_VAD_MODEL``
        to ``repo_id:filename`` (e.g. a ``silero_vad.onnx``) or a local path.
        """

        spec = self.settings.gipformer_vad_model
        if not spec:
            logger.warning(
                "GIPFORMER_SEGMENTATION=vad needs GIPFORMER_VAD_MODEL "
                "(repo_id:filename or a local silero_vad.onnx path); using overlap"
            )
            return None
        try:
            import numpy as np  # type: ignore
            import sherpa_onnx  # type: ignore

            vad_sr = 16000
            signal = _resample_linear(np, samples, sample_rate, vad_sr)

            config = sherpa_onnx.VadModelConfig()
            config.silero_vad.model = self._vad_model_path(spec)
            config.silero_vad.threshold = 0.5
            config.silero_vad.min_silence_duration = 0.25
            config.silero_vad.min_speech_duration = 0.25
            config.sample_rate = vad_sr
            vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=30)

            spans_sec: list[tuple[float, float]] = []

            def _drain() -> None:
                while not vad.empty():
                    seg = vad.front
                    start_sec = seg.start / vad_sr
                    spans_sec.append((start_sec, start_sec + len(seg.samples) / vad_sr))
                    vad.pop()

            window = 512
            for index in range(0, len(signal), window):
                vad.accept_waveform(signal[index : index + window])
                _drain()
            vad.flush()
            _drain()

            if not spans_sec:
                return None
            return [
                (int(start * sample_rate), int(end * sample_rate))
                for start, end in spans_sec
            ]
        except Exception as exc:  # pragma: no cover - depends on VAD runtime
            logger.warning("Gipformer VAD unavailable (%s); using overlap windows", exc)
            return None

    def _vad_model_path(self, spec: str) -> str:
        if ":" in spec and not Path(spec).exists():
            repo_id, filename = spec.split(":", 1)
            from huggingface_hub import hf_hub_download  # type: ignore

            return hf_hub_download(repo_id=repo_id, filename=filename)
        return spec

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

    def warmup(self) -> dict[str, object]:
        return {"provider": "mock", "ready": self.allow}

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
