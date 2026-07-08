import pytest

from app.providers.base import GlossaryEntry
from app.risk import classify_risk


@pytest.mark.parametrize(
    ("source", "translation", "expected_tier", "expected_kind"),
    [
        ("đau ngực", "chest pain", "critical", "red_flag"),
        ("khó thở", "shortness of breath", "critical", "red_flag"),
        ("dị ứng penicillin", "allergic to penicillin", "critical", "allergy"),
        ("đang mang thai", "pregnant", "critical", "pregnancy"),
        ("đau chân trái", "left leg pain", "high", "laterality"),
        ("uống 500 mg", "take 500 mg", "high", "dose_number"),
        ("ngày 2 lần", "2 times a day", "high", "frequency_duration"),
        ("nhỏ mắt 1 giọt", "1 eye drop", "high", "route"),
        ("không uống thuốc", "do not take medicine", "high", "negation"),
    ],
)
def test_risk_rules_emit_expected_tiers(
    source: str,
    translation: str,
    expected_tier: str,
    expected_kind: str,
) -> None:
    result = classify_risk(source, translation, 0.99, 0.99, 0.7)

    assert result.tier == expected_tier
    assert expected_kind in {span["kind"] for span in result.spans}


def test_number_mismatch_is_critical() -> None:
    result = classify_risk("uống 1 viên", "take 2 tablets", 0.99, 0.99, 0.7)

    assert result.tier == "critical"
    assert "number_mismatch" in {span["kind"] for span in result.spans}


def test_negation_mismatch_is_critical() -> None:
    result = classify_risk("không dị ứng penicillin", "allergic to penicillin", 0.99, 0.99, 0.7)

    assert result.tier == "critical"
    assert "negation_mismatch" in {span["kind"] for span in result.spans}


def test_lasa_drug_hit_is_critical() -> None:
    result = classify_risk(
        "uống Lasix",
        "take Lasix",
        0.99,
        0.99,
        0.7,
        [GlossaryEntry(term_vi="Lasix", term_en="Lasix", kind="drug", lasa_group="Lasix")],
    )

    assert result.tier == "critical"
    assert "drug_name" in {span["kind"] for span in result.spans}


def test_low_confidence_is_flagged_without_hiding_other_tier() -> None:
    result = classify_risk("xin chào", "hello", 0.4, 0.99, 0.7)

    assert result.tier == "low"
    assert "low_confidence" in {span["kind"] for span in result.spans}
