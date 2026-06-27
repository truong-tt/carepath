from __future__ import annotations

import contextlib
import sys
import tempfile
import unittest
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from carepath.services.audio import normalize_audio


class AudioTests(unittest.TestCase):
    def test_stdlib_fallback_converts_stereo_pcm16_to_mono(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.wav"
            output_path = Path(temp_dir) / "output.wav"
            with contextlib.closing(wave.open(str(input_path), "wb")) as writer:
                writer.setnchannels(2)
                writer.setsampwidth(2)
                writer.setframerate(16000)
                frames = bytearray()
                for _ in range(8):
                    frames.extend((1000).to_bytes(2, "little", signed=True))
                    frames.extend((3000).to_bytes(2, "little", signed=True))
                writer.writeframes(bytes(frames))

            normalize_audio(input_path, output_path)

            with contextlib.closing(wave.open(str(output_path), "rb")) as reader:
                self.assertEqual(reader.getnchannels(), 1)
                self.assertEqual(reader.getsampwidth(), 2)
                self.assertEqual(reader.getframerate(), 16000)
                first_sample = int.from_bytes(reader.readframes(1), "little", signed=True)
                self.assertEqual(first_sample, 2000)


if __name__ == "__main__":
    unittest.main()

