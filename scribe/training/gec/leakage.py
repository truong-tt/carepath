"""Leakage / memorization checks for synthetic transcripts (paper App. C / Table 6).

Two layers:

* **Generation guard** (pure python) — ``duplicate_rejection_reason`` rejects a
  candidate whose n-gram overlap with any real or already-accepted transcript is
  too high, so obvious copies never enter the dataset.

* **Audit report** (lazy SentenceBERT + sacrebleu) — ``leakage_report`` reproduces
  paper Table 6: for each synthetic transcript it finds the most similar real
  transcript by SentenceBERT cosine similarity, then reports the mean cosine and
  the mean BLEU(1-3) against that nearest neighbour. High cosine + low BLEU is the
  paper's evidence that the synthetic data is *in-domain but not memorized*.
"""

from __future__ import annotations

from gec.metrics import normalize_text


def ngram_overlap(candidate: str, reference: str, n: int = 3) -> float:
    cand = _ngrams(normalize_text(candidate).split(), n)
    ref = _ngrams(normalize_text(reference).split(), n)
    if not cand or not ref:
        return 0.0
    return len(cand & ref) / len(cand)


def duplicate_rejection_reason(
    candidate: str,
    references: list[str],
    max_ngram_overlap: float = 0.72,
) -> str | None:
    """Return a reason string if ``candidate`` is a near-duplicate, else ``None``."""

    for reference in references:
        overlap = ngram_overlap(candidate, reference)
        if overlap >= max_ngram_overlap:
            return f"near_duplicate_ngram_overlap:{overlap:.3f}"
    return None


def leakage_report(
    synthetic_texts: list[str],
    real_texts: list[str],
    model_name: str = "bkai-foundation-models/vietnamese-bi-encoder",
    dataset_label: str = "synthetic",
) -> dict:
    """Mean nearest-neighbour cosine similarity + BLEU (paper Table 6).

    Requires ``sentence-transformers`` and ``sacrebleu`` (training extras). Raises
    a clear error if they are missing rather than silently degrading, because a
    leakage audit that does not actually embed/score would be misleading.
    """

    if not synthetic_texts or not real_texts:
        return {
            "dataset": dataset_label,
            "n_synthetic": len(synthetic_texts),
            "n_real": len(real_texts),
            "mean_cosine_similarity": None,
            "mean_bleu": None,
            "note": "empty input",
        }

    try:
        import numpy as np  # type: ignore
        from sentence_transformers import SentenceTransformer  # type: ignore
        from sacrebleu.metrics import BLEU  # type: ignore
    except ImportError as exc:  # pragma: no cover - exercised only with extras
        raise ImportError(
            "leakage_report needs the training extras: pip install "
            "'sentence-transformers' sacrebleu"
        ) from exc

    from gec.retrieval import segment_vietnamese

    model = SentenceTransformer(model_name)
    syn_emb = model.encode(
        [segment_vietnamese(t) for t in synthetic_texts],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    real_emb = model.encode(
        [segment_vietnamese(t) for t in real_texts],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    sims = syn_emb @ real_emb.T  # cosine (rows are L2-normalized)
    nearest = sims.argmax(axis=1)
    best_cos = sims.max(axis=1)

    bleu = BLEU(effective_order=True)
    bleu_scores = [
        bleu.sentence_score(synthetic_texts[i], [real_texts[int(nearest[i])]]).score / 100.0
        for i in range(len(synthetic_texts))
    ]

    return {
        "dataset": dataset_label,
        "n_synthetic": len(synthetic_texts),
        "n_real": len(real_texts),
        "model": model_name,
        "mean_cosine_similarity": round(float(np.mean(best_cos)), 4),
        "max_cosine_similarity": round(float(np.max(best_cos)), 4),
        "mean_bleu": round(float(np.mean(bleu_scores)), 4),
        "max_bleu": round(float(np.max(bleu_scores)), 4),
        "interpretation": (
            "High cosine + low BLEU => synthetic data is in-domain but not "
            "memorized (paper Table 6)."
        ),
    }


def _ngrams(tokens: list[str], n: int) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return set()
    return {tuple(tokens[idx : idx + n]) for idx in range(len(tokens) - n + 1)}
