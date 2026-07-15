"""Named-entity / code-switch term datastore (paper §4.2 Step 1).

The paper runs spaCy ``en-core-web-sm`` over every transcript (real *and*
synthetic) and stores the extracted NEs. English NER does not fit Vietnamese
code-switched medical text, so CarePath extracts the entities that actually drive
ASR errors here: the English/Latin medical tokens embedded in otherwise-Vietnamese
speech. Because ViMedCSS gold transcripts carry full Vietnamese diacritics, a
diacritic-free Latin token is a high-precision signal of a code-switch term
(``SpO2``, ``HbA1c``, ``metformin``, ``COPD`` …).

The datastore unions three sources, matching the paper's "extract from all
transcriptions, including synthetic":

1. the curated medical lexicon seed,
2. dataset-provided ``cs_terms_list`` annotations, and
3. tokens mined from gold / synthetic transcripts via ``extract_code_switch_terms``.
"""

from __future__ import annotations

import json
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

from gec.metrics import split_terms

# ASCII tokens that are Vietnamese particles or generic English stopwords — not NEs.
_STOPWORDS = {
    "a", "an", "and", "or", "the", "is", "are", "of", "to", "in", "on", "for",
    "with", "co", "khong", "la", "va", "co2",  # co2 handled separately below if real
    "benh", "nhan", "bac", "si", "ngay", "gio",
}
# Keep these even though short / common — they are real medical entities.
_FORCE_KEEP = {"co2", "o2", "t2", "t3", "t4", "b12", "d3"}


def has_vietnamese_diacritics(token: str) -> bool:
    """True if the token carries a Vietnamese tone/vowel mark or đ."""

    if "đ" in token or "Đ" in token:
        return True
    decomposed = unicodedata.normalize("NFD", token)
    return any(unicodedata.category(ch) == "Mn" for ch in decomposed)


def extract_code_switch_terms(text: str) -> list[str]:
    """Mine code-switch / NE candidate surfaces from a (diacritic-bearing) transcript."""

    found: list[str] = []
    for raw in text.split():
        token = raw.strip().strip(".,;:!?()[]\"'")
        if not token or has_vietnamese_diacritics(token):
            continue
        lower = token.lower()
        if lower in _FORCE_KEEP:
            found.append(token)
            continue
        if not any(ch.isalpha() for ch in token):
            continue  # pure numbers / units handled by metrics, not the datastore
        if len(token) < 2:
            continue
        has_digit = any(ch.isdigit() for ch in token)
        is_acronym = token.isupper() and len(token) >= 2
        is_mixedcase = token != lower and token != token.upper()  # SpO2, HbA1c
        looks_english = len(token) >= 3 and lower not in _STOPWORDS
        if has_digit or is_acronym or is_mixedcase or looks_english:
            found.append(token)
    return found


def build_datastore(
    lexicon_path: Path,
    pair_paths: list[Path] | None = None,
    transcript_fields: tuple[str, ...] = ("gold_text", "clean_text", "segment_text"),
    dataset: str | None = None,
    splits: tuple[str, ...] = ("train",),
    limit_per_split: int | None = None,
    dataset_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a term datastore JSON payload (compatible with the retriever's loader)."""

    terms: dict[str, dict[str, Any]] = {}
    counts: Counter[str] = Counter()

    for entry in _load_lexicon(lexicon_path):
        key = _normalize_key(entry["term"])
        terms[key] = {
            **entry,
            "source": entry.get("source", "curated_lexicon"),
            "allow_fuzzy": bool(entry.get("allow_fuzzy", False)),
        }

    for pair_path in pair_paths or []:
        for row in _read_jsonl(pair_path):
            for term in split_terms(row.get("cs_terms_list") or row.get("gold_terms")):
                _merge_term(terms, counts, term, source="annotation")
            for field in transcript_fields:
                value = row.get(field)
                if value:
                    for term in extract_code_switch_terms(str(value)):
                        _merge_term(terms, counts, term, source="mined")

    if dataset:
        from datasets import load_dataset  # type: ignore
        from gec.manifest import load_approved_hf_split

        for split in splits:
            data = (
                load_approved_hf_split(dataset, split, dataset_manifest)
                if dataset_manifest
                else load_dataset(dataset, split=split)
            )
            # Text-only job: drop every other column (above all ``audio``) before
            # iterating — the datasets Audio feature decodes each clip on row
            # access, which turns a sub-minute text scan into hours of decode.
            keep = [c for c in ("cs_terms_list", "segment_text") if c in data.column_names]
            if keep:
                data = data.select_columns(keep)
            if limit_per_split:
                data = data.select(range(min(limit_per_split, len(data))))
            for row in data:
                for term in split_terms(row.get("cs_terms_list")):
                    _merge_term(terms, counts, term, source=f"{dataset}:{split}")
                if row.get("segment_text"):
                    for term in extract_code_switch_terms(str(row["segment_text"])):
                        _merge_term(terms, counts, term, source=f"{dataset}:{split}")

    return {
        "metadata": {
            "version": 1,
            "term_count": len(terms),
            "sources": {
                "lexicon": str(lexicon_path),
                "pairs": [str(p) for p in (pair_paths or [])],
                "dataset": dataset,
            },
        },
        "terms": sorted(terms.values(), key=lambda item: item["term"].lower()),
    }


def write_datastore(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _merge_term(
    terms: dict[str, dict[str, Any]],
    counts: Counter[str],
    term: str,
    source: str,
) -> None:
    clean = term.strip()
    if not clean:
        return
    key = _normalize_key(clean)
    counts[key] += 1
    if key not in terms:
        terms[key] = {
            "term": clean,
            "category": "code_switch",
            "aliases": [],
            "vietnamese": None,
            "source": source,
            "allow_fuzzy": False,
            "frequency": 0,
        }
    terms[key]["frequency"] = int(counts[key])


def _load_lexicon(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["terms"] if isinstance(payload, dict) else payload
    return [dict(row) for row in rows]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _normalize_key(term: str) -> str:
    return " ".join(term.lower().split())
