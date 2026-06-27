from __future__ import annotations

import argparse
import contextlib
import json
import tempfile
import wave
from pathlib import Path

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send an audio clip through the running CarePath API."
    )
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--audio", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--preview-chars", type=int, default=500)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument(
        "--encounter-context",
        default="Phong kham noi tong quat",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    health_url = args.url.rstrip("/") + "/api/v1/health"
    soap_url = args.url.rstrip("/") + "/api/v1/soap-notes"

    with httpx.Client(timeout=args.timeout) as client:
        health = client.get(health_url)
        health.raise_for_status()
        health_json = health.json()
        if health_json.get("asr_provider") != "gipformer":
            raise SystemExit(
                "API is not in Gipformer mode. Set ASR_PROVIDER=gipformer and restart."
            )

        with _audio_path(args.audio) as audio_path:
            with audio_path.open("rb") as handle:
                response = client.post(
                    soap_url,
                    files={"audio": (audio_path.name, handle, "audio/wav")},
                    data={"encounter_context": args.encounter_context},
                )

        if response.status_code >= 400:
            raise SystemExit(
                f"SOAP request failed: HTTP {response.status_code} {response.text}"
            )

        payload = response.json()
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        print(
            json.dumps(
                {
                    "asr_provider": health_json["asr_provider"],
                    "asr_ready": health_json["asr_ready"],
                    "raw_transcript_chars": len(payload["raw_transcript"]),
                    "corrected_transcript_chars": len(payload["corrected_transcript"]),
                    "raw_transcript_preview": _preview(
                        payload["raw_transcript"], args.preview_chars
                    ),
                    "corrected_transcript_preview": _preview(
                        payload["corrected_transcript"], args.preview_chars
                    ),
                    "retrieved_terms": payload["retrieved_terms"],
                    "soap_review_required": payload["soap"]["review_required"],
                    "soap": payload["soap"],
                    "metadata": payload["metadata"],
                    "output": str(args.output) if args.output else None,
                },
                ensure_ascii=True,
                indent=2,
            )
        )


@contextlib.contextmanager
def _audio_path(audio: Path | None):
    if audio is not None:
        yield audio
        return

    with tempfile.TemporaryDirectory(prefix="carepath_real_asr_") as temp_dir:
        path = Path(temp_dir) / "silence.wav"
        _write_silent_wav(path)
        yield path


def _write_silent_wav(path: Path) -> None:
    with contextlib.closing(wave.open(str(path), "wb")) as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(16000)
        writer.writeframes(b"\x00\x00" * 16000)


def _preview(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


if __name__ == "__main__":
    main()
