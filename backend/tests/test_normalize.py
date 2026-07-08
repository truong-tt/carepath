import pytest

from app.normalize import (
    contains_folded,
    normalize_text,
    parse_vietnamese_number_words,
    strip_diacritics,
)


@pytest.mark.parametrize(
    ("words", "value"),
    [
        (["một"], 1),
        (["hai"], 2),
        (["ba"], 3),
        (["bốn"], 4),
        (["tư"], 4),
        (["năm"], 5),
        (["lăm"], 5),
        (["sáu"], 6),
        (["bảy"], 7),
        (["tám"], 8),
        (["chín"], 9),
        (["mười"], 10),
        (["mười", "một"], 11),
        (["mười", "lăm"], 15),
        (["hai", "mươi"], 20),
        (["hai", "mươi", "mốt"], 21),
        (["ba", "mươi", "lăm"], 35),
        (["một", "trăm"], 100),
        (["một", "trăm", "linh", "năm"], 105),
        (["một", "trăm", "hai", "mươi"], 120),
        (["năm", "trăm"], 500),
        (["một", "nghìn"], 1000),
        (["một", "nghìn", "hai", "trăm"], 1200),
        (["một", "rưỡi"], 1.5),
        (["nửa"], 0.5),
    ],
)
def test_parse_vietnamese_number_words(words: list[str], value: float) -> None:
    assert parse_vietnamese_number_words(words) == value


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Uống nửa viên", "Uống 0.5 viên"),
        ("Ngày hai lần", "Ngày 2 lần"),
        ("trong mười ngày", "trong 10 ngày"),
        ("Tái khám sau mười ngày", "Tái khám +10 days"),
        ("sau 5 ngày", "+5 days"),
        ("Năm trăm mi-li-gam", "500 mg"),
        ("uống 500 milligrams", "uống 500 mg"),
        ("tiêm 2 micrograms", "tiêm 2 mcg"),
        ("nhỏ 5 mi-li-lít", "nhỏ 5 ml"),
        ("uống một viên", "uống 1 viên"),
        ("uống hai gói", "uống 2 gói"),
        ("uống ba ống", "uống 3 ống"),
        ("uống bốn viên", "uống 4 viên"),
        ("uống năm viên", "uống 5 viên"),
        ("uống sáu viên", "uống 6 viên"),
        ("uống bảy viên", "uống 7 viên"),
        ("uống tám viên", "uống 8 viên"),
        ("uống chín viên", "uống 9 viên"),
        ("uống mười viên", "uống 10 viên"),
        ("uống mười lăm viên", "uống 15 viên"),
        ("uống hai mươi viên", "uống 20 viên"),
        ("uống hai mươi mốt viên", "uống 21 viên"),
        ("uống một trăm hai mươi mg", "uống 120 mg"),
        ("uống một trăm linh năm mg", "uống 105 mg"),
        ("uống một nghìn mg", "uống 1000 mg"),
        ("uống một rưỡi viên", "uống 1.5 viên"),
    ],
)
def test_normalize_text_research_cases(raw: str, expected: str) -> None:
    assert normalize_text(raw) == expected


def test_diacritic_helpers_support_glossary_fallback() -> None:
    assert strip_diacritics("thuốc kháng sinh") == "thuoc khang sinh"
    assert contains_folded("Benh nhan di ung thuoc", "dị ứng thuốc")
