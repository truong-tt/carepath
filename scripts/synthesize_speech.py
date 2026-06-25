from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synthesize Vietnamese audio from clean DARAG transcripts."
    )
    parser.add_argument("--input", required=True, help="JSONL from generate_synthetic_transcripts.py")
    parser.add_argument("--output", default="artifacts/synthetic/synthetic_audio_manifest.jsonl")
    parser.add_argument("--audio-dir", default="artifacts/synthetic/audio")
    parser.add_argument("--provider", choices=["mms"], default="mms")
    parser.add_argument("--model", default="facebook/mms-tts-vie")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = read_jsonl(Path(args.input))
    if args.limit:
        rows = rows[: args.limit]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    audio_dir = Path(args.audio_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)
    completed = load_completed_ids(output_path) if args.resume else set()

    synthesizer = MMSSynthesizer(args.model)
    mode = "a" if args.resume and output_path.exists() else "w"
    with output_path.open(mode, encoding="utf-8") as handle:
        for row in rows:
            synthetic_id = row["synthetic_id"]
            if synthetic_id in completed:
                continue
            audio_path = audio_dir / f"{safe_filename(synthetic_id)}.wav"
            synthesizer.synthesize(row["clean_text"], audio_path)
            out = {
                **row,
                "audio_path": str(audio_path),
                "tts_provider": args.provider,
                "tts_model": args.model,
            }
            handle.write(json.dumps(out, ensure_ascii=False) + "\n")
            handle.flush()
    print(f"Wrote synthetic audio manifest to {output_path}")


class MMSSynthesizer:
    def __init__(self, model_name: str):
        import torch  # type: ignore
        from transformers import VitsModel, AutoTokenizer  # type: ignore

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = VitsModel.from_pretrained(model_name)
        self.model.eval()

    def synthesize(self, text: str, output_path: Path) -> None:
        import soundfile as sf  # type: ignore

        inputs = self.tokenizer(text, return_tensors="pt")
        with self.torch.no_grad():
            waveform = self.model(**inputs).waveform[0].cpu().numpy()
        sf.write(str(output_path), waveform, self.model.config.sampling_rate)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def load_completed_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {
        row["synthetic_id"]
        for row in read_jsonl(path)
        if row.get("synthetic_id") and row.get("audio_path")
    }


def safe_filename(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


if __name__ == "__main__":
    main()
