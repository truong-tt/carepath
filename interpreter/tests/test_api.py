import logging

import anyio
from fastapi.testclient import TestClient

import app.api as api_module
from app import crud
from app.api import websocket_session
from app.config import Settings
from app.main import app
from app.providers.mock import MockASRProvider, MockMTProvider, MockReviewerProvider
from app.providers.registry import ProviderSet


class DisconnectOnInitialState:
    accepted = False

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, _payload: object) -> None:
        raise RuntimeError("client disconnected")


def test_websocket_ignores_disconnect_before_initial_state(db_session) -> None:
    session = crud.create_session(db_session, {"ok": True})
    websocket = DisconnectOnInitialState()

    anyio.run(websocket_session, websocket, session.id, db_session)

    assert websocket.accepted is True


def test_session_rest_and_websocket_text_turn(db_session) -> None:
    del db_session
    with TestClient(app) as client:
        session_response = client.post(
            "/api/sessions",
            json={"consent": {"ai_disclosure": True, "patient": "test"}},
        )
        assert session_response.status_code == 201
        session_id = session_response.json()["session_id"]

        with client.websocket_connect(f"/ws/sessions/{session_id}") as ws:
            assert ws.receive_json() == {"type": "session_state", "turns": []}
            ws.send_json(
                {
                    "type": "text_turn",
                    "speaker": "doctor",
                    "lang": "vi",
                    "text": "xin chao",
                }
            )
            result = ws.receive_json()

        assert result["type"] == "turn_result"
        assert result["requires_confirmation"] is False
        assert result["low_confidence"] is False
        assert result["turn"]["source_text"] == "xin chao"
        assert result["turn"]["translation"] == "[vi->en] xin chao"

        transcript = client.get(f"/api/sessions/{session_id}/transcript").json()
        assert len(transcript) == 1

        turn_id = transcript[0]["id"]
        confirm = client.post(f"/api/turns/{turn_id}/confirm", json={})
        assert confirm.status_code == 409

        feedback = client.post(
            f"/api/turns/{turn_id}/feedback",
            json={"reason": "other", "comment": "ok"},
        )
        assert feedback.status_code == 201


def test_websocket_rejects_overlapping_turns(db_session) -> None:
    del db_session
    with TestClient(app) as client:
        session_id = client.post("/api/sessions", json={"consent": {"ok": True}}).json()[
            "session_id"
        ]
        with client.websocket_connect(f"/ws/sessions/{session_id}") as ws:
            ws.receive_json()
            ws.send_json({"type": "start_turn", "speaker": "doctor", "lang": "vi"})
            ws.send_json({"type": "start_turn", "speaker": "patient", "lang": "en"})
            assert ws.receive_json() == {
                "type": "turn_error",
                "message": "turn already in progress",
                "retryable": True,
            }


def test_dropped_turn_does_not_block_reconnect(db_session) -> None:
    del db_session
    with TestClient(app) as client:
        session_id = client.post("/api/sessions", json={"consent": {"ok": True}}).json()[
            "session_id"
        ]
        with client.websocket_connect(f"/ws/sessions/{session_id}") as ws:
            ws.receive_json()
            ws.send_json({"type": "start_turn", "speaker": "doctor", "lang": "vi"})

        with client.websocket_connect(f"/ws/sessions/{session_id}") as ws:
            assert ws.receive_json() == {"type": "session_state", "turns": []}


def test_websocket_asr_failure_sends_error_and_keeps_socket(db_session, monkeypatch) -> None:
    del db_session
    monkeypatch.setattr(
        "app.api.get_providers",
        lambda settings: ProviderSet(
            asr=MockASRProvider(fail=True),
            mt=MockMTProvider(),
            reviewer=MockReviewerProvider(),
        ),
    )
    with TestClient(app) as client:
        session_id = client.post("/api/sessions", json={"consent": {"ok": True}}).json()[
            "session_id"
        ]
        with client.websocket_connect(f"/ws/sessions/{session_id}") as ws:
            ws.receive_json()
            ws.send_json({"type": "start_turn", "speaker": "doctor", "lang": "vi"})
            ws.send_bytes(b"xin chao")
            ws.send_json({"type": "end_turn"})
            assert ws.receive_json() == {
                "type": "turn_error",
                "message": "translation failed — retry or use typed fallback",
                "retryable": True,
                "failure_context": {
                    "speaker": "doctor",
                    "src_lang": "vi",
                    "tgt_lang": "en",
                    "source_text": None,
                    "translation": None,
                },
            }

            ws.send_json(
                {
                    "type": "text_turn",
                    "speaker": "doctor",
                    "lang": "vi",
                    "text": "xin chao",
                }
            )
            assert ws.receive_json()["type"] == "turn_result"


