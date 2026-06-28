from __future__ import annotations

import contextlib
import io
import os
import sys
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

# Hermetic config: mock ASR + offline LLM, and do not read the real .env.
os.environ.setdefault("ASR_PROVIDER", "mock")
os.environ.setdefault("ALLOW_MOCK_ASR", "true")
os.environ.setdefault("LLM_PROVIDER", "offline")
os.environ.setdefault("MEDICAL_LEXICON_PATH", str(REPO_ROOT / "data" / "medical_lexicon.json"))
os.environ.setdefault("CAREPATH_ENV_FILE", "__tests_no_env__")

from fastapi.testclient import TestClient

import carepath.main as main_module
from carepath.main import app, get_pipeline, get_settings


def _silent_wav_bytes(seconds: int = 1) -> bytes:
    buffer = io.BytesIO()
    with contextlib.closing(wave.open(buffer, "wb")) as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(16000)
        writer.writeframes(b"\x00\x00" * 16000 * seconds)
    return buffer.getvalue()


class UploadGuardrailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        get_settings.cache_clear()
        get_pipeline.cache_clear()
        cls.client = TestClient(app)

    def test_valid_wav_is_accepted(self) -> None:
        response = self.client.post(
            "/api/v1/soap-notes",
            files={"audio": ("demo.wav", _silent_wav_bytes(), "audio/wav")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["soap"]["review_required"])

    def test_unsupported_file_type_is_rejected(self) -> None:
        response = self.client.post(
            "/api/v1/soap-notes",
            files={"audio": ("notes.txt", b"not audio", "text/plain")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported file type", response.json()["detail"])

    def test_oversized_upload_is_rejected(self) -> None:
        with patch.object(main_module, "MAX_UPLOAD_BYTES", 1024):
            response = self.client.post(
                "/api/v1/soap-notes",
                files={"audio": ("big.wav", b"\x00" * 4096, "audio/wav")},
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn("too large", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
