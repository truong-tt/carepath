"""CLI: LLM/RAG correction baseline (paper's +GEC comparison row).

Runs the live CarePath retrieval + LLM correction over GEC pairs, adding a
``corrected_text`` column so ``evaluate``/``gate`` can compare the trained adapter
against the no-training LLM/RAG baseline.

    python scripts/gec/llm_rag_baseline.py \
      --input artifacts/gec_pairs/vimedcss_gipformer_pairs_smoke.jsonl \
      --output artifacts/evaluations/ckey_rag_smoke.jsonl --limit 20
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from carepath.gec.cliutil import configure_stdout  # noqa: E402

configure_stdout()

from carepath.config import Settings  # noqa: E402
from carepath.gec.data import read_jsonl  # noqa: E402
from carepath.services.pipeline import CarePathPipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    rows = read_jsonl(Path(args.input))
    if args.limit:
        rows = rows[: args.limit]

    pipeline = CarePathPipeline(Settings.from_env())
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            result = pipeline.process_text(row["raw_asr"])
            handle.write(
                json.dumps(
                    {
                        **row,
                        "corrected_text": result.corrected_transcript,
                        "llm_rag_retrieved_terms": [t.term for t in result.retrieved_terms],
                        "correction_metadata": result.metadata,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(f"Wrote {len(rows)} LLM/RAG-corrected rows to {output_path}")


if __name__ == "__main__":
    main()
