"""Every risk kind the engine actually produces must have a Vietnamese UI label.

Without this, a new detector silently renders as "Thông tin cần kiểm tra"
("item to check"), which tells a clinician nothing about why a turn was gated.

The kinds are collected by running the engine over the risk fixtures rather
than by reading its source, so the guard follows real behaviour instead of a
regex over Python that a refactor could quietly invalidate. It crosses the
Python/TypeScript boundary deliberately: the drift it catches is a Python
change outrunning a TypeScript one.
"""

import json
import re
from pathlib import Path

from app.glossary import lookup_glossary, seed_glossary
from app.normalize import normalize_text
from app.risk import classify_risk

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "interpreter" / "eval" / "fixtures"
LABELS = REPO_ROOT / "scribe" / "frontend" / "src" / "visit" / "riskLabels.ts"


def produced_kinds(db_session) -> set[str]:
    seed_glossary(db_session)
    kinds: set[str] = set()
    for name in ("risk_cases.jsonl", "risk_precision_cases.jsonl"):
        for line in (FIXTURE_DIR / name).read_text(encoding="utf-8").splitlines():
            case = json.loads(line)
            source = normalize_text(case["source"])
            result = classify_risk(
                source,
                normalize_text(case["translation"]),
                case["asr_confidence"],
                case["mt_confidence"],
                0.7,
                lookup_glossary(db_session, source),
            )
            kinds.update(span["kind"] for span in result.spans)
    return kinds


def labelled_kinds() -> set[str]:
    return set(re.findall(r"^  ([a-z_]+): \{", LABELS.read_text(encoding="utf-8"), re.MULTILINE))


def test_fixtures_still_exercise_a_broad_set_of_kinds(db_session) -> None:
    """Guard the guard: a shrunken fixture set would make this test vacuous."""
    kinds = produced_kinds(db_session)
    assert len(kinds) >= 12, f"fixtures only produced {sorted(kinds)}"
    assert {"allergy", "dose_number", "drug_name", "low_confidence"} <= kinds


def test_every_produced_risk_kind_has_a_ui_label(db_session) -> None:
    missing = sorted(produced_kinds(db_session) - labelled_kinds())
    assert not missing, (
        f"risk kinds with no Vietnamese label: {missing}. "
        f"Add them to {LABELS.relative_to(REPO_ROOT).as_posix()}."
    )
