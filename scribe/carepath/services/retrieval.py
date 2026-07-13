from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Protocol

from carepath_shared.normalize import normalize_for_match


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


class TermRetriever(Protocol):
    def retrieve(self, text: str, limit: int | None = None) -> list[RetrievedTerm]:
        ...


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


DEFAULT_SEMANTIC_MODEL = "bkai-foundation-models/vietnamese-bi-encoder"


class SemanticTermRetriever:
    """Cosine top-k retrieval (paper Eq. 1) with a Vietnamese-native bi-encoder.

    Uses ``bkai-foundation-models/vietnamese-bi-encoder`` (PhoBERT-base-v2) by
    default. That model *requires word-segmented input*, so both the datastore
    surfaces and the query are run through ``pyvi`` before encoding. Term/alias/
    vietnamese surfaces are embedded once and cached on first ``retrieve``.

    English-only code-switched NEs embed weakly here (PhoBERT is Vietnamese), so
    prefer ``HybridTermRetriever`` in practice — keep this for evaluation/ablation.
    """

    def __init__(
        self,
        lexicon_path: Path,
        top_k: int = 5,
        model_name: str = DEFAULT_SEMANTIC_MODEL,
    ):
        self.lexicon_path = lexicon_path
        self.top_k = top_k
        self.model_name = model_name
        self.entries = MedicalTermRetriever._load_entries(lexicon_path)
        self._model = None
        self._entry_index: list[TermEntry] = []
        self._embeddings = None

    def _ensure_index(self) -> None:
        if self._model is not None:
            return
        from sentence_transformers import SentenceTransformer  # type: ignore

        self._model = SentenceTransformer(self.model_name)
        surfaces: list[str] = []
        index: list[TermEntry] = []
        for entry in self.entries:
            names = [entry.term, *entry.aliases]
            if entry.vietnamese:
                names.append(entry.vietnamese)
            for name in names:
                if name and name.strip():
                    surfaces.append(segment_vietnamese(name))
                    index.append(entry)
        self._entry_index = index
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
        if self._embeddings is None or not self._entry_index:
            return []

        query = self._model.encode(
            [segment_vietnamese(text)], convert_to_numpy=True, normalize_embeddings=True
        )[0]
        scores = self._embeddings @ query  # cosine: embeddings are L2-normalized

        # A term can have several surfaces (term/alias/vietnamese); keep its best.
        best: dict[str, tuple[float, TermEntry]] = {}
        for idx, score in enumerate(scores):
            entry = self._entry_index[idx]
            current = best.get(entry.term)
            if current is None or score > current[0]:
                best[entry.term] = (float(score), entry)

        ranked = sorted(best.values(), key=lambda item: (-item[0], item[1].term.lower()))
        return [
            RetrievedTerm(
                term=entry.term,
                score=round(score, 4),
                category=entry.category,
                source=entry.source,
                vietnamese=entry.vietnamese,
                match_kind="semantic",
            )
            for score, entry in ranked[:limit]
        ]


class HybridTermRetriever:
    """Union of lexical + semantic candidates.

    Lexical matches take precedence — they are high-precision for the
    character/phoneme-mangled English NEs the paper notes dominate ASR errors —
    and remaining slots are filled with top semantic matches for Vietnamese
    phrasing the lexical matcher misses.
    """

    def __init__(
        self,
        lexical: TermRetriever,
        semantic: TermRetriever,
        top_k: int = 5,
    ):
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
        # Lexical first (match_kind != "semantic"), each group by score desc.
        merged.sort(key=lambda item: (item.match_kind == "semantic", -item.score, item.term.lower()))
        return merged[:limit]


def build_retriever(settings) -> TermRetriever:
    """Construct the retriever named by ``settings.retrieval_backend``.

    Default is ``lexical`` so the base install (no ``sentence-transformers``/
    ``pyvi``) and existing behavior are unchanged; ``semantic`` and ``hybrid``
    opt into the Vietnamese bi-encoder.
    """

    lexical = MedicalTermRetriever(settings.medical_lexicon_path, top_k=settings.retrieval_top_k)
    backend = getattr(settings, "retrieval_backend", "lexical")
    if backend == "lexical":
        return lexical
    semantic = SemanticTermRetriever(
        settings.medical_lexicon_path,
        top_k=settings.retrieval_top_k,
        model_name=getattr(settings, "semantic_model_name", DEFAULT_SEMANTIC_MODEL),
    )
    if backend == "semantic":
        return semantic
    if backend == "hybrid":
        return HybridTermRetriever(lexical, semantic, top_k=settings.retrieval_top_k)
    raise ValueError(
        f"RETRIEVAL_BACKEND must be 'lexical', 'semantic', or 'hybrid', got {backend!r}"
    )


def segment_vietnamese(text: str) -> str:
    """Word-segment Vietnamese for the bi-encoder (required by the model card).

    Falls back to the raw string if ``pyvi`` is unavailable so the retriever still
    runs (with slightly weaker matching) instead of crashing.
    """

    try:
        from pyvi import ViTokenizer  # type: ignore
    except Exception:
        return text
    return ViTokenizer.tokenize(text)


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
