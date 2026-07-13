"""The combined service serves both products: scriber /api/v1/* and
interpreter /api/* + /ws/* from one FastAPI app with one lifespan."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scribe"))
sys.path.insert(0, str(REPO_ROOT / "interpreter"))

# Hermetic keyless config for both products (same pattern as test_api.py).
os.environ.setdefault("ASR_PROVIDER", "mock")
os.environ.setdefault("ALLOW_MOCK_ASR", "true")
os.environ.setdefault("LLM_PROVIDER", "offline")
os.environ.setdefault("MEDICAL_LEXICON_PATH", str(REPO_ROOT / "data" / "medical_lexicon.json"))
os.environ.setdefault("CAREPATH_ENV_FILE", "__tests_no_env__")
os.environ.setdefault("PROVIDER_MODE", "mock")
_TMP_DB = Path(tempfile.mkdtemp(prefix="carepath_combined_")) / "combined.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB.as_posix()}"

from fastapi.testclient import TestClient

import app.config as interpreter_config
import app.db as interpreter_db
from carepath.main import SITE_DIST_DIR, app, get_pipeline, get_settings


class CombinedAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        get_settings.cache_clear()
        get_pipeline.cache_clear()
        interpreter_config.get_settings.cache_clear()
        interpreter_db.set_engine(None)

    def test_lifespan_boots_both_products_and_serves_both_apis(self) -> None:
        # The context manager runs the combined lifespan: scriber warmup plus
        # interpreter init_db/seed_glossary/purge.
        with TestClient(app) as client:
            scriber_health = client.get("/api/v1/health")
            self.assertEqual(scriber_health.status_code, 200, scriber_health.text)
            self.assertEqual(scriber_health.json()["asr_provider"], "mock")

            interpreter_health = client.get("/api/health")
            self.assertEqual(interpreter_health.status_code, 200, interpreter_health.text)
            self.assertEqual(interpreter_health.json()["provider_mode"], "mock")

            created = client.post(
                "/api/sessions",
                json={"consent": {"language": "vi", "accepted": True}},
            )
            self.assertEqual(created.status_code, 201, created.text)
            session_id = created.json()["session_id"]

            with client.websocket_connect(f"/ws/sessions/{session_id}") as websocket:
                snapshot = websocket.receive_json()
                self.assertEqual(snapshot["type"], "session_state")
                self.assertEqual(snapshot["turns"], [])

    @unittest.skipUnless(SITE_DIST_DIR.is_dir(), "site build is not available")
    def test_clinical_notes_route_serves_the_site_entrypoint(self) -> None:
        with TestClient(app) as client:
            response = client.get("/ghi-chep-lam-sang/")

        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn('id="root"', response.text)

    def test_public_interpreter_browser_paths_are_blocked(self) -> None:
        with TestClient(app) as client:
            responses = [
                client.get("/phien-dich-y-khoa/"),
                client.get("/phien-dich-y-khoa/assets/index.js"),
                client.get("/console"),
                client.get("/console/?lang=en"),
            ]

        for response in responses:
            self.assertEqual(response.status_code, 404, response.text)


if __name__ == "__main__":
    unittest.main()
