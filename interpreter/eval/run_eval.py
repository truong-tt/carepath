import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import crud  # noqa: E402
from app.config import Settings  # noqa: E402
from app.db import init_db  # noqa: E402
from app.glossary import lookup_glossary, seed_glossary  # noqa: E402
from app.normalize import normalize_text  # noqa: E402
from app.providers import get_providers  # noqa: E402
from app.risk.engine import load_lexicon  # noqa: E402
from app.session import process_text_turn  # noqa: E402

NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
UNIT_RE = re.compile(r"\b(?:mg|ml|mcg|viên|gói|ống|tablet|tablets|sachet|ampoule)\b", re.I)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def count_terms(text: str, terms: list[str]) -> int:
    folded = text.casefold()
    return sum(folded.count(term.casefold()) for term in terms)


def preservation(row: dict[str, str], output: str, db: Session) -> dict[str, bool]:
    source = normalize_text(row["source"])
    glossary_hits = lookup_glossary(db, source)
    drug_terms = [hit.term_vi for hit in glossary_hits if hit.kind == "drug"]
    laterality_terms = load_lexicon("laterality.json")
    negation_terms = load_lexicon("negation_cues.json")
    return {
        "number_exact": NUMBER_RE.findall(source) == NUMBER_RE.findall(output),
        "unit_exact": UNIT_RE.findall(source) == UNIT_RE.findall(output),
        "negation_polarity": (
            count_terms(source, negation_terms) == count_terms(output, negation_terms)
        ),
        "laterality_exact": count_terms(source, laterality_terms)
        == count_terms(output, laterality_terms),
        "drug_name_exact": all(term.casefold() in output.casefold() for term in drug_terms),
    }


def score(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    counters = Counter()
    for row in rows:
        counters["risk_correct"] += row["actual_tier"] == row["expected_tier"]
        counters["escalation_correct"] += row["requires_confirmation"] == (
            row["actual_tier"] in {"high", "critical"}
        )
        for key, passed in row["preservation"].items():
            counters[key] += passed
    return {
        "total": total,
        "risk_accuracy": counters["risk_correct"] / total,
        "escalation_correctness": counters["escalation_correct"] / total,
        "preservation": {
            key: counters[key] / total
            for key in [
                "number_exact",
                "unit_exact",
                "negation_polarity",
                "laterality_exact",
                "drug_name_exact",
            ]
        },
    }


def write_reports(report: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "eval_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    metrics = report["metrics"]
    lines = [
        "# Eval Report",
        "",
        f"- Total rows: {metrics['total']}",
        f"- Risk accuracy: {metrics['risk_accuracy']:.2%}",
        f"- Escalation correctness: {metrics['escalation_correctness']:.2%}",
    ]
    for key, value in metrics["preservation"].items():
        lines.append(f"- {key}: {value:.2%}")
    (output_dir / "eval_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_eval(path: Path, provider_mode: str) -> dict[str, Any]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine)
    with Session(engine) as db:
        seed_glossary(db)
        session = crud.create_session(db, {"eval": True})
        settings = Settings(provider_mode="mock" if provider_mode == "mock" else "cloud")
        providers = get_providers(settings)
        rows = []
        for row in read_tsv(path):
            turn = process_text_turn(
                db,
                providers,
                settings,
                session_id=session.id,
                speaker=row["speaker"],
                lang=row["lang"],
                text=row["source"],
                asr_confidence=0.5 if row["category"].startswith("low_confidence") else 0.99,
            )
            rows.append(
                {
                    **row,
                    "actual_tier": turn.risk_tier,
                    "requires_confirmation": turn.status in {"awaiting_confirm", "blocked"},
                    "translation": turn.translation,
                    "preservation": preservation(row, turn.translation, db),
                }
            )
    return {"metrics": score(rows), "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", required=True, type=Path)
    parser.add_argument("--providers", choices=["mock", "real"], default="mock")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "eval" / "reports")
    args = parser.parse_args()

    report = run_eval(args.set, args.providers)
    write_reports(report, args.output_dir)
    print(json.dumps(report["metrics"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
