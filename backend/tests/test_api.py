from fastapi.testclient import TestClient

from app.main import app


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
        assert confirm.json()["status"] == "confirmed"

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
