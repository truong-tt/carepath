from __future__ import annotations

import argparse
import csv
import json
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create HopeGait GEC pairs by running Gipformer over ViMedCSS audio: "
            "raw_asr -> gold segment_text."
        )
    )
    parser.add_argument("--dataset", default="tensorxt/ViMedCSS")
    parser.add_argument("--output", default="artifacts/gec_pairs/vimedcss_gipformer_pairs.jsonl")
    parser.add_argument("--splits", nargs="+", default=["train", "validation", "test", "hard"])
    parser.add_argument("--limit-per-split", type=int, default=None)
    parser.add_argument("--asr-provider", default="gipformer", choices=["gipformer", "mock"])
    parser.add_argument("--lexicon", default="data/medical_lexicon.json")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    from datasets import Audio, load_dataset  # type: ignore

    from hopegait.config import Settings
    from hopegait.services.retrieval import MedicalTermRetriever
    from hopegait.services.asr import build_asr_service

    settings = Settings.from_env()
    if args.asr_provider == "mock":
        settings = replace(settings, asr_provider="mock", allow_mock_asr=True)
    asr = build_asr_service(settings)
    retriever = MedicalTermRetriever(Path(args.lexicon), top_k=settings.retrieval_top_k)

    manifest_rows: list[dict[str, Any]] = []
    completed = load_completed_ids(output_path) if args.resume else set()
    mode = "a" if args.resume and output_path.exists() else "w"
    with output_path.open(mode, encoding="utf-8") as handle:
        for split in args.splits:
            dataset = load_dataset(args.dataset, split=split).cast_column(
                "audio", Audio(decode=True)
            )
            if args.limit_per_split:
                dataset = dataset.select(range(min(args.limit_per_split, len(dataset))))

            for row in dataset:
                row_id = f"{split}:{row['segment_id']}"
                if row_id in completed:
                    continue
                pair = transcribe_row(asr, retriever, split, row)
                handle.write(json.dumps(pair, ensure_ascii=False) + "\n")
                handle.flush()
                manifest_rows.append(pair)

    write_manifest_csv(output_path.with_suffix(".manifest.csv"), manifest_rows)
    print(f"Wrote {len(manifest_rows)} GEC pairs to {output_path}")


def transcribe_row(asr: Any, retriever: Any, split: str, row: dict[str, Any]) -> dict[str, Any]:
    audio = row["audio"]
    array = audio["array"]
    sampling_rate = int(audio["sampling_rate"])

    with tempfile.TemporaryDirectory(prefix="hopegait_pair_") as temp_dir:
        wav_path = Path(temp_dir) / f"{row['segment_id']}.wav"
        write_wav(wav_path, array, sampling_rate)
        result = asr.transcribe(wav_path)

    gold_terms = split_terms(row.get("cs_terms_list", ""))
    retrieval_text = " ".join(part for part in (result.text, row["segment_text"]) if part)
    retrieved_terms = [item.term for item in retriever.retrieve(retrieval_text)]
    return {
        "split": split,
        "source_kind": "vimedcss_real",
        "audio_id": row["segment_id"],
        "raw_asr": result.text,
        "gold_text": row["segment_text"],
        "gold_terms": gold_terms,
        "retrieved_terms": retrieved_terms,
        "cs_terms_list": row.get("cs_terms_list", ""),
        "topic": row.get("topic"),
        "duration_seconds": row.get("duration_seconds"),
        "asr_model": result.model,
        "asr_metadata": result.metadata,
    }


def split_terms(raw: str | list[str] | None) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    return [item.strip() for item in str(raw).split(";") if item.strip()]


def load_completed_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    completed = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        completed.add(f"{row.get('split')}:{row.get('audio_id')}")
    return completed


def write_wav(path: Path, samples: Any, sampling_rate: int) -> None:
    import soundfile as sf  # type: ignore

    sf.write(str(path), samples, sampling_rate)


def write_manifest_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
