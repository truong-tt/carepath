import asyncio

import pytest
from fastapi.testclient import TestClient

import app.main as interpreter_main
from app.config import get_settings
from app.main import app, validate_runtime_settings


def test_health_check() -> None:
    response = TestClient(app).get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "provider_mode": "mock"}


def test_cloud_mode_requires_non_default_admin_token(monkeypatch) -> None:
    monkeypatch.setenv("PROVIDER_MODE", "cloud")
    monkeypatch.setenv("ADMIN_TOKEN", "change-me")
    get_settings.cache_clear()

    with pytest.raises(RuntimeError, match="ADMIN_TOKEN"):
        validate_runtime_settings()

    get_settings.cache_clear()


def test_cors_origins_parse_csv(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "https://console.example/, https://site.example")
    get_settings.cache_clear()

    assert get_settings().cors_origins == ("https://console.example", "https://site.example")

    get_settings.cache_clear()


def test_daily_retention_purge_repeats_until_cancelled(db_session, monkeypatch) -> None:
    del db_session
    calls: list[int] = []
    sleeps = 0

    async def sleep_once(_seconds: int) -> None:
        nonlocal sleeps
        sleeps += 1
        if sleeps > 1:
            raise asyncio.CancelledError

    monkeypatch.setattr(interpreter_main.asyncio, "sleep", sleep_once)
    monkeypatch.setattr(
        interpreter_main.crud,
        "purge_old_sessions",
        lambda _db, retention_days: calls.append(retention_days),
    )

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(interpreter_main._purge_old_sessions_daily(30))

    assert calls == [30]
