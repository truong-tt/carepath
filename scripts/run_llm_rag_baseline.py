from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run HopeGait retrieval + LLM correction over GEC pairs."
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "apps" / "api"))

    from hopegait.config import Settings
    from hopegait.services.pipeline import HopeGaitPipeline

    args = parse_args()
    rows = [
        json.loads(line)
        for line in Path(args.input).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if args.limit:
        rows = rows[: args.limit]

    pipeline = HopeGaitPipeline(Settings.from_env())
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            result = pipeline.process_text(row["raw_asr"])
            enriched = {
                **row,
                "corrected_text": result.corrected_transcript,
                "retrieved_terms": [item.term for item in result.retrieved_terms],
                "correction_metadata": result.metadata,
            }
            handle.write(json.dumps(enriched, ensure_ascii=False) + "\n")
    print(f"Wrote {len(rows)} corrected rows to {output_path}")


if __name__ == "__main__":
    main()

