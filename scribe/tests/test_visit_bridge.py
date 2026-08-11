"""The bilingual visit bridge: interpreted turns become both end-of-visit documents.

Runs the real Interpreter websocket pipeline and the real Scribe pipeline in one
process, keyless, exactly as the combined app does in production.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scribe"))
sys.path.insert(0, str(REPO_ROOT / "interpreter"))

os.environ.setdefault("ASR_PROVIDER", "mock")
os.environ.setdefault("ALLOW_MOCK_ASR", "true")
os.environ.setdefault("LLM_PROVIDER", "offline")
os.environ.setdefault("MEDICAL_LEXICON_PATH", str(REPO_ROOT / "data" / "medical_lexicon.json"))
os.environ.setdefault("CAREPATH_ENV_FILE", "__tests_no_env__")
os.environ.setdefault("PROVIDER_MODE", "mock")
_TMP_DB = Path(tempfile.mkdtemp(prefix="carepath_visit_")) / "visit.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB.as_posix()}"

from fastapi.testclient import TestClient

import app.config as interpreter_config
import app.db as interpreter_db
from carepath.main import _render_visit_transcript, app, get_pipeline, get_settings


class _Turn:
    """Minimal stand-in for TurnRecord, for the pure rendering rules."""

    def __init__(self, speaker, src_lang, source_text, translation, status, corrected_text=None):
        self.speaker = speaker
        self.src_lang = src_lang
        self.source_text = source_text
        self.translation = translation
        self.status = status
        self.corrected_text = corrected_text


class VisitTranscriptRenderingTests(unittest.TestCase):
    """Source speech is always usable; a translation only once it is confirmed."""

    def test_source_language_turns_always_use_what_was_said(self) -> None:
        turns = [_Turn("doctor", "vi", "Ngừng thuốc này", "Stop this medicine", "awaiting_confirm")]

        vietnamese, withheld = _render_visit_transcript(turns, "vi")

        self.assertIn("Bác sĩ: Ngừng thuốc này", vietnamese)
        self.assertEqual(withheld, 0, "the clinician's own words were never in doubt")

    def test_unconfirmed_translation_is_withheld_and_counted(self) -> None:
        turns = [_Turn("doctor", "vi", "Ngừng thuốc này", "Stop this medicine", "awaiting_confirm")]

        english, withheld = _render_visit_transcript(turns, "en")

        self.assertEqual(english, "")
        self.assertEqual(withheld, 1)
        self.assertNotIn("Stop this medicine", english)

    def test_blocked_translation_is_withheld(self) -> None:
        turns = [_Turn("patient", "en", "I take 15 mg", "Tôi uống 15 mg", "blocked")]

        vietnamese, withheld = _render_visit_transcript(turns, "vi")

        self.assertEqual(withheld, 1)
        self.assertNotIn("15 mg", vietnamese)

    def test_confirmed_edit_wins_over_the_raw_translation(self) -> None:
        turns = [
            _Turn(
                "patient",
                "en",
                "I take 15 mg",
                "Tôi uống 15 mg",
                "corrected",
                corrected_text="Tôi uống 500 mg",
            )
        ]

        vietnamese, withheld = _render_visit_transcript(turns, "vi")

        self.assertIn("500 mg", vietnamese)
        self.assertNotIn("15 mg", vietnamese)
        self.assertEqual(withheld, 0)

    def test_every_speaker_has_a_label_in_both_languages(self) -> None:
        """The fallback is the raw key, and 'document:' reads as a bug to a patient."""
        from carepath.main import SPEAKER_LABELS

        for language in ("vi", "en"):
            for speaker in ("doctor", "patient", "document"):
                self.assertIn(speaker, SPEAKER_LABELS[language])
                self.assertNotEqual(SPEAKER_LABELS[language][speaker], speaker)

    def test_delivered_low_risk_turns_need_no_confirmation(self) -> None:
        turns = [_Turn("patient", "en", "Good morning", "Chào buổi sáng", "delivered")]

        vietnamese, withheld = _render_visit_transcript(turns, "vi")

        self.assertIn("Bệnh nhân: Chào buổi sáng", vietnamese)
        self.assertEqual(withheld, 0)


class VisitBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        get_settings.cache_clear()
        get_pipeline.cache_clear()
        interpreter_config.get_settings.cache_clear()
        interpreter_db.set_engine(None)

    def _start_visit(self, client) -> str:
        created = client.post(
            "/api/sessions",
            json={
                "consent": {
                    "ai_disclosure": True,
                    "interpreter_right": True,
                    "patient_context": {"age": 34, "sex": "nam", "reason": "nổi mẩn da"},
                }
            },
        )
        self.assertEqual(created.status_code, 201, created.text)
        return created.json()["session_id"]

    def test_visit_produces_both_documents(self) -> None:
        with TestClient(app) as client:
            visit_id = self._start_visit(client)

            with client.websocket_connect(f"/ws/sessions/{visit_id}") as ws:
                ws.receive_json()
                for speaker, lang, text in [
                    ("patient", "en", "I developed a rash after taking amoxicillin"),
                    ("doctor", "vi", "Bác sĩ sẽ ngừng thuốc này"),
                ]:
                    ws.send_json(
                        {"type": "text_turn", "speaker": speaker, "lang": lang, "text": text}
                    )
                    ws.receive_json()

            response = client.post(f"/api/v1/visits/{visit_id}/note")

            self.assertEqual(response.status_code, 200, response.text)
            body = response.json()
            self.assertEqual(body["visit_id"], visit_id)
            self.assertEqual(body["turn_count"], 2)
            self.assertTrue(body["clinical_note"]["review_required"])
            self.assertTrue(body["patient_summary"]["review_required"])
            self.assertIn("amoxicillin", body["patient_summary"]["what_we_discussed"])

    def test_unconfirmed_turn_is_counted_and_its_translation_excluded(self) -> None:
        with TestClient(app) as client:
            visit_id = self._start_visit(client)

            with client.websocket_connect(f"/ws/sessions/{visit_id}") as ws:
                ws.receive_json()
                # A dose is high risk, so this turn is gated awaiting confirmation.
                ws.send_json(
                    {
                        "type": "text_turn",
                        "speaker": "patient",
                        "lang": "en",
                        "text": "I was taking 500 mg twice a day",
                    }
                )
                result = ws.receive_json()
                self.assertTrue(result["requires_confirmation"])

            response = client.post(f"/api/v1/visits/{visit_id}/note")

            self.assertEqual(response.status_code, 200, response.text)
            body = response.json()
            self.assertEqual(body["unconfirmed_turn_count"], 1)
            # The gated turn's machine translation must not reach either document.
            documents = " ".join(
                str(value)
                for section in ("clinical_note", "patient_summary")
                for value in body[section].values()
            )
            self.assertNotIn("[en->vi]", documents)

    def test_confirmed_turn_reaches_the_clinical_note(self) -> None:
        with TestClient(app) as client:
            visit_id = self._start_visit(client)

            with client.websocket_connect(f"/ws/sessions/{visit_id}") as ws:
                ws.receive_json()
                ws.send_json(
                    {
                        "type": "text_turn",
                        "speaker": "patient",
                        "lang": "en",
                        "text": "I was taking 500 mg twice a day",
                    }
                )
                turn_id = ws.receive_json()["turn"]["id"]

            confirmed = client.post(
                f"/api/turns/{turn_id}/confirm",
                json={"edited_translation": "Bệnh nhân uống 500 mg, ngày hai lần"},
            )
            self.assertEqual(confirmed.status_code, 200, confirmed.text)

            body = client.post(f"/api/v1/visits/{visit_id}/note").json()

            self.assertEqual(body["unconfirmed_turn_count"], 0)
            joined = " ".join(str(value) for value in body["clinical_note"].values())
            self.assertIn("500 mg", joined)

    def test_confirmed_prescription_lines_become_the_patient_medication_list(self) -> None:
        """Not generated: the patient's instructions are the confirmed translation."""
        with TestClient(app) as client:
            visit_id = self._start_visit(client)

            with client.websocket_connect(f"/ws/sessions/{visit_id}") as ws:
                ws.receive_json()
                ws.send_json(
                    {
                        "type": "text_turn",
                        "speaker": "document",
                        "lang": "vi",
                        "text": "Amoxicillin 500 mg Uống 1 viên, ngày 2 lần",
                    }
                )
                turn_id = ws.receive_json()["turn"]["id"]

            confirmed = client.post(
                f"/api/turns/{turn_id}/confirm",
                json={"edited_translation": "Amoxicillin 500 mg - take 1 tablet twice a day"},
            )
            self.assertEqual(confirmed.status_code, 200, confirmed.text)

            body = client.post(f"/api/v1/visits/{visit_id}/note").json()

            self.assertIn(
                "Amoxicillin 500 mg - take 1 tablet twice a day",
                body["patient_summary"]["medications"],
            )

    def test_follow_up_advice_is_not_filed_as_a_medication(self) -> None:
        """A frequency alone is not a medicine: 'come back in 5 days' carries one."""
        with TestClient(app) as client:
            visit_id = self._start_visit(client)

            with client.websocket_connect(f"/ws/sessions/{visit_id}") as ws:
                ws.receive_json()
                ws.send_json(
                    {
                        "type": "text_turn",
                        "speaker": "document",
                        "lang": "vi",
                        "text": "Lời dặn: Uống nhiều nước. Tái khám sau 5 ngày.",
                    }
                )
                turn_id = ws.receive_json()["turn"]["id"]

            client.post(
                f"/api/turns/{turn_id}/confirm",
                json={"edited_translation": "Advice: drink water. Follow-up after 5 days."},
            )
            body = client.post(f"/api/v1/visits/{visit_id}/note").json()

            self.assertNotIn("Follow-up after 5 days", body["patient_summary"]["medications"])

    def test_unconfirmed_prescription_lines_stay_out_of_the_medication_list(self) -> None:
        with TestClient(app) as client:
            visit_id = self._start_visit(client)

            with client.websocket_connect(f"/ws/sessions/{visit_id}") as ws:
                ws.receive_json()
                # A dose is high risk, so this line is gated.
                ws.send_json(
                    {
                        "type": "text_turn",
                        "speaker": "document",
                        "lang": "vi",
                        "text": "Amoxicillin 500 mg Uống 1 viên, ngày 2 lần",
                    }
                )
                self.assertTrue(ws.receive_json()["requires_confirmation"])
                # Something ungated so the visit still has content to document.
                ws.send_json(
                    {"type": "text_turn", "speaker": "patient", "lang": "en", "text": "Thank you"}
                )
                ws.receive_json()

            body = client.post(f"/api/v1/visits/{visit_id}/note").json()

            self.assertNotIn("Amoxicillin", body["patient_summary"]["medications"])
            self.assertGreaterEqual(body["unconfirmed_turn_count"], 1)

    def test_unknown_visit_is_404(self) -> None:
        with TestClient(app) as client:
            response = client.post("/api/v1/visits/does-not-exist/note")
            self.assertEqual(response.status_code, 404)

    def test_visit_without_turns_is_400(self) -> None:
        with TestClient(app) as client:
            visit_id = self._start_visit(client)
            response = client.post(f"/api/v1/visits/{visit_id}/note")
            self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
