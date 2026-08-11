"""The eval's preservation metrics compare meaning across two languages.

They used to compare surface tokens, which scored correct translations as
failures: "Tiêm 1 ống" -> "Inject 1 ampoule" looked like a unit error, and a
Vietnamese yes/no question ending in "không" looked like a dropped negation.
Published figures were therefore misleading.

Both directions matter. A metric that never fails is as useless as one that
always does, so half of these assert that a genuinely broken translation is
still caught.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))

from run_eval import (  # noqa: E402
    canonical_laterality,
    canonical_numbers,
    canonical_units,
    negation_count,
)

NEGATION_TERMS = [
    "không",
    "chưa",
    "ngưng",
    "dừng",
    "không còn",
    "not",
    "no",
    "never",
    "stop",
    "stopped",
    "without",
]


def negations(text: str) -> int:
    return negation_count(text, NEGATION_TERMS)


# --- units: the same dose form, named in two languages -----------------------


@pytest.mark.parametrize(
    ("vi", "en"),
    [
        ("Tiêm 1 ống", "Inject 1 ampoule"),
        ("Uống 2 gói", "Take 2 sachets"),
        ("Uống 1 viên", "Take 1 tablet"),
        ("Nhỏ 2 giọt", "Instil 2 drops"),
        ("Uống 500 mg", "Take 500 milligrams"),
    ],
)
def test_matching_dose_forms_count_as_preserved(vi: str, en: str) -> None:
    assert canonical_units(vi) == canonical_units(en)


@pytest.mark.parametrize(
    ("vi", "en"),
    [
        ("Uống 2 viên", "Take 2 sachets"),  # tablet became sachet
        ("Tiêm 1 ống", "Inject 1 tablet"),  # injection became oral
        ("Uống 1 viên", "Take it"),  # form dropped entirely
    ],
)
def test_a_changed_dose_form_still_fails(vi: str, en: str) -> None:
    assert canonical_units(vi) != canonical_units(en)


# --- numbers: digits, spelled words, and decimal separators ------------------


@pytest.mark.parametrize(
    ("vi", "en"),
    [
        ("ngày 2 lần", "Twice a day"),
        ("uống 1 viên", "Take one tablet"),
        ("trong 3 ngày", "For three days"),
        ("sốt trên 38,5 độ C", "Fever above 38.5 degrees C"),  # comma vs period
        ("uống 500 mg", "Take 500 mg"),
    ],
)
def test_equivalent_numbers_count_as_preserved(vi: str, en: str) -> None:
    assert canonical_numbers(vi) == canonical_numbers(en)


@pytest.mark.parametrize(
    ("vi", "en"),
    [
        ("uống 500 mg", "Take 50 mg"),  # order of magnitude
        ("uống 500 mg", "Take one tablet"),  # dose replaced
        ("ngày 2 lần", "Three times a day"),  # frequency changed
        ("uống 500 mg", "Take the medicine"),  # dose dropped
    ],
)
def test_a_changed_number_still_fails(vi: str, en: str) -> None:
    assert canonical_numbers(vi) != canonical_numbers(en)


# --- negation: the error class that actually harms patients ------------------


@pytest.mark.parametrize(
    ("vi", "en"),
    [
        ("Anh có dị ứng thuốc nào không?", "Do you have any drug allergy?"),
        ("Anh từng mổ tim chưa?", "Have you ever had heart surgery?"),
        ("Con thấy mệt không?", "Do you feel tired?"),
        ("Anh còn đau không", "Are you still in pain"),
    ],
)
def test_a_yes_no_question_is_not_a_negation(vi: str, en: str) -> None:
    """"không"/"chưa" at the end make a question, not a negative."""
    assert negations(vi) == negations(en)


@pytest.mark.parametrize(
    ("vi", "en"),
    [
        ("không dị ứng penicillin", "allergic to penicillin"),  # dropped the "not"
        ("chưa uống thuốc", "took the medicine"),  # reversed
        ("không còn đau ngực", "chest pain"),  # dropped
    ],
)
def test_a_flipped_negation_still_fails(vi: str, en: str) -> None:
    assert negations(vi) != negations(en)


@pytest.mark.parametrize(
    "english",
    ["Hospital noise.", "He cannot hear clearly.", "Nothing unusual.", "There is a nodule."],
)
def test_a_cue_buried_inside_a_word_is_not_a_negation(english: str) -> None:
    """Substring counting read "no" inside noise, cannot, nothing and nodule."""
    assert negations(english) == 0


def test_a_repeated_dose_form_is_not_a_unit_error() -> None:
    """One instruction may name the form twice: "Eye drops 1 drop"."""
    assert canonical_units("nhỏ mắt 1 giọt") == canonical_units("Eye drops 1 drop")
    assert canonical_units("nhỏ tai 3 giọt") == canonical_units("Ear drops 3 drop")


def test_negation_inside_a_sentence_is_still_counted() -> None:
    """Only a trailing particle is stripped; mid-sentence "không" is real."""
    assert negations("không dị ứng penicillin") == 1
    assert negations("Bệnh nhân không dị ứng, đúng không?") == 1


# --- laterality --------------------------------------------------------------


def test_matching_laterality_counts_as_preserved() -> None:
    assert canonical_laterality("đau tay trái") == canonical_laterality("pain in the left hand")


def test_swapped_laterality_still_fails() -> None:
    assert canonical_laterality("đau tay trái") != canonical_laterality("pain in the right hand")
