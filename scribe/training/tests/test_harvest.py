"""Data-driven ASR-confusion harvesting (paper Limitation #1, learned not guessed).

Positive cases below are copied from REAL Gipformer output on ViMedCSS
(artifacts/gec_pairs/vimedcss_gipformer_pairs_smoke.jsonl): "reductase" is
transcribed "REDO TAY", "testosterone" -> "TESTO". They are observed behaviour,
not invented manglings. The real-artifact test runs the full file when present.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scribe"))

from gec.harvest import enrich_datastore, harvest_aliases, rows_for_alias_mining
from carepath.services.retrieval import MedicalTermRetriever

REAL_PAIRS = Path("artifacts/gec_pairs/vimedcss_gipformer_pairs_smoke.jsonl")


class HarvestLogicTests(unittest.TestCase):
    def test_held_out_confusion_is_never_mined(self) -> None:
        pairs = [
            {
                "split": "train",
                "gold_text": "nam testosterone thành",
                "raw_asr": "nam testosterone thành",
            },
            {
                "split": "hard",
                "gold_text": "nam testosterone thành",
                "raw_asr": "nam testo thành",
            },
        ]
        mined = harvest_aliases(
            rows_for_alias_mining(pairs), ["testosterone"], min_count=1
        )
        self.assertNotIn("testosterone", mined)

    def test_harvests_real_renderings_and_skips_clean(self) -> None:
        pairs = [
            {"gold_text": "5 alpha reductase là một enzyme",
             "raw_asr": "NĂMFA REDO TAY LÀ MỘT ENZYM"},               # reductase -> redo tay
            {"gold_text": "hóc môn nam testosterone thành dạng",
             "raw_asr": "HÓC MÔN NAM TESTO THÀNH DẠNG"},              # testosterone -> testo
            {"gold_text": "bệnh nhân đo SpO2", "raw_asr": "bệnh nhân đo SpO2"},  # clean
        ]
        out = harvest_aliases(pairs, ["reductase", "testosterone", "SpO2"])
        self.assertTrue(any("redo" in a for a in out.get("reductase", [])))
        self.assertIn("testo", out.get("testosterone", []))
        self.assertNotIn("SpO2", out)  # correctly transcribed -> no alias

    def test_plausibility_guard_drops_alignment_garbage(self) -> None:
        # term maps to a span sharing no letters with it -> must be rejected.
        pairs = [{"gold_text": "đo nồng độ glucose trong máu",
                  "raw_asr": "đo nồng độ wwww trong máu"}]
        self.assertNotIn("glucose", harvest_aliases(pairs, ["glucose"], min_similarity=0.4))

    def test_enriched_datastore_recovers_mangled_term(self) -> None:
        payload = {"terms": [
            {"term": "testosterone", "category": "biomarker", "aliases": [],
             "vietnamese": None, "source": "lexicon", "allow_fuzzy": False},
        ]}
        enrich_datastore(payload, [
            {"gold_text": "nam testosterone thành", "raw_asr": "NAM TESTO THÀNH"},
        ], min_count=1)
        entry = payload["terms"][0]
        self.assertIn("testo", entry["aliases"])
        self.assertTrue(entry["allow_fuzzy"])
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ds.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            names = [t.term for t in MedicalTermRetriever(path, top_k=5).retrieve("lượng testo cao")]
            self.assertIn("testosterone", names)


@unittest.skipUnless(REAL_PAIRS.exists(), "real Gipformer smoke pairs not present")
class RealArtifactTests(unittest.TestCase):
    def test_harvest_over_real_gipformer_pairs(self) -> None:
        rows = [json.loads(line) for line in REAL_PAIRS.read_text(encoding="utf-8").splitlines() if line]
        if not any("gipformer" in str(row.get("asr_model", "")).lower() for row in rows):
            self.skipTest("artifact is not a real Gipformer decode")
        terms = sorted({t for r in rows for t in (r.get("gold_terms") or [])} | {"reductase", "testosterone"})
        out = harvest_aliases(rows, terms, min_count=1)
        # real renderings are captured, and the over-short junk ("hb") is filtered
        self.assertTrue(any("testo" in a for a in out.get("testosterone", [])))
        for aliases in out.values():
            for alias in aliases:
                self.assertGreaterEqual(len(alias.replace(" ", "")), 3)


if __name__ == "__main__":
    unittest.main()
