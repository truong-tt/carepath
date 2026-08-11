import argparse
import csv
import json
import re
import sys
import time
from collections import Counter
from datetime import UTC, datetime
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

NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")

# These metrics compare a Vietnamese source against an English translation, so
# every one of them has to compare *meaning*, not surface tokens. Comparing raw
# tokens scored correct translations as failures: "Tiêm 1 ống" -> "Inject 1
# ampoule" looked like a unit error, and "Ngày hai lần" -> "Twice a day" looked
# like a dropped number.

UNIT_CANON = {
    "mg": "MG",
    "ml": "ML",
    "mcg": "MCG",
    "µg": "MCG",
    "microgram": "MCG",
    "micrograms": "MCG",
    "milligram": "MG",
    "milligrams": "MG",
    "millilitre": "ML",
    "millilitres": "ML",
    "milliliter": "ML",
    "milliliters": "ML",
    "viên": "TABLET",
    "tablet": "TABLET",
    "tablets": "TABLET",
    "gói": "SACHET",
    "sachet": "SACHET",
    "sachets": "SACHET",
    "ống": "AMPOULE",
    "ampoule": "AMPOULE",
    "ampoules": "AMPOULE",
    "giọt": "DROP",
    "drop": "DROP",
    "drops": "DROP",
}
UNIT_RE = re.compile(r"\b(" + "|".join(sorted(UNIT_CANON, key=len, reverse=True)) + r")\b", re.I)

LATERALITY_CANON = {"trái": "LEFT", "left": "LEFT", "phải": "RIGHT", "right": "RIGHT"}
LATERALITY_RE = re.compile(
    r"\b(" + "|".join(sorted(LATERALITY_CANON, key=len, reverse=True)) + r")\b", re.I
)

# Vietnamese number words are already digits by the time normalize_text is done;
# English ones are not.
EN_NUMBER_WORDS = {
    "one": "1", "once": "1", "two": "2", "twice": "2", "three": "3", "thrice": "3",
    "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12", "half": "0.5",
}
EN_NUMBER_RE = re.compile(r"\b(" + "|".join(EN_NUMBER_WORDS) + r")\b", re.I)

# A Vietnamese yes/no question ends in "không", "chưa" or "chứ". That is
# interrogative, not negation: "Anh có dị ứng không?" is "Do you have an
# allergy?", which carries no negation in either language.
QUESTION_TAIL_RE = re.compile(r"\s*\b(không|chưa|chứ)\b\s*[?.!]*\s*$", re.IGNORECASE)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def count_terms(text: str, terms: list[str]) -> int:
    """Count whole-word occurrences.

    Substring counting scored "Hospital noise" and "cannot" as carrying the
    negation cue "no", so correct translations failed on negation polarity.
    """
    folded = text.casefold()
    return sum(
        len(re.findall(rf"\b{re.escape(term.casefold())}\b", folded)) for term in terms
    )


def canonical_units(text: str) -> set[str]:
    """Which dose forms are named, not how many times.

    A translation may repeat the form — "Eye drops 1 drop" names DROP twice for
    one instruction — so counting occurrences flagged correct output. Whether a
    form was preserved, dropped or swapped is what this metric is for; the count
    itself is the number metric's job.
    """
    return {UNIT_CANON[match.group(1).casefold()] for match in UNIT_RE.finditer(text)}


def canonical_laterality(text: str) -> set[str]:
    return {LATERALITY_CANON[match.group(1).casefold()] for match in LATERALITY_RE.finditer(text)}


def canonical_numbers(text: str) -> Counter:
    """Numbers as values, with English number words and decimal commas folded in."""
    spelled = EN_NUMBER_RE.sub(lambda m: EN_NUMBER_WORDS[m.group(1).casefold()], text)
    return Counter(value.replace(",", ".") for value in NUMBER_RE.findall(spelled))


def negation_count(text: str, negation_terms: list[str]) -> int:
    return count_terms(QUESTION_TAIL_RE.sub("", text.strip()), negation_terms)


