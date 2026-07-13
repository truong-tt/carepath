from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_canonical_terms_cover_both_serving_targets() -> None:
    source = ROOT / "shared" / "carepath_shared" / "terms" / "medical_terms.json"
    terms = json.loads(source.read_text(encoding="utf-8"))["terms"]

    assert len(terms) == 192
    assert sum("scribe" in term["targets"] for term in terms) == 35
    assert sum("interpreter" in term["targets"] for term in terms) == 165
    assert all({"term_vi", "term_en", "kind", "aliases", "risk_flags", "targets"} <= term.keys() for term in terms)


def test_generated_term_artifacts_are_current() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/build_term_artifacts.py", "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
