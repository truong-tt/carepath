from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for package_dir in ("shared", "interpreter", "scribe", "scribe/training"):
    sys.path.insert(0, str(ROOT / package_dir))

from app.normalize import normalize_text as interpreter_normalize_text  # noqa: E402
from carepath.evaluation import normalize_text as scribe_metric_normalize_text  # noqa: E402
from carepath.services.retrieval import normalize_for_match as scribe_normalize_for_match  # noqa: E402
from carepath_shared.normalize import (  # noqa: E402
    normalize_for_match,
    normalize_for_metrics,
    normalize_text,
)
from gec.metrics import normalize_text as training_metric_normalize_text  # noqa: E402
from gec.retrieval import normalize_for_match as training_normalize_for_match  # noqa: E402


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (" Uống nửa viên ", "Uống 0.5 viên"),
        ("uống nửa viên, ngày hai lần", "uống 0.5 viên, ngày 2 lần"),
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
        ("uống một trăm linh năm mg", "uống 105 mg"),
        ("Ba của cháu bị đau bụng", "Ba của cháu bị đau bụng"),
        ("anh Tư đến khám", "anh Tư đến khám"),
    ],
)
def test_interpreter_normalization_characterization(text: str, expected: str) -> None:
    assert normalize_text(text) == expected
    assert interpreter_normalize_text(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (" SpO2 98% ", "spo2 98%"),
        ("Bệnh nhân\tĐAU ngực", "bệnh nhân đau ngực"),
        ("Năm trăm mi-li-gam", "năm trăm mi-li-gam"),
        ("TÁI khám sau mười ngày", "tái khám sau mười ngày"),
        ("Metformin 500 MG", "metformin 500 mg"),
        ("ĐO HUYẾT ÁP 120 mmHg", "đo huyết áp 120 mmhg"),
        ("Viêm phổi COVID-19", "viêm phổi covid-19"),
        ("NaCl 0,9%", "nacl 0,9%"),
        ("  HbA1c\n7.2%  ", "hba1c 7.2%"),
        ("Bác sĩ Nguyễn Văn A", "bác sĩ nguyễn văn a"),
        ("PHẢI / trái", "phải / trái"),
        ("Ceftriaxone 1 g", "ceftriaxone 1 g"),
        ("đau bụng  ,  sốt", "đau bụng , sốt"),
        ("  sáu   tháng  ", "sáu tháng"),
        ("SpO₂ 98 %", "spo₂ 98 %"),
        ("µg", "µg"),
        ("HỒ SƠ NFC", "hồ sơ nfc"),
    ],
)
def test_metric_normalization_characterization(text: str, expected: str) -> None:
    assert normalize_for_metrics(text) == expected
    assert scribe_metric_normalize_text(text) == expected
    assert training_metric_normalize_text(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("tăng huyết áp", "tang huyet ap"),
        ("Bệnh nhân SpO2 98%", "benh nhan spo2 98%"),
        ("Đau ngực, khó thở.", "dau nguc, kho tho."),
        ("NaCl 0,9% / glucose", "nacl 0,9% / glucose"),
        ("HbA1c: 7.2%", "hba1c 7.2%"),
        ("Ceftriaxone 1 g", "ceftriaxone 1 g"),
        ("PHẢI—trái", "phai trai"),
        ("Bác sĩ Nguyễn Văn A", "bac si nguyen van a"),
        ("COVID-19 (PCR+)", "covid 19 pcr"),
        ("mg/dL", "mg/dl"),
        ("  đo   huyết áp  ", "do huyet ap"),
        ("SpO₂ 98%", "spo 98%"),
        ("điều trị 5 µg", "dieu tri 5 g"),
        ("A/B,C.D", "a/b,c.d"),
        ("nhiệt độ 38,5°C", "nhiet do 38,5 c"),
        ("sốc phản vệ!", "soc phan ve"),
        ("xét nghiệm CRP (mg/L)", "xet nghiem crp mg/l"),
    ],
)
def test_retrieval_normalization_characterization(text: str, expected: str) -> None:
    assert normalize_for_match(text) == expected
    assert scribe_normalize_for_match(text) == expected
    assert training_normalize_for_match(text) == expected