def test_websocket_mt_failure_sends_error_and_keeps_socket(db_session, monkeypatch) -> None:
    del db_session
    mt = MockMTProvider(fail=True)
    monkeypatch.setattr(
        "app.api.get_providers",
        lambda settings: ProviderSet(
            asr=MockASRProvider(),
            mt=mt,
            reviewer=MockReviewerProvider(),
        ),
    )
    with TestClient(app) as client:
        session_id = client.post("/api/sessions", json={"consent": {"ok": True}}).json()[
            "session_id"
        ]
        with client.websocket_connect(f"/ws/sessions/{session_id}") as ws:
            ws.receive_json()
            ws.send_json(
                {
                    "type": "text_turn",
                    "speaker": "doctor",
                    "lang": "vi",
                    "text": "xin chao",
                }
            )
            assert ws.receive_json() == {
                "type": "turn_error",
                "message": "translation failed — retry or use typed fallback",
                "retryable": True,
                "failure_context": {
                    "speaker": "doctor",
                    "src_lang": "vi",
                    "tgt_lang": "en",
                    "source_text": "xin chao",
                    "translation": None,
                },
            }

            mt.fail = False
            ws.send_json(
                {
                    "type": "text_turn",
                    "speaker": "doctor",
                    "lang": "vi",
                    "text": "xin chao",
                }
            )
            assert ws.receive_json()["type"] == "turn_result"


def test_websocket_rejects_new_turns_on_ended_session(db_session) -> None:
    del db_session
    with TestClient(app) as client:
        session_id = client.post("/api/sessions", json={"consent": {"ok": True}}).json()[
            "session_id"
        ]
        assert client.post(f"/api/sessions/{session_id}/end").status_code == 204
        with client.websocket_connect(f"/ws/sessions/{session_id}") as ws:
            ws.receive_json()
            ws.send_json(
                {
                    "type": "text_turn",
                    "speaker": "doctor",
                    "lang": "vi",
                    "text": "xin chao",
                }
            )
            assert ws.receive_json() == {
                "type": "turn_error",
                "message": "session ended",
                "retryable": False,
            }


def test_websocket_rejects_oversized_audio(db_session, monkeypatch) -> None:
    del db_session
    monkeypatch.setattr("app.api.get_settings", lambda: Settings(max_turn_audio_bytes=3))
    with TestClient(app) as client:
        session_id = client.post("/api/sessions", json={"consent": {"ok": True}}).json()[
            "session_id"
        ]
        with client.websocket_connect(f"/ws/sessions/{session_id}") as ws:
            ws.receive_json()
            ws.send_json({"type": "start_turn", "speaker": "doctor", "lang": "vi"})
            ws.send_bytes(b"abcd")
            assert ws.receive_json() == {
                "type": "turn_error",
                "message": "audio turn too large",
                "retryable": True,
            }


def test_websocket_rejects_oversized_typed_turn(db_session) -> None:
    del db_session
    with TestClient(app) as client:
        session_id = client.post("/api/sessions", json={"consent": {"ok": True}}).json()[
            "session_id"
        ]
        with client.websocket_connect(f"/ws/sessions/{session_id}") as ws:
            ws.receive_json()
            ws.send_json(
                {
                    "type": "text_turn",
                    "speaker": "doctor",
                    "lang": "vi",
                    "text": "x" * 2001,
                }
            )
            assert ws.receive_json() == {
                "type": "turn_error",
                "message": "typed turn too long",
                "retryable": True,
            }


