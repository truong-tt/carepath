"""Internal two-pass fact and SOAP schemas with source-grounding checks."""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

FACT_TYPES = {
    "symptom",
    "history",
    "observation",
    "assessment",
    "medication",
    "dose",
    "plan",
}
CRITICAL_FACT_TYPES = {"assessment", "medication", "dose"}
SOAP_FIELDS = (
    "subjective",
    "objective",
    "assessment",
    "plan",
    "missing_information",
    "review_required",
)
NEGATION_CUES = ("không", "chưa", "khỏi", "âm tính", "no ", "not ", "denies")
NUMBER_UNIT_RE = re.compile(
    r"\b\d+(?:[.,/]\d+)?\s*(?:%|mmhg|mg/dl|mmol/l|mg|g|mcg|ml|l|bpm|đơn vị)?\b",
    flags=re.IGNORECASE,
)


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def make_fact(
    transcript: str,
    fact_type: str,
    value: str,
    source_text: str,
    *,
    negated: bool = False,
    uncertain: bool = False,
) -> dict[str, Any]:
    start = transcript.find(source_text)
    if start < 0:
        raise ValueError(f"source text is not an exact transcript span: {source_text!r}")
    return {
        "type": fact_type,
        "value": value,
        "negated": bool(negated),
        "uncertain": bool(uncertain),
        "source_span": {"start": start, "end": start + len(source_text), "text": source_text},
    }


def validate_fact(fact: Any, transcript: str) -> list[str]:
    if not isinstance(fact, dict):
        return ["fact must be an object"]
    issues: list[str] = []
    fact_type = fact.get("type")
    if fact_type not in FACT_TYPES:
        issues.append(f"unsupported fact type: {fact_type!r}")
    if not str(fact.get("value", "")).strip():
        issues.append("fact value must be non-empty")
    if not isinstance(fact.get("negated"), bool) or not isinstance(fact.get("uncertain"), bool):
        issues.append("fact negated and uncertain must be booleans")
    span = fact.get("source_span")
    if not isinstance(span, dict):
        return issues + ["fact source_span must be an object"]
    try:
        start, end, text = int(span["start"]), int(span["end"]), str(span["text"])
    except (KeyError, TypeError, ValueError):
        return issues + ["fact source_span must contain start, end, and text"]
    if start < 0 or end <= start or transcript[start:end] != text:
        issues.append("fact source_span does not exactly match transcript")
    if fact.get("negated") and not any(cue in normalize(text) for cue in NEGATION_CUES):
        issues.append("negated fact has no negation cue in its source span")
    return issues


def validate_soap(soap: Any) -> list[str]:
    if not isinstance(soap, dict):
        return ["soap must be an object"]
    issues = [f"soap missing field: {field}" for field in SOAP_FIELDS if field not in soap]
    for field in SOAP_FIELDS[:4]:
        if field in soap and not isinstance(soap[field], str):
            issues.append(f"soap {field} must be a string")
    if "missing_information" in soap and not isinstance(soap["missing_information"], list):
        issues.append("soap missing_information must be a list")
    if soap.get("review_required") is not True:
        issues.append("soap review_required must be true")
    return issues


def validate_prediction(prediction: Any, transcript: str) -> list[str]:
    if not isinstance(prediction, dict):
        return ["prediction must be an object"]
    facts = prediction.get("facts")
    issues = [] if isinstance(facts, list) else ["prediction facts must be a list"]
    for fact in facts if isinstance(facts, list) else []:
        issues.extend(validate_fact(fact, transcript))
    issues.extend(validate_soap(prediction.get("soap")))
    return issues


def validate_example(row: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in ("example_id", "split", "transcript", "facts", "soap", "provenance"):
        if field not in row:
            issues.append(f"example missing field: {field}")
    if row.get("split") not in {"train", "validation"}:
        issues.append("example split must be train or validation")
    transcript = str(row.get("transcript", ""))
    if not transcript.strip():
        issues.append("example transcript must be non-empty")
    issues.extend(validate_prediction({"facts": row.get("facts"), "soap": row.get("soap")}, transcript))
    if not isinstance(row.get("provenance"), dict):
        issues.append("example provenance must be an object")
    return issues


def clinical_text(prediction: dict[str, Any]) -> str:
    fact_values = [str(fact.get("value", "")) for fact in prediction.get("facts", [])]
    soap = prediction.get("soap", {})
    soap_values = [str(soap.get(field, "")) for field in SOAP_FIELDS[:4]]
    return " ".join(fact_values + soap_values)


def number_units(text: str) -> set[str]:
    return {re.sub(r"\s+", "", match.group(0).casefold()) for match in NUMBER_UNIT_RE.finditer(text)}


def canonical_mentions(
    text: str, terms: dict[str, dict[str, set[str]]], kinds: set[str]
) -> set[str]:
    normalized = normalize(text)
    return {
        canonical
        for canonical, aliases in terms.items()
        if kinds & aliases["kinds"]
        and any(
            re.search(rf"(?<!\w){re.escape(normalize(alias))}(?!\w)", normalized)
            for alias in aliases["values"]
        )
    }


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
