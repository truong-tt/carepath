"""Reading a photographed Vietnamese medical document into confirmable turns.

The point of this path: harm for limited-English-proficiency patients
concentrates at medication reconciliation and discharge, which happen on paper.
The vision model only transcribes -- the risk engine, not the model, decides
whether a line is dangerous.
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scribe"))
sys.path.insert(0, str(REPO_ROOT / "interpreter"))

os.environ.setdefault("ASR_PROVIDER", "mock")
os.environ.setdefault("ALLOW_MOCK_ASR", "true")
os.environ.setdefault("LLM_PROVIDER", "offline")
os.environ.setdefault("MEDICAL_LEXICON_PATH", str(REPO_ROOT / "data" / "medical_lexicon.json"))
os.environ.setdefault("CAREPATH_ENV_FILE", "__tests_no_env__")
# setdefault, never assignment: these modules share a process, and pinning a
# mode here leaks into every other test module that imports the app.
os.environ.setdefault("PROVIDER_MODE", "mock")
_TMP_DB = Path(tempfile.mkdtemp(prefix="carepath_docs_")) / "docs.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB.as_posix()}"

from fastapi.testclient import TestClient

import app.config as interpreter_config
import app.db as interpreter_db
from app.providers.base import ProviderOutputError
from app.providers.ckey import CKeyChatClient, parse_document_lines, read_document_lines
from app.providers.registry import read_document
from app.config import Settings
from carepath.main import app, get_pipeline, get_settings

PNG_1PX = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06"
    b"\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05"
    b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


class FakeResponse:
    def __init__(self, content: str) -> None:
        self._body = json.dumps({"choices": [{"message": {"content": content}}]}).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *exc: object) -> None:
        return None


class RecordingOpener:
    def __init__(self, content: str) -> None:
        self.content = content
        self.requests: list[dict] = []

    def __call__(self, request, timeout=None):
        self.requests.append(json.loads(request.data.decode("utf-8")))
        return FakeResponse(self.content)


class ParseTests(unittest.TestCase):
    def test_parses_lines(self) -> None:
        lines = parse_document_lines('{"lines": ["Amoxicillin 500mg", "  ngày 2 lần  "]}')
        self.assertEqual(lines, ["Amoxicillin 500mg", "ngày 2 lần"])

    def test_unreadable_document_yields_nothing(self) -> None:
        """Fail closed: better zero lines than a guess at what a prescription says."""
        self.assertEqual(parse_document_lines('{"lines": []}'), [])

    def test_accepts_fenced_json(self) -> None:
        self.assertEqual(parse_document_lines('```json\n{"lines": ["a"]}\n```'), ["a"])

    def test_rejects_prose_or_extra_keys(self) -> None:
        for bad in [
            '{"lines": ["a"], "summary": "a prescription"}',
            '{"text": "Amoxicillin"}',
            '{"lines": "Amoxicillin"}',
            '{"lines": [{"text": "a"}]}',
            "The document says Amoxicillin 500mg",
        ]:
            with self.assertRaises(ProviderOutputError, msg=bad):
                parse_document_lines(bad)


class VisionRequestTests(unittest.TestCase):
    def test_image_is_sent_as_a_data_uri_alongside_the_prompt(self) -> None:
        opener = RecordingOpener('{"lines": ["Amoxicillin 500mg"]}')
        client = CKeyChatClient(
            api_key="sk-test",
            base_url="https://example.test/v1",
            model="gpt-5.4",
            opener=opener,
            backoff_seconds=0,
        )

        lines = read_document_lines(client, PNG_1PX, "image/png")

        self.assertEqual(lines, ["Amoxicillin 500mg"])
        content = opener.requests[0]["messages"][1]["content"]
        self.assertEqual(content[0]["type"], "text")
        self.assertEqual(content[1]["type"], "image_url")
        self.assertTrue(content[1]["image_url"]["url"].startswith("data:image/png;base64,"))
        system = opener.requests[0]["messages"][0]["content"]
        self.assertIn("Do not translate", system)


class ModeTests(unittest.TestCase):
    def test_modes_without_vision_fail_closed(self) -> None:
        """Silence would read as 'the document was blank'. Raise instead."""
        for mode in ("mock", "cloud"):
            with self.assertRaises(RuntimeError, msg=mode):
                read_document(Settings(provider_mode=mode), PNG_1PX, "image/png")

    def test_demo_mode_replays_a_scripted_prescription(self) -> None:
        lines = read_document(Settings(provider_mode="demo"), PNG_1PX, "image/png")
        self.assertTrue(any("Amoxicillin" in line for line in lines))


class EndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        get_settings.cache_clear()
        get_pipeline.cache_clear()
        interpreter_config.get_settings.cache_clear()
        interpreter_db.set_engine(None)

    def _visit(self, client) -> str:
        return client.post("/api/sessions", json={"consent": {"ok": True}}).json()["session_id"]

    def _upload(self, client, visit_id, data=PNG_1PX, filename="donthuoc.png", ctype="image/png"):
        return client.post(
            f"/api/v1/visits/{visit_id}/documents",
            files={"image": (filename, io.BytesIO(data), ctype)},
        )

    def test_document_lines_become_gated_turns(self) -> None:
        prescription = read_document(Settings(provider_mode="demo"), PNG_1PX, "image/png")
        with TestClient(app) as client:
            visit_id = self._visit(client)

            # Patch the reader rather than pinning PROVIDER_MODE for the process.
            with patch("carepath.main.read_document", return_value=prescription):
                response = self._upload(client, visit_id)

            self.assertEqual(response.status_code, 200, response.text)
            turns = response.json()
            self.assertTrue(turns)
            self.assertTrue(all(turn["speaker"] == "document" for turn in turns))

            # The risk engine, not the vision model, decides this is risky.
            dosed = [
                turn
                for turn in turns
                if any(span["kind"] == "dose_number" for span in turn["risk_spans"])
            ]
            self.assertTrue(dosed, "a prescription line with a dose should be detected")
            self.assertEqual(dosed[0]["status"], "awaiting_confirm")

            # They are ordinary turns, so they appear in the visit transcript.
            transcript = client.get(f"/api/sessions/{visit_id}/transcript").json()
            self.assertEqual(len(transcript), len(turns))

    def test_sample_header_reads_the_scripted_document_whatever_was_uploaded(self) -> None:
        """The public demo's sample path, which the page labels as scripted.

        `demo` mode never looks at the bytes. That is honest for a sample and
        would be a fabrication for a visitor's own prescription, so the header
        exists to make the distinction explicit at the call site.
        """
        with TestClient(app) as client:
            visit_id = self._visit(client)
            response = client.post(
                f"/api/v1/visits/{visit_id}/documents",
                files={"image": ("anything.png", io.BytesIO(PNG_1PX), "image/png")},
                headers={"X-CarePath-Sample": "1"},
            )

            self.assertEqual(response.status_code, 200, response.text)
            turns = response.json()
            self.assertTrue(any("Amoxicillin" in turn["source_text"] for turn in turns))

    def test_sample_mode_still_gates_the_risky_lines(self) -> None:
        """Scripted translation, real gate. If the demo showed a dose straight
        to the patient pane it would be advertising the opposite of the product.
        """
        with TestClient(app) as client:
            visit_id = self._visit(client)
            turns = client.post(
                f"/api/v1/visits/{visit_id}/documents",
                files={"image": ("anything.png", io.BytesIO(PNG_1PX), "image/png")},
                headers={"X-CarePath-Sample": "1"},
            ).json()

            dosed = [
                turn
                for turn in turns
                if any(span["kind"] == "dose_number" for span in turn["risk_spans"])
            ]
            self.assertTrue(dosed, "the scripted prescription must carry a dose line")
            for turn in dosed:
                self.assertEqual(turn["status"], "awaiting_confirm")

    def test_without_the_header_the_configured_mode_still_applies(self) -> None:
        """The header opts in. It must not become the default by accident: this
        process runs PROVIDER_MODE=mock, which has no vision and fails closed.
        """
        with TestClient(app) as client:
            visit_id = self._visit(client)
            self.assertEqual(self._upload(client, visit_id).status_code, 502)

    def test_rejects_a_non_image_upload(self) -> None:
        with TestClient(app) as client:
            visit_id = self._visit(client)
            response = self._upload(
                client, visit_id, data=b"not an image", filename="notes.txt", ctype="text/plain"
            )
            self.assertEqual(response.status_code, 400)

    def test_rejects_an_empty_upload(self) -> None:
        with TestClient(app) as client:
            visit_id = self._visit(client)
            self.assertEqual(self._upload(client, visit_id, data=b"").status_code, 400)

    def test_unknown_visit_is_404(self) -> None:
        with TestClient(app) as client:
            self.assertEqual(self._upload(client, "nope").status_code, 404)

    def test_reader_failure_is_502_and_creates_no_turns(self) -> None:
        with TestClient(app) as client:
            visit_id = self._visit(client)
            with patch("carepath.main.read_document", side_effect=RuntimeError("gateway down")):
                response = self._upload(client, visit_id)

            self.assertEqual(response.status_code, 502)
            self.assertEqual(client.get(f"/api/sessions/{visit_id}/transcript").json(), [])

    def test_failure_message_does_not_leak_internals(self) -> None:
        with TestClient(app) as client:
            visit_id = self._visit(client)
            with patch(
                "carepath.main.read_document",
                side_effect=RuntimeError("sk-secret leaked and Tôi bị dị ứng"),
            ):
                response = self._upload(client, visit_id)
            self.assertNotIn("sk-secret", response.text)
            self.assertNotIn("dị ứng", response.text)


if __name__ == "__main__":
    unittest.main()
