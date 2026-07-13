from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from carepath.services.retrieval import MedicalTermRetriever, normalize_for_match


class RetrievalTests(unittest.TestCase):
    def test_normalize_for_match_removes_vietnamese_diacritics(self) -> None:
        self.assertEqual(normalize_for_match("tăng huyết áp"), "tang huyet ap")

    def test_retrieve_exact_and_alias_terms(self) -> None:
        retriever = MedicalTermRetriever(Path("data/medical_lexicon.json"), top_k=5)
        terms = retriever.retrieve("bệnh nhân SpO2 98% và cao huyết áp")
        names = [item.term for item in terms]
        self.assertIn("SpO2", names)
        self.assertIn("hypertension", names)

    def test_short_aliases_do_not_match_inside_words(self) -> None:
        retriever = MedicalTermRetriever(Path("data/medical_lexicon.json"), top_k=10)
        terms = retriever.retrieve(
            "benh nhan dau nguc spo2 98 % huyet ap 120 tren 80 mmhg "
            "Phong kham noi tong quat"
        )
        names = [item.term for item in terms]
        self.assertIn("SpO2", names)
        self.assertNotIn("potassium", names)
        self.assertNotIn("hemoglobin", names)
        self.assertNotIn("glucose", names)

    def test_hernia_transcript_does_not_retrieve_unrelated_terms(self) -> None:
        retriever = MedicalTermRetriever(Path("data/medical_lexicon.json"), top_k=10)
        text = (
            "Bệnh nhân 32 tuổi có khối phồng vùng bẹn, xuất hiện khi đứng "
            "ho hoặc rặn, biến mất khi nằm, nghi thoát vị bẹn phải."
        )
        names = [item.term for item in retriever.retrieve(text)]
        self.assertNotIn("platelet", names)
        self.assertNotIn("glucose", names)
        self.assertNotIn("X-ray", names)
        self.assertNotIn("diabetes mellitus", names)
        self.assertNotIn("diastolic", names)


if __name__ == "__main__":
    unittest.main()
