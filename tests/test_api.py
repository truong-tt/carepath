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

    def setUp(self) -> None:
        get_settings.cache_clear()
        main_module._rate_limit_events.clear()
        main_module._global_rate_limit_events.clear()

    def _post_wav(self, headers: dict[str, str] | None = None):
        return self.client.post(
            "/api/v1/soap-notes",
            files={"audio": ("demo.wav", _silent_wav_bytes(), "audio/wav")},
            headers=headers or {},
        )

    def test_valid_wav_is_accepted(self) -> None:
        response = self._post_wav()
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

    def test_startup_warms_pipeline(self) -> None:
        calls: list[bool] = []

        class FakePipeline:
            def warmup(self) -> dict[str, object]:
                calls.append(True)
                return {"asr": {"ready": True}}

        with patch.object(main_module, "get_pipeline", return_value=FakePipeline()):
            main_module._warmup_pipeline()

        self.assertEqual(calls, [True])

    def test_fourth_request_from_same_ip_is_rate_limited(self) -> None:
        with patch.dict(
            os.environ,
            {
                "TEAM_CODE": "",
                "SOAP_RATE_LIMIT_PER_IP_HOUR": "3",
                "SOAP_RATE_LIMIT_PER_IP_DAY": "10",
                "SOAP_RATE_LIMIT_GLOBAL_DAY": "100",
            },
            clear=False,
        ):
            get_settings.cache_clear()
            headers = {"X-Forwarded-For": "203.0.113.10"}
            responses = [self._post_wav(headers=headers) for _ in range(4)]

        self.assertEqual(
            [response.status_code for response in responses[:3]],
            [200, 200, 200],
        )
        self.assertEqual(responses[3].status_code, 429)
        self.assertIn("Retry-After", responses[3].headers)
        self.assertIn("giới hạn demo", responses[3].json()["detail"]["message"])

    def test_team_code_bypasses_limits(self) -> None:
        with patch.dict(
            os.environ,
            {
                "TEAM_CODE": "letmein",
                "SOAP_RATE_LIMIT_PER_IP_HOUR": "1",
                "SOAP_RATE_LIMIT_PER_IP_DAY": "1",
                "SOAP_RATE_LIMIT_GLOBAL_DAY": "1",
            },
            clear=False,
        ):
            get_settings.cache_clear()
            headers = {"X-Forwarded-For": "203.0.113.11", "X-Team-Code": "letmein"}
            responses = [self._post_wav(headers=headers) for _ in range(3)]

        self.assertEqual(
            [response.status_code for response in responses],
            [200, 200, 200],
        )

    def test_wrong_team_code_is_limited_like_anonymous(self) -> None:
        with patch.dict(
            os.environ,
            {
                "TEAM_CODE": "letmein",
                "SOAP_RATE_LIMIT_PER_IP_HOUR": "1",
                "SOAP_RATE_LIMIT_PER_IP_DAY": "10",
                "SOAP_RATE_LIMIT_GLOBAL_DAY": "100",
            },
            clear=False,
        ):
            get_settings.cache_clear()
            headers = {"X-Forwarded-For": "203.0.113.12", "X-Team-Code": "wrong"}
            first = self._post_wav(headers=headers)
            second = self._post_wav(headers=headers)

        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(second.status_code, 429)

    def test_global_daily_cap_limits_all_ips(self) -> None:
        with patch.dict(
            os.environ,
            {
                "TEAM_CODE": "",
                "SOAP_RATE_LIMIT_PER_IP_HOUR": "10",
                "SOAP_RATE_LIMIT_PER_IP_DAY": "10",
                "SOAP_RATE_LIMIT_GLOBAL_DAY": "2",
            },
            clear=False,
        ):
            get_settings.cache_clear()
            first = self._post_wav(headers={"X-Forwarded-For": "203.0.113.13"})
            second = self._post_wav(headers={"X-Forwarded-For": "203.0.113.14"})
            third = self._post_wav(headers={"X-Forwarded-For": "203.0.113.15"})

        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(second.status_code, 200, second.text)
        self.assertEqual(third.status_code, 429)
        self.assertIn("giới hạn sử dụng trong ngày", third.json()["detail"]["message"])


if __name__ == "__main__":
    unittest.main()
