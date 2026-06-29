"""Evaluation tables for DARAG (paper Tables 3 & 4) — no ML dependencies.

Two reports over a predictions JSONL (rows carrying ``gold_text``, ``raw_asr`` and
any correction columns):

* ``wer_report`` — paper Table 3 style: per prediction column, per split, the
  averaged WER/CER/term-F1/number-unit/overcorrection. Consumed by ``gate``.
* ``ne_f1_table`` — **paper Table 4**: micro-F1 of code-switched NEs per method
  (Baseline = ``raw_asr``, +GEC = LLM/RAG ``corrected_text``, +DARAG = ``gec_pred``,
  +DARAG w/ ID NE = ``gec_pred_id_ne``) split into ID vs OOD. Methods whose column
  is absent are skipped, so the same function serves smoke and full runs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from carepath.gec.config import ID_SPLITS, OOD_SPLITS
from carepath.gec.metrics import (
    PairMetrics,
    TermConfusion,
    average_metrics,
    score_correction,
    score_pair,
    split_terms,
    term_confusion,
)

# Method label -> prediction column (paper Table 4 rows).
NE_F1_METHODS = [
    ("Baseline", "raw_asr"),
    ("+GEC", "corrected_text"),
    ("+DARAG", "gec_pred"),
    ("+DARAG w/ ID NE", "gec_pred_id_ne"),
]


def _row_terms(row: dict[str, Any]) -> list[str]:
    return row.get("gold_terms") or split_terms(row.get("cs_terms_list"))


def wer_report(rows: list[dict[str, Any]], prediction_columns: list[str]) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for column in prediction_columns:
        by_split: dict[str, list[PairMetrics]] = {}
        for row in rows:
            if column not in row:
                continue
            split = row.get("split", "unknown")
            terms = _row_terms(row)
            if column != "raw_asr" and row.get("raw_asr"):
                metric = score_correction(row["gold_text"], row["raw_asr"], row[column], terms)
            else:
                metric = score_pair(row["gold_text"], row[column], terms)
            by_split.setdefault(split, []).append(metric)
        report[column] = {
            split: _summarize(average_metrics(metrics), len(metrics))
            for split, metrics in sorted(by_split.items())
        }
    return report


def ne_f1_table(
    rows: list[dict[str, Any]],
    id_splits: tuple[str, ...] = ID_SPLITS,
    ood_splits: tuple[str, ...] = OOD_SPLITS,
) -> dict[str, Any]:
    """Micro-F1 of NEs per method, ID vs OOD (paper Table 4)."""

    groups = {"ID": set(id_splits), "OOD": set(ood_splits)}
    table: dict[str, Any] = {}
    for label, column in NE_F1_METHODS:
        present = any(column in row for row in rows)
        if not present:
            continue
        method_row: dict[str, Any] = {}
        for group_name, splits in groups.items():
            confusion = TermConfusion()
            n = 0
            for row in rows:
                if row.get("split") not in splits or column not in row:
                    continue
                confusion = confusion + term_confusion(
                    row["gold_text"], row[column], _row_terms(row)
                )
                n += 1
            if n:
                method_row[group_name] = {
                    "n": n,
                    "precision": round(confusion.precision, 4),
                    "recall": round(confusion.recall, 4),
                    "f1_micro": round(confusion.f1, 4),
                }
        if method_row:
            table[label] = method_row
    return table


def render_ne_f1_table(table: dict[str, Any]) -> str:
    """Pretty-print the NE-F1 ablation table for notebook/CLI output."""

    lines = [f"{'Method':<20} {'ID F1':>8} {'OOD F1':>8}"]
    lines.append("-" * 38)
    for label, _ in NE_F1_METHODS:
        if label not in table:
            continue
        row = table[label]
        id_f1 = row.get("ID", {}).get("f1_micro")
        ood_f1 = row.get("OOD", {}).get("f1_micro")
        lines.append(
            f"{label:<20} "
            f"{('-' if id_f1 is None else f'{id_f1:.4f}'):>8} "
            f"{('-' if ood_f1 is None else f'{ood_f1:.4f}'):>8}"
        )
    return "\n".join(lines)


def build_reports(
    input_path: Path,
    prediction_columns: list[str],
    wer_output: Path | None = None,
    ne_f1_output: Path | None = None,
) -> dict[str, Any]:
    rows = [
        json.loads(line)
        for line in input_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    wer = wer_report(rows, prediction_columns)
    ne_table = ne_f1_table(rows)
    if wer_output:
        wer_output.parent.mkdir(parents=True, exist_ok=True)
        wer_output.write_text(json.dumps(wer, ensure_ascii=False, indent=2), encoding="utf-8")
    if ne_f1_output:
        ne_f1_output.parent.mkdir(parents=True, exist_ok=True)
        ne_f1_output.write_text(json.dumps(ne_table, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"wer": wer, "ne_f1": ne_table}


def _summarize(metrics: PairMetrics, count: int) -> dict[str, Any]:
    return {
        "n": count,
        "wer": round(metrics.wer, 4),
        "cer": round(metrics.cer, 4),
        "term_precision": round(metrics.term_precision, 4),
        "term_recall": round(metrics.term_recall, 4),
        "term_f1": round(metrics.term_f1, 4),
        "number_unit_preservation": round(metrics.number_unit_preservation, 4),
        "overcorrection_rate": round(metrics.overcorrection_rate, 4),
    }