def test_info_logs_do_not_include_turn_text(db_session, caplog) -> None:
    del db_session
    caplog.set_level(logging.INFO, logger="app.api")
    sensitive_text = "patient-secret-phrase"
    with TestClient(app) as client:
        session_id = client.post("/api/sessions", json={"consent": {"ok": True}}).json()[
            "session_id"
        ]
        with client.websocket_connect(f"/ws/sessions/{session_id}") as ws:
            ws.receive_json()
            ws.send_json(
                {
                    "type": "text_turn",
                    "speaker": "doctor",
                    "lang": "vi",
                    "text": sensitive_text,
                }
            )
            assert ws.receive_json()["type"] == "turn_result"

    messages = [record.getMessage() for record in caplog.records if record.name == "app.api"]
    assert "turn_processed" in messages
    assert sensitive_text not in caplog.text
    assert f"[vi->en] {sensitive_text}" not in caplog.text


def test_confirm_rejects_ended_session_and_delivered_turn(db_session) -> None:
    del db_session
    with TestClient(app) as client:
        session_id = client.post("/api/sessions", json={"consent": {"ok": True}}).json()[
            "session_id"
        ]
        with client.websocket_connect(f"/ws/sessions/{session_id}") as ws:
            ws.receive_json()
            ws.send_json(
                {
                    "type": "text_turn",
                    "speaker": "doctor",
                    "lang": "vi",
                    "text": "xin chao",
                }
            )
            delivered_id = ws.receive_json()["turn"]["id"]
            ws.send_json(
                {
                    "type": "text_turn",
                    "speaker": "doctor",
                    "lang": "vi",
                    "text": "uống 500 mg",
                }
            )
            awaiting_id = ws.receive_json()["turn"]["id"]

        assert client.post(f"/api/turns/{delivered_id}/confirm", json={}).status_code == 409
        assert client.post(f"/api/sessions/{session_id}/end").status_code == 204
        assert client.post(f"/api/turns/{awaiting_id}/confirm", json={}).status_code == 409


def test_admin_review_filters_flagged_risk_and_exports_csv(db_session) -> None:
    del db_session
    with TestClient(app) as client:
        session_id = client.post("/api/sessions", json={"consent": {"ok": True}}).json()[
            "session_id"
        ]
        with client.websocket_connect(f"/ws/sessions/{session_id}") as ws:
            ws.receive_json()
            ws.send_json(
                {
                    "type": "text_turn",
                    "speaker": "doctor",
                    "lang": "vi",
                    "text": "uống 500 mg",
                }
            )
            turn = ws.receive_json()["turn"]

        client.post(
            f"/api/turns/{turn['id']}/feedback",
            json={"reason": "wrong_term", "comment": "dose needs review"},
        )

        assert client.get("/api/admin/review").status_code == 401
        response = client.get(
            "/api/admin/review?risk=high&flagged=1&limit=1",
            headers={"X-Admin-Token": "change-me"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == 1
        assert payload["items"][0]["id"] == turn["id"]
        assert payload["items"][0]["feedback"][0]["reason"] == "wrong_term"

        csv_response = client.get(
            "/api/admin/review?format=csv&flagged=1",
            headers={"X-Admin-Token": "change-me"},
        )
        assert csv_response.status_code == 200
        assert "wrong_term" in csv_response.text


def test_admin_review_uses_constant_time_token_comparison(db_session, monkeypatch) -> None:
    del db_session
    calls: list[tuple[str, str]] = []

    def compare_digest(left: str, right: str) -> bool:
        calls.append((left, right))
        return left == right

    monkeypatch.setattr(api_module.hmac, "compare_digest", compare_digest)
    with TestClient(app) as client:
        assert client.get("/api/admin/review").status_code == 401
        assert client.get(
            "/api/admin/review", headers={"X-Admin-Token": "change-me"}
        ).status_code == 200

    assert calls == [("", "change-me"), ("change-me", "change-me")]


def test_admin_review_escalated_filter(db_session) -> None:
    del db_session
    with TestClient(app) as client:
        session_id = client.post("/api/sessions", json={"consent": {"ok": True}}).json()[
            "session_id"
        ]
        with client.websocket_connect(f"/ws/sessions/{session_id}") as ws:
            ws.receive_json()
            ws.send_json(
                {
                    "type": "text_turn",
                    "speaker": "patient",
                    "lang": "en",
                    "text": "I have chest pain",
                }
            )
            turn = ws.receive_json()["turn"]

        client.post(f"/api/sessions/{session_id}/escalate")
        response = client.get(
            "/api/admin/review?escalated=1",
            headers={"X-Admin-Token": "change-me"},
        )

        assert response.status_code == 200
        assert response.json()["items"][0]["id"] == turn["id"]
