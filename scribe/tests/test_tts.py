"""Vietnamese speech synthesis: guardrails and the browser-fallback contract.

The real voice is a 63 MB download, so these tests inject a fake engine. One
opt-in test exercises the real model when it is already on disk.
"""

from __future__ import annotations

import os
import sys
import unittest
import wave
from io import BytesIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scribe"))

from carepath.services.tts import (
    DEFAULT_TTS_REPO,
    DisabledTTS,
    TTSError,
    VietnameseTTS,
    _to_wav_bytes,
    build_tts,
)


class _FakeAudio:
    def __init__(self, seconds: float = 0.5, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.samples = [0.0] * int(seconds * sample_rate)


class _FakeEngine:
    def __init__(self):
        self.calls = []

    def generate(self, text, sid=0, speed=1.0):
        self.calls.append((text, sid, speed))
        return _FakeAudio()


class _Settings:
    tts_provider = "piper"
    tts_repo_id = DEFAULT_TTS_REPO
    tts_model_dir = Path("models/vi-tts")
    gipformer_num_threads = 2


class WavEncodingTests(unittest.TestCase):
    def test_produces_a_readable_mono_16bit_wav(self) -> None:
        data = _to_wav_bytes([0.0, 0.5, -0.5, 1.0, -1.0], 22050)

        with wave.open(BytesIO(data), "rb") as handle:
            self.assertEqual(handle.getnchannels(), 1)
            self.assertEqual(handle.getsampwidth(), 2)
            self.assertEqual(handle.getframerate(), 22050)
            self.assertEqual(handle.getnframes(), 5)

    def test_clamps_out_of_range_samples_without_wrapping(self) -> None:
        """A sample above 1.0 must saturate, not overflow into a loud click."""
        data = _to_wav_bytes([9.0, -9.0], 22050)

        with wave.open(BytesIO(data), "rb") as handle:
            frames = handle.readframes(2)
        self.assertEqual(int.from_bytes(frames[0:2], "little", signed=True), 32767)
        self.assertEqual(int.from_bytes(frames[2:4], "little", signed=True), -32767)


class SynthesisGuardTests(unittest.TestCase):
    def _tts(self) -> tuple[VietnameseTTS, _FakeEngine]:
        tts = VietnameseTTS(model_dir=Path("models/vi-tts"))
        engine = _FakeEngine()
        tts._engine = engine
        return tts, engine

    def test_synthesizes_vietnamese(self) -> None:
        tts, engine = self._tts()

        audio, sample_rate = tts.synthesize("Bệnh nhân bị dị ứng amoxicillin")

        self.assertEqual(sample_rate, 22050)
        self.assertTrue(audio.startswith(b"RIFF"))
        self.assertEqual(engine.calls[0][0], "Bệnh nhân bị dị ứng amoxicillin")

    def test_rejects_empty_text(self) -> None:
        tts, _ = self._tts()
        with self.assertRaises(TTSError):
            tts.synthesize("   ")

    def test_rejects_oversized_text(self) -> None:
        tts, _ = self._tts()
        with self.assertRaises(TTSError):
            tts.synthesize("a" * 801)

    def test_engine_failure_becomes_ttserror(self) -> None:
        """So the endpoint answers 503 and the browser voice takes over."""
        tts = VietnameseTTS(model_dir=Path("models/vi-tts"))

        class Broken:
            def generate(self, *a, **k):
                raise RuntimeError("espeak data missing")

        tts._engine = Broken()
        with self.assertRaises(TTSError):
            tts.synthesize("xin chào")


class BuilderTests(unittest.TestCase):
    def test_piper_provider_builds_the_vietnamese_voice(self) -> None:
        self.assertIsInstance(build_tts(_Settings()), VietnameseTTS)

    def test_disabling_falls_back_to_the_browser(self) -> None:
        class Off(_Settings):
            tts_provider = "off"

        tts = build_tts(Off())
        self.assertIsInstance(tts, DisabledTTS)
        self.assertFalse(tts.readiness()[0])
        with self.assertRaises(TTSError):
            tts.synthesize("xin chào")


@unittest.skipUnless(
    os.getenv("CAREPATH_TTS_MODEL_DIR") and Path(os.environ["CAREPATH_TTS_MODEL_DIR"]).is_dir(),
    "set CAREPATH_TTS_MODEL_DIR to a downloaded voice to run the real synthesis test",
)
class RealVoiceTests(unittest.TestCase):
    def test_real_voice_speaks_a_clinical_sentence(self) -> None:
        tts = VietnameseTTS(model_dir=Path(os.environ["CAREPATH_TTS_MODEL_DIR"]))

        audio, sample_rate = tts.synthesize("Bệnh nhân bị dị ứng amoxicillin, uống 500 mg.")

        with wave.open(BytesIO(audio), "rb") as handle:
            seconds = handle.getnframes() / handle.getframerate()
        self.assertGreater(seconds, 1.0, "a full sentence should be over a second of audio")
        self.assertEqual(sample_rate, 22050)


if __name__ == "__main__":
    unittest.main()
