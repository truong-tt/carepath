import pytest
from fastapi.testclient import TestClient

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
