"""Retrieval-Augmented Correction datastore lookup (paper §4.2 Step 2, Eq. 1).

Standalone copy used by the offline pipeline (pair building, evaluation,
leakage), kept separate from the runtime ``carepath.services.retrieval`` so the
research layer has no dependency on the serving path. Two retrievers:

* ``LexicalNERetriever`` — normalized exact / substring / fuzzy matching. Cheap,
  no ML deps, and high-precision for the character-mangled English NEs that the
  paper notes dominate ASR errors.
* ``SemanticNERetriever`` — cosine top-k with the Vietnamese bi-encoder
  (paper Eq. 1), lazily importing ``sentence-transformers``.

``build_ne_retriever`` picks ``lexical`` / ``semantic`` / ``hybrid``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from carepath_shared.normalize import normalize_for_match

DEFAULT_SEMANTIC_MODEL = "bkai-foundation-models/vietnamese-bi-encoder"


@dataclass(frozen=True)
class TermEntry:
    term: str
    category: str = "medical"
    aliases: tuple[str, ...] = ()
    vietnamese: str | None = None
    source: str = "lexicon"
    allow_fuzzy: bool = False

    @classmethod
    def from_dict(cls, row: dict) -> "TermEntry":
        aliases = row.get("aliases") or []
        if isinstance(aliases, str):
            aliases = [aliases]
        return cls(
            term=str(row["term"]),
            category=str(row.get("category", "medical")),
            aliases=tuple(str(a) for a in aliases),
            vietnamese=str(row["vietnamese"]) if row.get("vietnamese") is not None else None,
            source=str(row.get("source", "lexicon")),
            allow_fuzzy=bool(row.get("allow_fuzzy", False)),
        )


@dataclass(frozen=True)
class RetrievedTerm:
    term: str
    score: float
    category: str
    source: str
    match_kind: str = "exact"


def load_entries(path: Path) -> list[TermEntry]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["terms"] if isinstance(payload, dict) else payload
    return [TermEntry.from_dict(row) for row in rows]


class LexicalNERetriever:
    def __init__(self, datastore_path: Path, top_k: int = 5, fuzzy_threshold: float = 0.92):
        self.top_k = top_k
        self.fuzzy_threshold = fuzzy_threshold
        self.entries = load_entries(datastore_path)

    def retrieve(self, text: str, limit: int | None = None) -> list[RetrievedTerm]:
        limit = limit or self.top_k
        query = normalize_for_match(text)
        if not query:
            return []
        candidates: list[RetrievedTerm] = []
        for entry in self.entries:
            score, kind = self._score(query, entry)
            if score >= 0.75:
                candidates.append(
                    RetrievedTerm(entry.term, score, entry.category, entry.source, kind)
                )
        candidates.sort(key=lambda item: (-item.score, item.term.lower()))
        return candidates[:limit]

    def _score(self, query: str, entry: TermEntry) -> tuple[float, str]:
        names = [entry.term, *entry.aliases]
        if entry.vietnamese:
            names.append(entry.vietnamese)
        best, best_kind = 0.0, "none"
        for name in names:
            normalized = normalize_for_match(name)
            if not normalized:
                continue
            if re.search(rf"(?<!\w){re.escape(normalized)}(?!\w)", query):
                score, kind = 1.0, "exact"
            elif len(normalized) < 3:
                continue
            elif normalized in query:
                score, kind = 0.92, "substring"
            elif entry.allow_fuzzy:
                score, kind = _best_window_ratio(query, normalized), "fuzzy"
                if score < self.fuzzy_threshold:
                    continue
            else:
                continue
            if score > best:
                best, best_kind = score, kind
        return best, best_kind


class SemanticNERetriever:
    """Cosine top-k retrieval with a Vietnamese-native bi-encoder (paper Eq. 1)."""

    def __init__(self, datastore_path: Path, top_k: int = 5, model_name: str = DEFAULT_SEMANTIC_MODEL):
        self.top_k = top_k
        self.model_name = model_name
        self.entries = load_entries(datastore_path)
        self._model = None
        self._index: list[TermEntry] = []
        self._embeddings = None

    def _ensure_index(self) -> None:
        if self._model is not None:
            return
        from sentence_transformers import SentenceTransformer  # type: ignore

        self._model = SentenceTransformer(self.model_name)
        surfaces, index = [], []
        for entry in self.entries:
            names = [entry.term, *entry.aliases]
            if entry.vietnamese:
                names.append(entry.vietnamese)
            for name in names:
                if name and name.strip():
                    surfaces.append(segment_vietnamese(name))
                    index.append(entry)
        self._index = index
        self._embeddings = (
            self._model.encode(surfaces, convert_to_numpy=True, normalize_embeddings=True)
            if surfaces
            else None
        )

    def retrieve(self, text: str, limit: int | None = None) -> list[RetrievedTerm]:
        limit = limit or self.top_k
        if not text or not text.strip():
            return []
        self._ensure_index()
        if self._embeddings is None or not self._index:
            return []
        query = self._model.encode(
            [segment_vietnamese(text)], convert_to_numpy=True, normalize_embeddings=True
        )[0]
        scores = self._embeddings @ query
        best: dict[str, tuple[float, TermEntry]] = {}
        for idx, score in enumerate(scores):
            entry = self._index[idx]
            current = best.get(entry.term)
            if current is None or score > current[0]:
                best[entry.term] = (float(score), entry)
        ranked = sorted(best.values(), key=lambda item: (-item[0], item[1].term.lower()))
        return [
            RetrievedTerm(entry.term, round(score, 4), entry.category, entry.source, "semantic")
            for score, entry in ranked[:limit]
        ]


class HybridNERetriever:
    """Lexical matches first (high precision), semantic fills remaining slots."""

    def __init__(self, lexical, semantic, top_k: int = 5):
        self.lexical = lexical
        self.semantic = semantic
        self.top_k = top_k

    def retrieve(self, text: str, limit: int | None = None) -> list[RetrievedTerm]:
        limit = limit or self.top_k
        chosen: dict[str, RetrievedTerm] = {
            item.term: item for item in self.lexical.retrieve(text, limit)
        }
        if len(chosen) < limit:
            for item in self.semantic.retrieve(text, limit):
                if item.term not in chosen:
                    chosen[item.term] = item
                if len(chosen) >= limit:
                    break
        merged = list(chosen.values())
        merged.sort(key=lambda item: (item.match_kind == "semantic", -item.score, item.term.lower()))
        return merged[:limit]


def build_ne_retriever(
    datastore_path: Path,
    backend: str = "lexical",
    top_k: int = 5,
    model_name: str = DEFAULT_SEMANTIC_MODEL,
):
    lexical = LexicalNERetriever(datastore_path, top_k=top_k)
    if backend == "lexical":
        return lexical
    semantic = SemanticNERetriever(datastore_path, top_k=top_k, model_name=model_name)
    if backend == "semantic":
        return semantic
    if backend == "hybrid":
        return HybridNERetriever(lexical, semantic, top_k=top_k)
    raise ValueError(f"backend must be lexical/semantic/hybrid, got {backend!r}")


def segment_vietnamese(text: str) -> str:
    """Word-segment Vietnamese for the bi-encoder (required by its model card)."""

    try:
        from pyvi import ViTokenizer  # type: ignore
    except Exception:
        return text
    return ViTokenizer.tokenize(text)


def _best_window_ratio(query: str, candidate: str) -> float:
    q_tokens = query.split()
    c_tokens = candidate.split()
    if not q_tokens or not c_tokens:
        return 0.0
    sizes = {max(1, len(c_tokens) - 1), len(c_tokens), len(c_tokens) + 1}
    best = SequenceMatcher(None, query, candidate).ratio() * 0.75
    for size in sizes:
        for idx in range(0, max(1, len(q_tokens) - size + 1)):
            window = " ".join(q_tokens[idx : idx + size])
            best = max(best, SequenceMatcher(None, window, candidate).ratio())
    return best
