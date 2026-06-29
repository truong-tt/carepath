from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import quote

from faster_whisper import WhisperModel


AUDIO_EXTENSIONS = {
    ".aac",
    ".flac",
    ".m4a",
    ".mp3",
    ".oga",
    ".ogg",
    ".opus",
    ".wav",
    ".webm",
}


def find_audio_files(audio_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in audio_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    )


def make_audio_url(base_url: str, audio_dir: Path, audio_path: Path) -> str:
    relative = audio_path.relative_to(audio_dir).as_posix()
    return f"{base_url.rstrip('/')}/{quote(relative)}"


def transcribe_file(model: WhisperModel, audio_path: Path, args: argparse.Namespace) -> str:
    segments, _info = model.transcribe(
        str(audio_path),
        language=args.language or None,
        beam_size=args.beam_size,
        vad_filter=args.vad_filter,
        condition_on_previous_text=False,
    )
    return " ".join(segment.text.strip() for segment in segments).strip()


def build_task(
    audio_dir: Path,
    audio_path: Path,
    text: str,
    base_url: str,
    model_name: str,
) -> dict:
    relative = audio_path.relative_to(audio_dir).as_posix()
    return {
        "external_id": relative,
        "data": {
            "audio": make_audio_url(base_url, audio_dir, audio_path),
            "audio_file": relative,
            "whisper_text": text,
        },
        "predictions": [
            {
                "model_version": f"faster-whisper:{model_name}",
                "result": [
                    {
                        "from_name": "transcription",
                        "to_name": "audio",
                        "type": "textarea",
                        "value": {"text": [text]},
                    }
                ],
            }
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe local audio files and create a Label Studio import JSON."
    )
    parser.add_argument("--audio-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", default="large-v3-turbo")
    parser.add_argument("--language", default="vi")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--beam-size", default=5, type=int)
    parser.add_argument(
        "--audio-base-url",
        default="http://127.0.0.1:8765",
        help="Base URL from scripts/labeling/serve_audio.py.",
    )
    parser.add_argument(
        "--no-vad-filter",
        action="store_false",
        dest="vad_filter",
        help="Disable silence filtering.",
    )
    parser.set_defaults(vad_filter=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audio_dir = args.audio_dir.resolve()
    output = args.output.resolve()

    if not audio_dir.exists():
        print(f"Audio folder not found: {audio_dir}", file=sys.stderr)
        return 2

    audio_files = find_audio_files(audio_dir)
    if not audio_files:
        print(f"No audio files found in: {audio_dir}", file=sys.stderr)
        return 2

    print(f"Loading Whisper model: {args.model}")
    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)

    tasks = []
    for index, audio_path in enumerate(audio_files, start=1):
        print(f"[{index}/{len(audio_files)}] {audio_path.name}")
        text = transcribe_file(model, audio_path, args)
        tasks.append(build_task(audio_dir, audio_path, text, args.audio_base_url, args.model))

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(tasks)} Label Studio tasks to: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
