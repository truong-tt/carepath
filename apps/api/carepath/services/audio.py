from __future__ import annotations

import contextlib
import wave
from pathlib import Path


class AudioNormalizationError(RuntimeError):
    """Raised when the uploaded audio cannot be normalized for ASR."""


def normalize_audio(input_path: Path, output_path: Path) -> Path:
    """Write mono audio to ``output_path`` and return it.

    The preferred path uses soundfile because Gipformer supports a broad set of
    formats through libsndfile. A small stdlib WAV fallback keeps tests and
    simple PCM demo clips working before optional ML/audio wheels are installed.
    """

    try:
        import soundfile as sf  # type: ignore
    except ImportError:
        _normalize_pcm_wav_with_stdlib(input_path, output_path)
        return output_path

    try:
        samples, sample_rate = sf.read(str(input_path), dtype="float32")
    except Exception as exc:  # pragma: no cover - depends on libsndfile
        raise AudioNormalizationError(f"Could not read audio file: {exc}") from exc

    try:
        import numpy as np  # type: ignore

        if getattr(samples, "ndim", 1) > 1:
            samples = np.mean(samples, axis=1)
    except ImportError:
        if isinstance(samples, list) and samples and isinstance(samples[0], list):
            samples = [sum(frame) / len(frame) for frame in samples]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        sf.write(str(output_path), samples, sample_rate)
    except Exception as exc:  # pragma: no cover - depends on libsndfile
        raise AudioNormalizationError(f"Could not write normalized audio: {exc}") from exc
    return output_path


def _normalize_pcm_wav_with_stdlib(input_path: Path, output_path: Path) -> None:
    try:
        with contextlib.closing(wave.open(str(input_path), "rb")) as reader:
            channels = reader.getnchannels()
            sample_width = reader.getsampwidth()
            frame_rate = reader.getframerate()
            frame_count = reader.getnframes()
            frames = reader.readframes(frame_count)
    except Exception as exc:
        raise AudioNormalizationError(
            "soundfile is not installed and the file is not a readable PCM WAV"
        ) from exc

    if channels == 1:
        mono_frames = frames
    elif sample_width == 2:
        mono_frames = _stereo_pcm16_to_mono(frames)
    else:
        raise AudioNormalizationError(
            "stdlib fallback only supports mono WAV or stereo 16-bit PCM WAV"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with contextlib.closing(wave.open(str(output_path), "wb")) as writer:
        writer.setnchannels(1)
        writer.setsampwidth(sample_width)
        writer.setframerate(frame_rate)
        writer.writeframes(mono_frames)


def _stereo_pcm16_to_mono(frames: bytes) -> bytes:
    out = bytearray()
    for idx in range(0, len(frames), 4):
        left = int.from_bytes(frames[idx : idx + 2], "little", signed=True)
        right = int.from_bytes(frames[idx + 2 : idx + 4], "little", signed=True)
        mixed = int((left + right) / 2)
        out.extend(mixed.to_bytes(2, "little", signed=True))
    return bytes(out)

