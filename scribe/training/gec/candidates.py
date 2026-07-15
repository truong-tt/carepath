"""CPU-only transcript benchmarks and evidence-gated candidate selection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gec.evaluate import wer_report
from gec.metrics import (
    TermConfusion,
    extract_numbers_and_units,
    term_confusion,
    word_error_rate,
)


def duration_report(
    rows: list[dict[str, Any]], manifest: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Report decoded audio duration without a hard-coded corpus estimate."""

    seconds = [
        float(row["duration_seconds"])
        for row in rows
        if isinstance(row.get("duration_seconds"), (int, float))
    ]
    if seconds:
        return {
            "source": "pair_duration_seconds",
            "hours": round(sum(seconds) / 3_600, 4),
            "rows_with_duration": len(seconds),
            "rows_missing_duration": len(rows) - len(seconds),
        }
    manifest_hours = (manifest or {}).get("audio_hours")
    return {
        "source": "manifest_audio_hours" if manifest_hours is not None else "unavailable",
        "hours": float(manifest_hours) if manifest_hours is not None else None,
        "rows_with_duration": 0,
        "rows_missing_duration": len(rows),
    }


def asr_benchmark(
    rows: list[dict[str, Any]],
    prediction_columns: tuple[str, ...] = ("raw_asr",),
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the cheap benchmark shared by mock smoke and real Colab runs."""

    available = tuple(column for column in prediction_columns if any(column in row for row in rows))
    if not rows or not available:
        raise ValueError("ASR benchmark needs rows and at least one prediction column")
    return {
        "schema": "carepath.transcript-benchmark/1",
        "hypothesis_source": "single_best",
        "duration": duration_report(rows, manifest),
        "metrics": wer_report(rows, list(available)),
        "clinical_slices": clinical_asr_slices(rows, available),
        "accent_slices": accent_slices(rows, available),
    }


def clinical_asr_slices(
    rows: list[dict[str, Any]], prediction_columns: tuple[str, ...]
) -> dict[str, Any]:
    """Make code-switch and non-code-switch denominators explicit.

    ViMedCSS exposes annotated terms but not token-level code-switch alignments,
    so term error is reported as a proxy and is never mislabeled as CS-WER/PIER.
    """

    output: dict[str, Any] = {}
    for column in prediction_columns:
        output[column] = {}
        for split in sorted({str(row.get("split", "unknown")) for row in rows}):
            split_rows = [row for row in rows if row.get("split") == split and column in row]
            confusion = TermConfusion()
            with_terms: list[float] = []
            without_terms: list[float] = []
            for row in split_rows:
                terms = row.get("gold_terms") or []
                if terms:
                    confusion = confusion + term_confusion(
                        row["gold_text"], row[column], terms
                    )
                    with_terms.append(word_error_rate(row["gold_text"], row[column]))
                else:
                    without_terms.append(word_error_rate(row["gold_text"], row[column]))
            denominator = confusion.true_positives + confusion.false_negatives
            output[column][split] = {
                "code_switch_term_error_proxy": {
                    "status": "available" if denominator else "unavailable",
                    "value": round(confusion.false_negatives / denominator, 4)
                    if denominator
                    else None,
                    "denominator": denominator,
                    "definition": "missed annotated code-switched term instances / annotated instances",
                    "is_pier": False,
                },
                "cs_wer": {
                    "status": "unavailable",
                    "reason": "ViMedCSS rows do not provide token-level code-switch alignments",
                },
                "pier": {
                    "status": "unavailable",
                    "reason": "term-recall proxy is not labeled as the paper's PIER",
                },
                "code_switched_utterance_wer": _mean_metric(with_terms),
                "non_code_switched_utterance_wer": _mean_metric(without_terms),
                "number_unit_preservation": (
                    wer_report(split_rows, [column]).get(column, {}).get(split, {}).get(
                        "number_unit_preservation"
                    )
                ),
            }
    return output


def accent_slices(
    rows: list[dict[str, Any]], prediction_columns: tuple[str, ...]
) -> dict[str, Any]:
    accent_key = next(
        (
            key
            for key in ("accent", "speaker_accent", "region")
            if any(row.get(key) not in (None, "") for row in rows)
        ),
        None,
    )
    if accent_key is None:
        return {
            "status": "unavailable",
            "reason": "dataset rows contain no accent/region metadata",
        }
    values = sorted({str(row[accent_key]) for row in rows if row.get(accent_key) not in (None, "")})
    return {
        "status": "available",
        "field": accent_key,
        "metrics": {
            value: wer_report(
                [row for row in rows if str(row.get(accent_key)) == value],
                list(prediction_columns),
            )
            for value in values
        },
    }


def _mean_metric(values: list[float]) -> dict[str, Any]:
    return {
        "status": "available" if values else "unavailable",
        "value": round(sum(values) / len(values), 4) if values else None,
        "denominator_utterances": len(values),
    }


def select_transcript_candidate(
    report: dict[str, Any],
    safety_report: dict[str, Any],
    candidates: tuple[str, ...] = ("raw_asr", "gec_pred", "phowhisper_pred"),
    latency_seconds: dict[str, float] | None = None,
    direct_safety_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Choose the safest passing candidate, then term error, WER, and latency.

    Direct ASR candidates need 10% relative hard-split WER and medical-term-error
    gains.  GEC needs a 5% medical-term-error gain and may worsen validation WER
    by no more than one absolute point.  Both need frozen medication/dosage
    non-regression; direct ASR must also run no slower than real time.
    """

    if "raw_asr" not in report or "hard" not in report["raw_asr"]:
        raise ValueError("candidate selection needs raw_asr hard-split metrics")
    latency_seconds = latency_seconds or {}
    raw_hard = report["raw_asr"]["hard"]
    raw_validation = report["raw_asr"].get("validation", raw_hard)
    decisions: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        metrics = report.get(candidate, {})
        hard = metrics.get("hard")
        validation = metrics.get("validation", hard)
        if hard is None:
            decisions[candidate] = {"eligible": False, "reasons": ["missing hard metrics"]}
            continue
        reasons: list[str] = []
        if candidate == "raw_asr":
            eligible = True
        else:
            hard_wer_gain = _relative_error_gain(raw_hard["wer"], hard["wer"])
            hard_term_gain = _relative_error_gain(
                1.0 - raw_hard["term_recall"], 1.0 - hard["term_recall"]
            )
            if candidate == "gec_pred":
                reasons.extend(_safety_issues(safety_report, candidate))
                if hard_term_gain < 0.05:
                    reasons.append("hard medical-term error gain is below 5%")
                if validation["wer"] > raw_validation["wer"] + 0.01 + 1e-9:
                    reasons.append("validation WER worsens by more than 1 absolute point")
            else:
                reasons.extend(_direct_safety_issues(direct_safety_report or {}, candidate))
                if hard_wer_gain < 0.10:
                    reasons.append("hard WER gain is below 10%")
                if hard_term_gain < 0.10:
                    reasons.append("hard medical-term error gain is below 10%")
                real_time_factor = latency_seconds.get(candidate)
                if real_time_factor is None or real_time_factor > 1.0:
                    reasons.append("real-time factor is above 1 or missing")
                if (
                    hard["number_unit_preservation"] + 1e-9
                    < raw_hard["number_unit_preservation"]
                ):
                    reasons.append("hard number/unit preservation regresses")
            eligible = not reasons
        decisions[candidate] = {
            "eligible": eligible,
            "reasons": reasons,
            "hard_wer": hard["wer"],
            "hard_medical_term_error": 1.0 - hard["term_recall"],
            "real_time_factor": latency_seconds.get(candidate),
        }

    passing = [name for name, item in decisions.items() if item["eligible"]]
    selected = min(
        passing,
        key=lambda name: (
            decisions[name]["hard_medical_term_error"],
            decisions[name]["hard_wer"],
            decisions[name]["real_time_factor"]
            if decisions[name]["real_time_factor"] is not None
            else float("inf"),
        ),
    )
    return {
        "schema": "carepath.transcript-candidate-selection/1",
        "selected": selected,
        "tie_break": ["hard_medical_term_error", "hard_wer", "real_time_factor"],
        "decisions": decisions,
    }


def plain_asr_lora_gate(
    report: dict[str, Any],
    baseline: str = "raw_asr",
    candidate: str = "phowhisper_pred",
    splits: tuple[str, ...] = ("validation", "hard"),
) -> dict[str, Any]:
    """Gate near-miss work behind 5% WER and medical-term-error gains."""

    failures: list[str] = []
    gains: dict[str, dict[str, float]] = {}
    for split in splits:
        raw = report.get(baseline, {}).get(split)
        current = report.get(candidate, {}).get(split)
        if raw is None or current is None:
            failures.append(f"{split}: missing baseline or candidate metrics")
            continue
        wer_gain = _relative_error_gain(raw["wer"], current["wer"])
        term_gain = _relative_error_gain(
            1.0 - raw["term_recall"], 1.0 - current["term_recall"]
        )
        gains[split] = {
            "relative_wer_gain": wer_gain,
            "relative_medical_term_error_gain": term_gain,
        }
        if wer_gain < 0.05:
            failures.append(f"{split}: relative WER gain is below 5%")
        if term_gain < 0.05:
            failures.append(f"{split}: relative medical-term error gain is below 5%")
        if current["number_unit_preservation"] + 1e-9 < raw["number_unit_preservation"]:
            failures.append(f"{split}: number/unit preservation regresses")
    return {
        "accepted": not failures,
        "gains": gains,
        "failures": failures,
        "next_stage": "near_miss_eligible" if not failures else "near_miss_blocked",
    }


def direct_asr_safety_report(
    rows: list[dict[str, Any]],
    prediction_columns: tuple[str, ...],
    lexicon_path: Path = Path("data/medical_lexicon.json"),
) -> dict[str, Any]:
    """Critical hard-split evidence for direct ASR; never uses text-only GEC fixtures."""

    medications: set[str] = set()
    try:
        lexicon = json.loads(lexicon_path.read_text(encoding="utf-8"))
        medications = {
            str(item["term"]).lower()
            for item in lexicon.get("terms", [])
            if item.get("category") == "medication"
        }
    except (OSError, json.JSONDecodeError):
        pass
    hard = [row for row in rows if row.get("split") == "hard"]
    categories = {
        "medication": [
            row
            for row in hard
            if any(str(term).lower() in medications for term in row.get("gold_terms", []))
        ],
        "dosage": [
            row
            for row in hard
            if any(any(char.isalpha() or char == "%" for char in item) for item in extract_numbers_and_units(row["gold_text"]))
        ],
        "numbers": [row for row in hard if extract_numbers_and_units(row["gold_text"])],
    }
    return {
        "source": "untouched ViMedCSS hard split",
        "categories": {
            category: {
                "status": "available" if category_rows else "unavailable",
                "n": len(category_rows),
                "metrics": wer_report(category_rows, list(prediction_columns))
                if category_rows
                else {},
            }
            for category, category_rows in categories.items()
        },
    }


def phonetic_candidate_gate(
    report: dict[str, Any],
    safety_report: dict[str, Any],
    baseline: str = "gec_full_pred",
    candidate: str = "gec_pred",
) -> dict[str, Any]:
    """Decide whether PiDA text corruption earns permission for later TTS work."""

    failures: list[str] = []
    try:
        base_hard = report[baseline]["hard"]
        candidate_hard = report[candidate]["hard"]
        base_validation = report[baseline]["validation"]
        candidate_validation = report[candidate]["validation"]
    except KeyError as exc:
        return {
            "accepted": False,
            "failures": [f"missing phonetic comparison metric: {exc}"],
            "tts_unlock": False,
        }
    hard_term_gain = _relative_error_gain(
        1.0 - base_hard["term_recall"],
        1.0 - candidate_hard["term_recall"],
    )
    if hard_term_gain < 0.05:
        failures.append("hard medical-term error proxy gain is below 5%")
    if candidate_validation["wer"] > base_validation["wer"] + 0.01 + 1e-9:
        failures.append("clean validation WER worsens by more than 1 absolute point")
    for category, metric in (
        ("drug_name", "term_recall"),
        ("dosage", "number_unit_preservation"),
        ("numbers", "number_unit_preservation"),
    ):
        category_report = safety_report.get(category, {})
        base = category_report.get(baseline, {}).get("frozen")
        current = category_report.get(candidate, {}).get("frozen")
        if base is None or current is None:
            failures.append(f"missing frozen {category} comparison")
        elif current[metric] + 1e-9 < base[metric]:
            failures.append(f"frozen {category}.{metric} regresses")
    return {
        "accepted": not failures,
        "hard_medical_term_error_proxy_relative_gain": hard_term_gain,
        "proxy_note": "annotated term error is used because PIER is unavailable",
        "clean_validation_wer_delta": candidate_validation["wer"] - base_validation["wer"],
        "failures": failures,
        "tts_unlock": not failures,
    }


def _relative_error_gain(baseline: float, candidate: float) -> float:
    if baseline <= 1e-12:
        return 0.0 if candidate <= 1e-12 else -1.0
    return (baseline - candidate) / baseline


def _safety_issues(report: dict[str, Any], candidate: str) -> list[str]:
    issues: list[str] = []
    for category, metric in (
        ("drug_name", "term_recall"),
        ("dosage", "number_unit_preservation"),
    ):
        category_report = report.get(category, {})
        raw = category_report.get("raw_asr", {}).get("frozen")
        current = category_report.get(candidate, {}).get("frozen")
        if raw is None or current is None:
            issues.append(f"missing frozen {category} metrics")
        elif current[metric] + 1e-9 < raw[metric]:
            issues.append(f"frozen {category}.{metric} regresses")
    return issues


def _direct_safety_issues(report: dict[str, Any], candidate: str) -> list[str]:
    issues: list[str] = []
    for category, metric in (
        ("medication", "term_recall"),
        ("dosage", "number_unit_preservation"),
        ("numbers", "number_unit_preservation"),
    ):
        evidence = report.get("categories", {}).get(category, {})
        metrics = evidence.get("metrics", {})
        raw = metrics.get("raw_asr", {}).get("hard")
        current = metrics.get(candidate, {}).get("hard")
        if evidence.get("status") != "available" or raw is None or current is None:
            issues.append(f"missing direct-ASR hard {category} safety evidence")
        elif current[metric] + 1e-9 < raw[metric]:
            issues.append(f"direct-ASR hard {category}.{metric} regresses")
    return issues