def preservation(row: dict[str, str], output: str, db: Session) -> dict[str, bool]:
    source = normalize_text(row["source"])
    glossary_hits = lookup_glossary(db, source)
    drug_terms = [hit.term_vi for hit in glossary_hits if hit.kind == "drug"]
    negation_terms = load_lexicon("negation_cues.json")
    return {
        "number_exact": canonical_numbers(source) == canonical_numbers(output),
        "unit_exact": canonical_units(source) == canonical_units(output),
        "negation_polarity": (
            negation_count(source, negation_terms) == negation_count(output, negation_terms)
        ),
        "laterality_exact": canonical_laterality(source) == canonical_laterality(output),
        "drug_name_exact": all(term.casefold() in output.casefold() for term in drug_terms),
    }


def score(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    counters = Counter()
    for row in rows:
        counters["risk_correct"] += row["actual_tier"] == row["expected_tier"]
        for key, passed in row["preservation"].items():
            counters[key] += passed
    latencies = sorted(row["latency_ms"] for row in rows if row.get("latency_ms"))
    return {
        "total": total,
        "risk_accuracy": counters["risk_correct"] / total,
        # escalation_correctness was removed deliberately: it re-derived
        # requires_confirmation from the same risk_tier it was compared against,
        # so it was a tautology that always reported 100%.
        "latency_ms": (
            {
                "median": latencies[len(latencies) // 2],
                "min": latencies[0],
                "max": latencies[-1],
            }
            if latencies
            else None
        ),
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
    run = report.get("run", {})
    lines = [
        "# Eval Report",
        "",
        f"- Provider mode: `{run.get('provider_mode')}`"
        + (f" (model `{run['model']}`)" if run.get("model") else ""),
        f"- Fixture: `{run.get('fixture')}`",
        f"- Recorded: {run.get('recorded_at')}",
        "",
        f"- Total rows: {metrics['total']}",
        f"- Risk accuracy: {metrics['risk_accuracy']:.2%}",
    ]
    if metrics.get("latency_ms"):
        latency = metrics["latency_ms"]
        lines.append(
            f"- Latency per turn: median {latency['median']}ms, "
            f"min {latency['min']}ms, max {latency['max']}ms"
        )
    lines.append("")
    lines.append("Preservation (source vs translation):")
    for key, value in metrics["preservation"].items():
        lines.append(f"- {key}: {value:.2%}")
    if run.get("provider_mode") in {"mock", "demo"}:
        lines += [
            "",
            "> Preservation figures from mock or demo mode are not evidence: the",
            "> canned translation contains the source text, so every check passes",
            "> trivially. Only a `ckey` or `cloud` run measures anything.",
        ]
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
        settings = Settings(provider_mode=provider_mode)
        providers = get_providers(settings)
        rows = []
        for index, row in enumerate(read_tsv(path), 1):
            start = time.perf_counter()
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
            latency_ms = int((time.perf_counter() - start) * 1000)
            print(f"[{index}] {row['id']} {turn.risk_tier} {latency_ms}ms", flush=True)
            rows.append(
                {
                    **row,
                    "actual_tier": turn.risk_tier,
                    "requires_confirmation": turn.status in {"awaiting_confirm", "blocked"},
                    "translation": turn.translation,
                    "latency_ms": latency_ms,
                    "preservation": preservation(row, turn.translation, db),
                }
            )
    return {
        "run": {
            "provider_mode": provider_mode,
            "model": settings.llm_model if provider_mode == "ckey" else None,
            "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "fixture": path.name,
        },
        "metrics": score(rows),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", required=True, type=Path)
    parser.add_argument(
        "--providers", choices=["mock", "demo", "ckey", "cloud"], default="mock"
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / "eval" / "reports")
    args = parser.parse_args()

    report = run_eval(args.set, args.providers)
    write_reports(report, args.output_dir)
    print(json.dumps(report["metrics"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
