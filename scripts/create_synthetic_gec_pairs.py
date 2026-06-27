from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Gipformer over synthetic TTS audio to create DARAG GEC pairs."
    )
    parser.add_argument("--input", required=True, help="JSONL from synthesize_speech.py")
    parser.add_argument("--output", default="artifacts/gec_pairs/darag_synthetic_pairs.jsonl")
    parser.add_argument("--lexicon", default="data/medical_lexicon.json")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "apps" / "api"))

    from carepath.config import Settings
    from carepath.darag import validate_gec_pair
    from carepath.services.asr import build_asr_service
    from carepath.services.retrieval import MedicalTermRetriever

    args = parse_args()
    rows = read_jsonl(Path(args.input))
    if args.limit:
        rows = rows[: args.limit]

    settings = Settings.from_env()
    asr = build_asr_service(settings)
    retriever = MedicalTermRetriever(Path(args.lexicon), top_k=settings.retrieval_top_k)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed = load_completed_ids(output_path) if args.resume else set()
    mode = "a" if args.resume and output_path.exists() else "w"

    with output_path.open(mode, encoding="utf-8") as handle:
        for row in rows:
            synthetic_id = row["synthetic_id"]
            if synthetic_id in completed:
                continue
            result = asr.transcribe(Path(row["audio_path"]))
            retrieved_terms = [
                item.term for item in retriever.retrieve(f"{result.text} {row['clean_text']}")
            ]
            pair = {
                "split": row.get("split", "train"),
                "source_kind": "darag_synthetic_tts",
                "audio_id": synthetic_id,
                "synthetic_id": synthetic_id,
                "raw_asr": result.text,
                "gold_text": row["clean_text"],
                "gold_terms": row.get("intended_terms", []),
                "retrieved_terms": retrieved_terms,
                "topic": row.get("topic"),
                "duration_seconds": result.metadata.get("duration_seconds"),
                "asr_model": result.model,
                "asr_metadata": result.metadata,
                "tts_model": row.get("tts_model"),
                "audio_path": row.get("audio_path"),
            }
            validation = validate_gec_pair(pair)
            if not validation.ok:
                raise ValueError(f"Invalid synthetic pair {synthetic_id}: {validation.errors}")
            handle.write(json.dumps(pair, ensure_ascii=False) + "\n")
            handle.flush()
    print(f"Wrote synthetic GEC pairs to {output_path}")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def load_completed_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {row["audio_id"] for row in read_jsonl(path) if row.get("audio_id")}


if __name__ == "__main__":
    main()
