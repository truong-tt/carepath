from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a labeled text-noise ablation by mining real Gipformer substitutions. "
            "This is not the primary DARAG synthetic-TTS path."
        )
    )
    parser.add_argument("--real-pairs", required=True)
    parser.add_argument("--synthetic-clean", required=True)
    parser.add_argument("--output", default="artifacts/gec_pairs/text_noise_ablation_pairs.jsonl")
    parser.add_argument("--noise-prob", type=float, default=0.18)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "apps" / "api"))

    from carepath.darag import validate_gec_pair

    args = parse_args()
    random.seed(args.seed)
    substitutions = mine_substitutions(read_jsonl(Path(args.real_pairs)))
    rows = read_jsonl(Path(args.synthetic_clean))
    if args.limit:
        rows = rows[: args.limit]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            noisy, applied = apply_noise(row["clean_text"], substitutions, args.noise_prob)
            pair = {
                "split": row.get("split", "train"),
                "source_kind": "text_noise_ablation",
                "audio_id": row["synthetic_id"],
                "synthetic_id": row["synthetic_id"],
                "raw_asr": noisy,
                "gold_text": row["clean_text"],
                "gold_terms": row.get("intended_terms", []),
                "retrieved_terms": row.get("intended_terms", []),
                "topic": row.get("topic"),
                "duration_seconds": None,
                "asr_model": "text_noise_from_real_gipformer_confusions",
                "asr_metadata": {"applied_substitutions": applied},
            }
            validation = validate_gec_pair(pair)
            if not validation.ok:
                raise ValueError(f"Invalid ablation pair: {validation.errors}")
            handle.write(json.dumps(pair, ensure_ascii=False) + "\n")
    print(f"Wrote text-noise ablation pairs to {output_path}")


def mine_substitutions(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        gold_tokens = str(row["gold_text"]).split()
        asr_tokens = str(row["raw_asr"]).split()
        for gold, asr in zip(gold_tokens, asr_tokens):
            if gold.lower() != asr.lower():
                counts[gold.lower()][asr] += 1
    return {
        gold: [candidate for candidate, _ in counter.most_common(5)]
        for gold, counter in counts.items()
    }


def apply_noise(
    clean_text: str,
    substitutions: dict[str, list[str]],
    noise_prob: float,
) -> tuple[str, list[dict[str, str]]]:
    noisy_tokens = []
    applied = []
    for token in clean_text.split():
        key = token.lower()
        if key in substitutions and random.random() < noise_prob:
            replacement = random.choice(substitutions[key])
            noisy_tokens.append(replacement)
            applied.append({"gold": token, "noisy": replacement})
        else:
            noisy_tokens.append(token)
    return " ".join(noisy_tokens), applied


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


if __name__ == "__main__":
    main()
