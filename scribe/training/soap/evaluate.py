"""Deterministic factual and clinical-safety evaluation for SOAP predictions."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from soap.data import load_manifest, read_jsonl, sha256_file
from soap.prompts import SYSTEM
from soap.schemas import (
    CRITICAL_FACT_TYPES,
    SOAP_FIELDS,
    canonical_mentions,
    clinical_text,
    normalize,
    number_units,
    validate_prediction,
)

def evaluate(predictions_path: Path, terminology: dict[str, dict[str, set[str]]]) -> dict[str, Any]:
    rows = read_jsonl(predictions_path)
    if not rows:
        raise ValueError("SOAP evaluation requires predictions")
    system_names = sorted(
        set(rows[0])
        - {"example_id", "transcript", "demographics", "reference", "system_provenance"}
    )
    if "adapter" not in system_names or "base" not in system_names:
        raise ValueError("SOAP predictions require base and adapter systems")
    systems: dict[str, dict[str, Any]] = {}
    for system in system_names:
        tp = fp = fn = schema_ok = unsupported = numeric_errors = negation_errors = 0
        failures: list[dict[str, Any]] = []
        for row in rows:
            reference = row["reference"]
            prediction = row[system]
            ref_facts = {_signature(fact) for fact in reference["facts"]}
            pred_facts = {_signature(fact) for fact in prediction.get("facts", []) if isinstance(fact, dict)}
            tp += len(ref_facts & pred_facts)
            fp += len(pred_facts - ref_facts)
            fn += len(ref_facts - pred_facts)
            schema_issues = validate_prediction(prediction, row["transcript"])
            safety = safety_issues(row["transcript"], reference, prediction, terminology)
            schema_ok += not schema_issues
            unsupported += len(safety["unsupported_critical"])
            numeric_errors += len(safety["numeric_errors"])
            negation_errors += len(safety["negation_errors"])
            if schema_issues or any(safety.values()):
                failures.append(
                    {
                        "example_id": row["example_id"],
                        "schema": schema_issues,
                        **safety,
                    }
                )
        precision = tp / (tp + fp) if tp + fp else 1.0
        recall = tp / (tp + fn) if tp + fn else 1.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        systems[system] = {
            "examples": len(rows),
            "factual_precision": round(precision, 6),
            "factual_recall": round(recall, 6),
            "factual_f1": round(f1, 6),
            "hallucination_rate": round(fp / (tp + fp), 6) if tp + fp else 0.0,
            "omission_rate": round(fn / (tp + fn), 6) if tp + fn else 0.0,
            "schema_validity": round(schema_ok / len(rows), 6),
            "unsupported_critical_facts": unsupported,
            "numeric_safety_errors": numeric_errors,
            "negation_safety_errors": negation_errors,
            "demographic_slices": _demographic_slices(rows, system),
            "failures": failures,
        }
    accepted, reasons = gate(systems)
    return {
        "schema": "carepath.soap.evaluation/1",
        "usage_scope": "research_only",
        "promotion_status": "blocked_research_only",
        "systems": systems,
        "system_provenance": rows[0].get("system_provenance", {}),
        "gate": {"accepted": accepted, "candidate": "adapter", "reasons": reasons},
    }


def safety_issues(
    transcript: str,
    reference: dict[str, Any],
    prediction: dict[str, Any],
    terminology: dict[str, dict[str, set[str]]],
) -> dict[str, list[str]]:
    transcript_numbers = number_units(transcript)
    output_numbers = number_units(clinical_text(prediction))
    numeric = sorted(output_numbers - transcript_numbers)
    ref_critical = {
        _signature(fact)
        for fact in reference.get("facts", [])
        if fact.get("type") in CRITICAL_FACT_TYPES
    }
    pred_critical = {
        _signature(fact)
        for fact in prediction.get("facts", [])
        if isinstance(fact, dict) and fact.get("type") in CRITICAL_FACT_TYPES
    }
    unsupported = ["unsupported fact: " + repr(item) for item in sorted(pred_critical - ref_critical)]
    source_drugs = canonical_mentions(transcript, terminology, {"drug"})
    output_drugs = canonical_mentions(clinical_text(prediction), terminology, {"drug"})
    unsupported.extend(f"unsupported medication: {item}" for item in sorted(output_drugs - source_drugs))
    source_conditions = canonical_mentions(transcript, terminology, {"condition"})
    assessment = str(prediction.get("soap", {}).get("assessment", ""))
    output_conditions = canonical_mentions(assessment, terminology, {"condition"})
    unsupported.extend(
        f"unsupported assessment: {item}" for item in sorted(output_conditions - source_conditions)
    )
    ref_polarity = {
        (fact.get("type"), normalize(str(fact.get("value", "")))): bool(fact.get("negated"))
        for fact in reference.get("facts", [])
    }
    negation = []
    for fact in prediction.get("facts", []):
        if not isinstance(fact, dict):
            continue
        key = (fact.get("type"), normalize(str(fact.get("value", ""))))
        if key in ref_polarity and bool(fact.get("negated")) != ref_polarity[key]:
            negation.append(f"negation mismatch: {fact.get('value')}")
    return {
        "unsupported_critical": unsupported,
        "numeric_errors": numeric,
        "negation_errors": negation,
    }


def gate(systems: dict[str, dict[str, Any]]) -> tuple[bool, list[str]]:
    candidate = systems["adapter"]
    reasons: list[str] = []
    if candidate["schema_validity"] != 1.0:
        reasons.append("adapter schema validity must be 100%")
    for metric in ("unsupported_critical_facts", "numeric_safety_errors", "negation_safety_errors"):
        if candidate[metric] != 0:
            reasons.append(f"adapter {metric} must be zero")
    for baseline in sorted(set(systems) - {"adapter"}):
        metrics = systems[baseline]
        if candidate["factual_f1"] < metrics["factual_f1"]:
            reasons.append(f"adapter factual_f1 regressed against {baseline}")
        if candidate["hallucination_rate"] > metrics["hallucination_rate"]:
            reasons.append(f"adapter hallucination_rate regressed against {baseline}")
        if candidate["omission_rate"] > metrics["omission_rate"]:
            reasons.append(f"adapter omission_rate regressed against {baseline}")
    return not reasons, reasons


def export_bundle(config, adapter_dir: Path, report_path: Path, output: Path) -> None:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not report["gate"]["accepted"]:
        raise ValueError("SOAP export blocked because the safety gate rejected the adapter")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    shutil.copytree(adapter_dir, output / "adapters" / "soap")
    shutil.copy2(report_path, output / "evaluation.json")
    (output / "MODEL_CARD.md").write_text(
        "# CarePath SOAP research adapter\n\n"
        "Research-only Vietnamese SOAP experiment. Production/commercial promotion is blocked. "
        "Outputs require clinician review and are not clinical validation.\n",
        encoding="utf-8",
    )
    files = {
        str(path.relative_to(output)).replace("\\", "/"): sha256_file(path)
        for path in sorted(output.rglob("*"))
        if path.is_file()
    }
    manifest = {
        "schema": "carepath.scribe.bundle/1",
        "usage_scope": "research_only",
        "promotion_status": "blocked_research_only",
        "base_model": config.base_model,
        "base_revision": config.base_revision,
        "tokenizer_revision": config.base_revision,
        "adapters": {"soap": "adapters/soap"},
        "correction_mode": "identity",
        "tasks": ["extract_grounded_facts", "write_grounded_soap"],
        "soap_fields": list(SOAP_FIELDS),
        "selected_seed": config.selected_seed,
        "evaluation": "evaluation.json",
        "model_card": "MODEL_CARD.md",
        "prompts": {"soap": SYSTEM},
        "max_new_tokens": {"soap": 1200},
        "licenses": {
            "base_model": "Apache-2.0",
            "training_sources": sorted(
                {source["license"] for source in load_manifest(config.manifest)["sources"]}
            ),
        },
        "files": files,
    }
    (output / "scribe_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )


def _signature(fact: dict[str, Any]) -> tuple[str, str, bool, bool]:
    return (
        str(fact.get("type", "")),
        normalize(str(fact.get("value", ""))),
        bool(fact.get("negated")),
        bool(fact.get("uncertain")),
    )


def _demographic_slices(rows: list[dict[str, Any]], system: str) -> dict[str, Any]:
    slices: dict[str, Any] = {}
    for attribute in ("age_group", "gender"):
        values = sorted(
            {str(row.get("demographics", {}).get(attribute)) for row in rows if row.get("demographics", {}).get(attribute)}
        )
        groups: dict[str, Any] = {}
        for value in values:
            selected = [row for row in rows if str(row.get("demographics", {}).get(attribute)) == value]
            tp = fp = fn = 0
            for row in selected:
                reference = {_signature(fact) for fact in row["reference"]["facts"]}
                predicted = {
                    _signature(fact)
                    for fact in row[system].get("facts", [])
                    if isinstance(fact, dict)
                }
                tp += len(reference & predicted)
                fp += len(predicted - reference)
                fn += len(reference - predicted)
            precision = tp / (tp + fp) if tp + fp else 1.0
            recall = tp / (tp + fn) if tp + fn else 1.0
            groups[value] = {
                "examples": len(selected),
                "factual_f1": round(
                    2 * precision * recall / (precision + recall) if precision + recall else 0.0,
                    6,
                ),
            }
        if groups:
            slices[attribute] = groups
    return {
        "status": "descriptive_research_only",
        "warning": "Synthetic smoke slices are not clinical fairness evidence.",
        "groups": slices,
    }
