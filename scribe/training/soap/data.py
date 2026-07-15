"""Public train-only source adapters and governed silver-data preparation."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

from soap.schemas import (
    SOAP_FIELDS,
    canonical_mentions,
    clinical_text,
    make_fact,
    normalize,
    number_units,
    stable_json,
    validate_example,
)

APPROVED_STATUS = "approved_research_only"
USAGE_SCOPE = "research_only"
PROMOTION_STATUS = "blocked_research_only"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(path: Path, *, require_approved: bool = True) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "dataset_id",
        "approval_status",
        "usage_scope",
        "promotion_status",
        "sources",
    }
    missing = required - payload.keys()
    if missing:
        raise ValueError(f"SOAP manifest missing fields: {sorted(missing)}")
    if (
        payload["usage_scope"] != USAGE_SCOPE
        or payload["promotion_status"] != PROMOTION_STATUS
    ):
        raise ValueError(
            "SOAP data must remain research_only and blocked_research_only"
        )
    if require_approved and payload["approval_status"] != APPROVED_STATUS:
        raise ValueError("SOAP data requires owner approval for research-only training")
    if not isinstance(payload["sources"], list) or not payload["sources"]:
        raise ValueError("SOAP manifest requires at least one source")
    for source in payload["sources"]:
        digest = source.get("sha256")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or set(digest.lower()) - set("0123456789abcdef")
        ):
            raise ValueError("SOAP source sha256 must be a SHA-256 digest")
        if digest == "0" * 64:
            raise ValueError("SOAP source sha256 must not be a placeholder")
        if source.get("allowed_splits") != ["train"]:
            raise ValueError("SOAP public/synthetic sources must be train-only")
        if source.get("download_url") or source.get("input_files"):
            if not re.fullmatch(r"[0-9a-f]{40}", str(source.get("revision", ""))):
                raise ValueError(
                    "approved public SOAP sources require an exact revision"
                )
            files = source.get("input_files", [])
            if any(
                not str(item.get("download_url", "")).startswith("https://")
                or not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", "")))
                for item in files
            ):
                raise ValueError(
                    "public SOAP source inputs require HTTPS URLs and SHA-256 hashes"
                )
    return payload


def read_source(path: Path, kind: str) -> list[dict[str, Any]]:
    if kind == "synthetic":
        return _read_json_rows(path)
    if kind in {"mts_dialog", "aci_bench"}:
        return _adapt_public_rows(path, kind)
    raise ValueError(f"unsupported SOAP source adapter: {kind!r}")


def _read_json_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line
        ]
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else list(payload.get("data", []))


def _adapt_public_rows(path: Path, kind: str) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    else:
        rows = _read_json_rows(path)
    adapted = []
    for index, row in enumerate(rows):
        source_split = str(row.get("split", "train")).lower()
        if source_split != "train":
            raise ValueError(
                f"{kind} adapter refuses non-train source split: {source_split}"
            )
        dialogue = _first(row, "dialogue", "conversation", "transcript", "input")
        note = _first(row, "note", "section_text", "clinical_note", "summary", "output")
        if not dialogue or not note:
            raise ValueError(f"{kind} row {index} lacks dialogue or note text")
        adapted.append(
            {
                "source_record_id": str(
                    row.get("id") or row.get("encounter_id") or index
                ),
                "source_split": "train",
                "dialogue": dialogue,
                "source_note": note,
            }
        )
    return adapted


def load_terminology(
    canonical_path: Path, medev_path: Path | None = None
) -> dict[str, dict[str, set[str]]]:
    payload = json.loads(canonical_path.read_text(encoding="utf-8"))
    terms: dict[str, dict[str, set[str]]] = {}
    for item in payload["terms"]:
        canonical = str(item["term_vi"])
        terms[canonical] = {
            "kinds": {str(item.get("kind", "other"))},
            "values": {
                canonical,
                str(item.get("term_en", "")),
                *map(str, item.get("aliases", [])),
            }
            - {""},
        }
    if medev_path:
        for row in _iter_medev(medev_path):
            vi, en = row
            if vi:
                entry = terms.setdefault(
                    vi, {"kinds": {"translation"}, "values": set()}
                )
                entry["values"].update({vi, en} - {""})
    return terms


def _iter_medev(path: Path) -> Iterable[tuple[str, str]]:
    if path.suffix.lower() in {".json", ".jsonl"}:
        for row in _read_json_rows(path):
            yield (
                _first(row, "vi", "vietnamese", "target"),
                _first(row, "en", "english", "source"),
            )
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            yield (
                _first(row, "vi", "vietnamese", "target"),
                _first(row, "en", "english", "source"),
            )


def prepare_examples(
    config, manifest: dict[str, Any], teacher
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    manifest_sources = {item["source_id"]: item for item in manifest["sources"]}
    if config.medev_terms:
        medev_meta = manifest_sources.get(config.medev_source_id)
        if medev_meta is None:
            raise ValueError(
                "MedEV terminology source is absent from the SOAP manifest"
            )
        if sha256_file(config.medev_terms) != medev_meta["sha256"]:
            raise ValueError(
                "MedEV terminology source hash does not match the SOAP manifest"
            )
    vocabulary = load_terminology(config.canonical_terms, config.medev_terms)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for source_config in config.sources:
        source_id = str(source_config["source_id"])
        source_meta = manifest_sources.get(source_id)
        if source_meta is None:
            raise ValueError(f"SOAP source {source_id!r} is absent from manifest")
        path = Path(str(source_config["path"]))
        digest = sha256_file(path)
        if digest != source_meta["sha256"]:
            raise ValueError(f"SOAP source hash mismatch for {source_id}")
        rows = read_source(path, str(source_config["kind"]))
        if config.max_rows is not None:
            rows = rows[: config.max_rows]
        for index, source_row in enumerate(rows):
            try:
                example = teacher.transform(source_row)
                example["example_id"] = (
                    f"{source_id}:{source_row.get('source_record_id', index)}"
                )
                validation_row = index % (
                    2 if config.profile_name == "smoke" else 5
                ) == (1 if config.profile_name == "smoke" else 4)
                example["split"] = "validation" if validation_row else "train"
                example["provenance"] = {
                    "dataset": source_meta["dataset"],
                    "source_id": source_id,
                    "source_record_id": str(source_row.get("source_record_id", index)),
                    "source_split": "train",
                    "source_url": source_meta["source_url"],
                    "revision": source_meta["revision"],
                    "source_sha256": digest,
                    "source_row_sha256": _source_row_sha256(source_row, index),
                    "license": source_meta["license"],
                    "teacher": teacher.provenance(),
                    "usage_scope": USAGE_SCOPE,
                }
                example["terminology"] = validate_terminology(example, vocabulary)
                issues = validate_example(example)
                if example["terminology"]["unknown_medications"]:
                    issues.append(
                        "medication is absent from canonical/MedEV terminology"
                    )
                issues.extend(grounded_soap_issues(example, vocabulary))
                if issues:
                    raise ValueError("; ".join(issues))
                accepted.append(example)
            except (KeyError, TypeError, ValueError) as exc:
                rejected.append(
                    {"source_id": source_id, "row": index, "reason": str(exc)}
                )
    if not accepted:
        raise ValueError("SOAP preparation produced no accepted examples")
    if not any(row["split"] == "validation" for row in accepted):
        accepted[-1]["split"] = "validation"
    return accepted, rejected


def validate_terminology(
    example: dict[str, Any], vocabulary: dict[str, dict[str, set[str]]]
) -> dict[str, Any]:
    all_kinds = {kind for entry in vocabulary.values() for kind in entry["kinds"]}
    known = sorted(canonical_mentions(example["transcript"], vocabulary, all_kinds))
    medications = [
        fact["value"] for fact in example["facts"] if fact["type"] == "medication"
    ]
    known_values = {
        normalize(value) for entry in vocabulary.values() for value in entry["values"]
    }
    unknown = sorted(
        value for value in medications if normalize(value) not in known_values
    )
    rendered = clinical_text({"facts": example["facts"], "soap": example["soap"]})
    unsupported_drugs = sorted(
        canonical_mentions(rendered, vocabulary, {"drug"})
        - canonical_mentions(example["transcript"], vocabulary, {"drug"})
    )
    unsupported_conditions = sorted(
        canonical_mentions(
            str(example["soap"]["assessment"]), vocabulary, {"condition"}
        )
        - canonical_mentions(example["transcript"], vocabulary, {"condition"})
    )
    return {
        "known_terms": known,
        "unknown_medications": unknown,
        "unsupported_soap_medications": unsupported_drugs,
        "unsupported_soap_assessments": unsupported_conditions,
    }


def grounded_soap_issues(
    example: dict[str, Any], vocabulary: dict[str, dict[str, set[str]]]
) -> list[str]:
    transcript, soap, facts = example["transcript"], example["soap"], example["facts"]
    issues: list[str] = []
    unsupported_numbers = number_units(
        clinical_text({"facts": [], "soap": soap})
    ) - number_units(transcript)
    if unsupported_numbers:
        issues.append(
            f"SOAP contains unsupported numbers/units: {sorted(unsupported_numbers)}"
        )
    allowed = {normalize(str(fact["value"])) for fact in facts}
    for section in SOAP_FIELDS[:4]:
        text = str(soap[section]).strip()
        if _missing_section(text):
            continue
        fragments = [
            normalize(fragment) for fragment in text.split(";") if fragment.strip()
        ]
        unsupported = [fragment for fragment in fragments if fragment not in allowed]
        if unsupported:
            issues.append(
                f"SOAP {section} contains unsupported fact text: {unsupported}"
            )
    assessment = str(soap["assessment"])
    if not _missing_section(assessment):
        values = {
            normalize(str(fact["value"]))
            for fact in facts
            if fact["type"] == "assessment"
        }
        if not values or not any(value in normalize(assessment) for value in values):
            issues.append("SOAP assessment requires a grounded assessment fact")
    plan = str(soap["plan"])
    if not _missing_section(plan):
        values = {
            normalize(str(fact["value"]))
            for fact in facts
            if fact["type"] in {"plan", "medication", "dose"}
        }
        if not values or not any(value in normalize(plan) for value in values):
            issues.append("SOAP plan requires a grounded plan/medication/dose fact")
    terminology = validate_terminology(example, vocabulary)
    if terminology["unsupported_soap_medications"]:
        issues.append("SOAP contains unsupported medication terminology")
    if terminology["unsupported_soap_assessments"]:
        issues.append("SOAP contains unsupported assessment terminology")
    return issues


def materialize_synthetic(source_row: dict[str, Any]) -> dict[str, Any]:
    transcript = str(source_row["dialogue"])
    facts = [
        make_fact(
            transcript,
            str(fact["type"]),
            str(fact["value"]),
            str(fact["source_text"]),
            negated=bool(fact.get("negated", False)),
            uncertain=bool(fact.get("uncertain", False)),
        )
        for fact in source_row["facts"]
    ]
    return {
        "transcript": transcript,
        "facts": facts,
        "soap": dict(source_row["soap"]),
        "demographics": dict(source_row.get("demographics", {})),
    }


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
        ),
        encoding="utf-8",
    )


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def _first(row: dict[str, Any], *keys: str) -> str:
    return next((str(row[key]).strip() for key in keys if row.get(key)), "")


def _missing_section(text: str) -> bool:
    return normalize(text).startswith(("chưa có", "không có thông tin"))


def _source_row_sha256(source_row: dict[str, Any], index: int) -> str:
    payload = {
        "source_record_id": str(source_row.get("source_record_id", index)),
        "source_split": str(source_row.get("source_split", "train")),
        "dialogue": str(source_row.get("dialogue", "")),
        "note": str(
            source_row.get("source_note") or stable_json(source_row.get("soap", {}))
        ),
    }
    return hashlib.sha256(stable_json(payload).encode("utf-8")).hexdigest()
