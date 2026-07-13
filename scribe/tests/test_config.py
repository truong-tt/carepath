from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from carepath.config import Settings, load_env_file


class ConfigTests(unittest.TestCase):
    def test_load_env_file_does_not_override_existing_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "ASR_PROVIDER=mock\nLLM_PROVIDER=offline\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"ASR_PROVIDER": "gipformer"}, clear=False):
                os.environ.pop("LLM_PROVIDER", None)
                load_env_file(env_path)

                self.assertEqual(os.environ["ASR_PROVIDER"], "gipformer")
                self.assertEqual(os.environ["LLM_PROVIDER"], "offline")

    def test_ckey_provider_gets_ckey_defaults(self) -> None:
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "ckey",
            },
            clear=True,
        ):
            settings = Settings.from_env()

        self.assertEqual(settings.llm_provider, "ckey")
        self.assertEqual(settings.llm_base_url, "https://api.xah.io/v1")
        self.assertEqual(settings.llm_model, "gpt-5.4")
        self.assertEqual(settings.gipformer_chunk_seconds, 20.0)

    def test_cors_origins_are_comma_separated(self) -> None:
        with patch.dict(
            os.environ,
            {
                "CORS_ORIGINS": "https://carepath.vercel.app, http://localhost:3000/ ,,",
            },
            clear=True,
        ):
            settings = Settings.from_env()

        self.assertEqual(
            settings.cors_origins,
            ("https://carepath.vercel.app", "http://localhost:3000"),
        )

    def test_abuse_guard_defaults(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings.from_env()

        self.assertIsNone(settings.team_code)
        self.assertEqual(settings.soap_rate_limit_per_ip_hour, 3)
        self.assertEqual(settings.soap_rate_limit_per_ip_day, 10)
        self.assertEqual(settings.soap_rate_limit_global_day, 100)


if __name__ == "__main__":
    unittest.main()
