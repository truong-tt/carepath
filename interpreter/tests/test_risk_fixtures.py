import json
from collections import Counter
from pathlib import Path

from app.glossary import lookup_glossary, seed_glossary
from app.normalize import normalize_text
from app.risk import classify_risk

FIXTURE = Path(__file__).parents[1] / "eval" / "fixtures" / "risk_cases.jsonl"
PRECISION_FIXTURE = (
    Path(__file__).parents[1] / "eval" / "fixtures" / "risk_precision_cases.jsonl"
)
SEVERITY_ORDER = ["low", "medium", "high", "critical"]


def test_risk_fixture_cases(db_session) -> None:
    seed_glossary(db_session)
    cases = [json.loads(line) for line in FIXTURE.read_text(encoding="utf-8").splitlines()]
    counts = Counter(case["failure_mode"] for case in cases)

    assert set(counts) == set(range(1, 31))
    assert all(count >= 3 for count in counts.values())

    for case in cases:
        source = normalize_text(case["source"])
        result = classify_risk(
            source,
            normalize_text(case["translation"]),
            case["asr_confidence"],
            case["mt_confidence"],
            0.7,
            lookup_glossary(db_session, source),
        )
        kinds = {span["kind"] for span in result.spans}
        assert result.tier == case["expected_tier"], case["id"]
        assert set(case["expected_kinds"]) <= kinds, case["id"]


def test_risk_precision_cases(db_session) -> None:
    """Guard both directions of diacritic matching.

    The main fixture only asserts that expected kinds are present, so it cannot
    catch a false positive. These cases assert that benign Vietnamese stays
    below a confirmation gate, and that undiacritized ASR text still matches.
    """
    seed_glossary(db_session)
    cases = [
        json.loads(line) for line in PRECISION_FIXTURE.read_text(encoding="utf-8").splitlines()
    ]
    assert cases

    for case in cases:
        source = normalize_text(case["source"])
        result = classify_risk(
            source,
            normalize_text(case["translation"]),
            case["asr_confidence"],
            case["mt_confidence"],
            0.7,
            lookup_glossary(db_session, source),
        )
        kinds = {span["kind"] for span in result.spans}

        assert SEVERITY_ORDER.index(result.tier) <= SEVERITY_ORDER.index(case["max_tier"]), (
            f"{case['id']}: tier {result.tier} exceeds {case['max_tier']} ({sorted(kinds)})"
        )
        offending = kinds & set(case["forbidden_kinds"])
        assert not offending, f"{case['id']}: false positive {sorted(offending)}"
        if "expected_tier" in case:
            assert result.tier == case["expected_tier"], case["id"]
        assert set(case.get("expected_kinds", [])) <= kinds, case["id"]
