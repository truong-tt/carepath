from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path


@dataclass(frozen=True)
class TermEntry:
    term: str
    category: str = "medical"
    aliases: tuple[str, ...] = field(default_factory=tuple)
    vietnamese: str | None = None
    source: str = "lexicon"
    allow_fuzzy: bool = False

    @classmethod
    def from_dict(cls, row: dict[str, object]) -> "TermEntry":
        aliases = row.get("aliases") or []
        if isinstance(aliases, str):
            aliases = [aliases]
        return cls(
            term=str(row["term"]),
            category=str(row.get("category", "medical")),
            aliases=tuple(str(item) for item in aliases),
            vietnamese=(
                str(row["vietnamese"]) if row.get("vietnamese") is not None else None
            ),
            source=str(row.get("source", "lexicon")),
            allow_fuzzy=bool(row.get("allow_fuzzy", False)),
        )


@dataclass(frozen=True)
class RetrievedTerm:
    term: str
    score: float
    category: str
    source: str
    vietnamese: str | None = None
    match_kind: str = "exact"


class MedicalTermRetriever:
    def __init__(self, lexicon_path: Path, top_k: int = 5, fuzzy_threshold: float = 0.92):
        self.lexicon_path = lexicon_path
        self.top_k = top_k
        self.fuzzy_threshold = fuzzy_threshold
        self.entries = self._load_entries(lexicon_path)

    def retrieve(self, text: str, limit: int | None = None) -> list[RetrievedTerm]:
        limit = limit or self.top_k
        query = normalize_for_match(text)
        if not query:
            return []

        candidates: list[RetrievedTerm] = []
        for entry in self.entries:
            score, source, match_kind = self._score_entry(query, entry)
            if score >= 0.75:
                candidates.append(
                    RetrievedTerm(
                        term=entry.term,
                        score=score,
                        category=entry.category,
                        source=source,
                        vietnamese=entry.vietnamese,
                        match_kind=match_kind,
                    )
                )

        candidates.sort(key=lambda item: (-item.score, item.term.lower()))
        return candidates[:limit]

    def _score_entry(self, query: str, entry: TermEntry) -> tuple[float, str, str]:
        names = [entry.term, *entry.aliases]
        if entry.vietnamese:
            names.append(entry.vietnamese)

        best = 0.0
        best_source = entry.term
        best_kind = "none"
        for name in names:
            normalized = normalize_for_match(name)
            if not normalized:
                continue
            if re.search(rf"(?<!\w){re.escape(normalized)}(?!\w)", query):
                score = 1.0
                kind = "exact"
            elif len(normalized) < 3:
                continue
            elif normalized in query:
                score = 0.92
                kind = "substring"
            elif entry.allow_fuzzy:
                score = _best_window_ratio(query, normalized)
                kind = "fuzzy"
                if score < self.fuzzy_threshold:
                    continue
            else:
                continue
            if score > best:
                best = score
                best_source = name
                best_kind = kind
        return best, best_source, best_kind

    @staticmethod
    def _load_entries(path: Path) -> list[TermEntry]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        rows = payload["terms"] if isinstance(payload, dict) else payload
        return [TermEntry.from_dict(row) for row in rows]


def normalize_for_match(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("đ", "d")
    text = re.sub(r"[^a-z0-9%/.,]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _best_window_ratio(query: str, candidate: str) -> float:
    query_tokens = query.split()
    candidate_tokens = candidate.split()
    if not query_tokens or not candidate_tokens:
        return 0.0

    window_sizes = {
        max(1, len(candidate_tokens) - 1),
        len(candidate_tokens),
        len(candidate_tokens) + 1,
    }
    best = SequenceMatcher(None, query, candidate).ratio() * 0.75
    for size in window_sizes:
        for idx in range(0, max(1, len(query_tokens) - size + 1)):
            window = " ".join(query_tokens[idx : idx + size])
            best = max(best, SequenceMatcher(None, window, candidate).ratio())
    return best
