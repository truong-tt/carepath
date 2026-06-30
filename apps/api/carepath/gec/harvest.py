"""Harvest real ASR confusions as datastore aliases (replaces hand-built G2P).

Vietnamese ASR mangles a code-switched term by *sound* ("reductase" -> "rê đắc
tay", "metformin" -> "mê pho min"). Rather than guess those renderings with a
hand-rolled pronunciation table — brittle, dialect-biased, and only as good as
whoever tuned it — we read how the deployed ASR *actually* mangles each term:

1. token-align every ``(gold_text, raw_asr)`` pair,
2. locate the term on the gold side,
3. record the ASR span aligned to it.

Those harvested surfaces are written back as datastore aliases, so the existing
lexical retriever recovers the term with no new matching code. The "phonetics"
are learned from Gipformer's own behaviour — accent/model specific, self-
calibrating, and updated for free every time new pairs are produced.

``ponytail:`` confusion mining is heuristic — token alignment + a width guard,
not forced phonetic alignment; min_count filters one-off noise. Raise min_count
on the full run if junk aliases appear.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from typing import Any, Iterable


def _tok(token: str) -> str:
    """Diacritic-folded, punctuation-stripped token key for alignment/matching."""

    t = unicodedata.normalize("NFD", token.lower())
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn").replace("đ", "d")
    return re.sub(r"[^a-z0-9]", "", t)


def _key(text: str) -> str:
    return " ".join(k for k in (_tok(w) for w in text.split()) if k)


def _gold_span(gold_keys: list[str], term: str) -> tuple[int, int] | None:
    """First contiguous token span of ``gold_keys`` equal to ``term`` (folded)."""

    needle = _key(term).split()
    if not needle:
        return None
    for i in range(0, len(gold_keys) - len(needle) + 1):
        if gold_keys[i : i + len(needle)] == needle:
            return i, i + len(needle)
    return None


def _aligned_asr_span(
    gold_keys: list[str],
    asr: list[str],
    asr_keys: list[str],
    gspan: tuple[int, int],
    max_extra: int = 2,
) -> str | None:
    """ASR token span aligned to the gold term span, via stdlib difflib opcodes."""

    start, end = gspan
    matcher = SequenceMatcher(a=gold_keys, b=asr_keys, autojunk=False)
    asr_idx: list[int] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "insert" or i2 <= start or i1 >= end:
            continue  # opcode does not touch the term's gold span
        asr_idx.extend(range(j1, j2))  # 'replace' / 'equal' region on the ASR side
    if not asr_idx:
        return None
    lo, hi = min(asr_idx), max(asr_idx)
    if (hi - lo + 1) > (end - start) + max_extra:  # diffuse alignment → unreliable
        return None
    return " ".join(asr[lo : hi + 1]).strip()


def harvest_aliases(
    pairs: Iterable[dict[str, Any]],
    terms: Iterable[str],
    min_count: int = 1,
    max_aliases: int = 4,
    min_similarity: float = 0.4,
    min_chars: int = 3,
) -> dict[str, list[str]]:
    """Map each term to the ASR renderings that replaced it across the pairs.

    A harvested span is kept only if it still *resembles* the term it replaced
    (character similarity ≥ ``min_similarity``): a real mangling of "testosterone"
    shares letters ("testo", "tester"), an alignment slip ("metcolan" for
    "Bartholin") does not. This is what stops harvested aliases from re-creating
    the over-retrieval the paper warns about. Verified against real Gipformer
    output, not invented examples.
    """

    terms = list(dict.fromkeys(terms))
    found: dict[str, Counter] = {t: Counter() for t in terms}
    for pair in pairs:
        gold = str(pair.get("gold_text") or "").split()
        asr = str(pair.get("raw_asr") or "").split()
        if not gold or not asr:
            continue
        gold_keys = [_tok(t) for t in gold]
        asr_keys = [_tok(t) for t in asr]
        asr_key = " ".join(k for k in asr_keys if k)
        for term in terms:
            tkey = _key(term)
            if not tkey or f" {tkey} " in f" {asr_key} ":
                continue  # ASR already rendered it correctly → no alias needed
            gspan = _gold_span(gold_keys, term)
            if gspan is None:
                continue
            span = _aligned_asr_span(gold_keys, asr, asr_keys, gspan)
            if not span or _key(span) == tkey:
                continue
            span_flat, term_flat = _key(span).replace(" ", ""), tkey.replace(" ", "")
            if len(span_flat) < min_chars:
                continue
            if SequenceMatcher(None, span_flat, term_flat).ratio() < min_similarity:
                continue  # alignment garbage, not a plausible mangling
            found[term][span.lower()] += 1

    out: dict[str, list[str]] = {}
    for term, counter in found.items():
        aliases = [a for a, c in counter.most_common(max_aliases) if c >= min_count]
        if aliases:
            out[term] = aliases
    return out


def enrich_datastore(
    payload: dict[str, Any] | list[dict[str, Any]],
    pairs: Iterable[dict[str, Any]],
    min_count: int = 1,
    max_aliases: int = 4,
) -> dict[str, Any] | list[dict[str, Any]]:
    """Add harvested ASR-confusion aliases to a datastore payload, in place.

    Enriched entries get ``allow_fuzzy=True`` so slight run-to-run ASR variation
    still matches via the retriever's fuzzy window, and keep a ``harvested``
    list so the additions are auditable / removable.
    """

    rows = payload["terms"] if isinstance(payload, dict) else payload
    harvested = harvest_aliases(pairs, [r["term"] for r in rows], min_count, max_aliases)
    enriched = 0
    for row in rows:
        new = harvested.get(row["term"])
        if not new:
            continue
        existing = {a.lower() for a in (row.get("aliases") or [])}
        existing.add(row["term"].lower())
        added = [a for a in new if a.lower() not in existing]
        if not added:
            continue
        row["aliases"] = list(row.get("aliases") or []) + added
        row["allow_fuzzy"] = True
        row["harvested"] = list(row.get("harvested") or []) + added
        enriched += 1

    if isinstance(payload, dict):
        meta = payload.setdefault("metadata", {})
        meta["harvested_terms"] = enriched
    return payload
