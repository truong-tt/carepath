from __future__ import annotations

import contextlib
import json
import os
import sys
import tempfile
import wave
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "scribe"))

    os.environ.setdefault("ASR_PROVIDER", "mock")
    os.environ.setdefault("ALLOW_MOCK_ASR", "true")
    os.environ.setdefault("LLM_PROVIDER", "offline")
    os.environ.setdefault("MEDICAL_LEXICON_PATH", str(repo_root / "data" / "medical_lexicon.json"))

    try:
        from fastapi.testclient import TestClient
    except ImportError as exc:
        raise SystemExit(
            "FastAPI test dependencies are missing. Run: pip install -e \".[dev]\""
        ) from exc

    from carepath.main import app, get_pipeline, get_settings

    get_settings.cache_clear()
    get_pipeline.cache_clear()
    client = TestClient(app)

    health = _assert_ok(client.get("/api/v1/health"), "health")
    correction = _assert_ok(
        client.post(
            "/api/v1/corrections",
            json={
                "raw_transcript": "benh nhan dau nguc spo2 98 % huyet ap 120 tren 80 mmhg",
                "encounter_context": "Phong kham noi tong quat",
            },
        ),
        "corrections",
    )

    with tempfile.TemporaryDirectory(prefix="carepath_smoke_") as temp_dir:
        wav_path = Path(temp_dir) / "demo.wav"
        _write_silent_wav(wav_path)
        with wav_path.open("rb") as handle:
            soap = _assert_ok(
                client.post(
                    "/api/v1/soap-notes",
                    files={"audio": ("demo.wav", handle, "audio/wav")},
                    data={"encounter_context": "Phong kham noi tong quat"},
                ),
                "soap-notes",
            )

    summary = {
        "health": health["status"],
        "correction_terms": correction["retrieved_terms"],
        "soap_review_required": soap["soap"]["review_required"],
        "asr_model": soap["metadata"].get("asr_model"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def _assert_ok(response, label: str) -> dict:
    if response.status_code >= 400:
        raise SystemExit(f"{label} failed: HTTP {response.status_code} {response.text}")
    return response.json()


def _write_silent_wav(path: Path) -> None:
    with contextlib.closing(wave.open(str(path), "wb")) as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(16000)
        writer.writeframes(b"\x00\x00" * 16000)


if __name__ == "__main__":
    main()
