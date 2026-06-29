from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


def latest_annotation(task: dict[str, Any]) -> dict[str, Any] | None:
    annotations = task.get("annotations") or task.get("completions") or []
    usable = [item for item in annotations if not item.get("was_cancelled")]
    if not usable:
        return None
    return sorted(usable, key=lambda item: item.get("updated_at") or item.get("created_at") or "")[-1]


def extract_text(annotation: dict[str, Any]) -> str:
    for result in annotation.get("result", []):
        if result.get("from_name") != "transcription":
            continue
        value = result.get("value") or {}
        text = value.get("text") or []
        if isinstance(text, list):
            return "\n".join(str(item).strip() for item in text if str(item).strip()).strip()
        return str(text).strip()
    return ""


def extract_quality(annotation: dict[str, Any]) -> str:
    for result in annotation.get("result", []):
        if result.get("from_name") != "quality":
            continue
        choices = (result.get("value") or {}).get("choices") or []
        return choices[0] if choices else ""
    return ""


def load_tasks(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "tasks" in data:
        data = data["tasks"]
    if not isinstance(data, list):
        raise ValueError("Expected a Label Studio JSON export list.")
    return data


def build_rows(tasks: list[dict[str, Any]]) -> tuple[list[dict[str, str]], int]:
    rows = []
    skipped = 0
    for task in tasks:
        annotation = latest_annotation(task)
        if annotation is None:
            skipped += 1
            continue

        gold_text = extract_text(annotation)
        if not gold_text:
            skipped += 1
            continue

        data = task.get("data") or {}
        rows.append(
            {
                "audio_file": str(data.get("audio_file") or ""),
                "audio_url": str(data.get("audio") or ""),
                "raw_asr": str(data.get("whisper_text") or ""),
                "gold_text": gold_text,
                "quality": extract_quality(annotation),
                "source": "label_studio",
            }
        )
    return rows, skipped


def write_jsonl(rows: list[dict[str, str]], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["audio_file", "audio_url", "raw_asr", "gold_text", "quality", "source"],
        )
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a Label Studio JSON export into training-ready transcript rows."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tasks = load_tasks(args.input)
    rows, skipped = build_rows(tasks)
    if not rows:
        print("No completed transcript annotations found.", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.suffix.lower() == ".csv":
        write_csv(rows, args.output)
    else:
        write_jsonl(rows, args.output)

    print(f"Wrote {len(rows)} rows to: {args.output}")
    if skipped:
        print(f"Skipped {skipped} tasks with no completed transcript.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
