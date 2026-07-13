"""Generate the Scribe and Interpreter term artifacts from shared source data."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "shared" / "carepath_shared" / "terms" / "medical_terms.json"
SCRIBE_TARGET = ROOT / "data" / "medical_lexicon.json"
INTERPRETER_TARGET = ROOT / "interpreter" / "app" / "glossary" / "data" / "seed_glossary.csv"


def _terms() -> list[dict[str, object]]:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    terms = payload.get("terms")
    if not isinstance(terms, list):
        raise ValueError(f"{SOURCE} must contain a terms list")
    return terms


def _target(term: dict[str, object], name: str) -> dict[str, object] | None:
    targets = term.get("targets")
    if not isinstance(targets, dict):
        raise ValueError(f"{term.get('term_en')!r} has no target mapping")
    target = targets.get(name)
    if target is None:
        return None
    if not isinstance(target, dict):
        raise ValueError(f"{term.get('term_en')!r} has an invalid {name} mapping")
    return target


def _ordered_terms(terms: list[dict[str, object]], name: str) -> list[tuple[dict[str, object], dict[str, object]]]:
    selected = [(term, target) for term in terms if (target := _target(term, name)) is not None]
    orders = [target.get("order") for _, target in selected]
    if sorted(orders) != list(range(len(selected))):
        raise ValueError(f"{name} target orders must be contiguous and unique")
    return sorted(selected, key=lambda item: int(item[1]["order"]))


def _scribe_artifact(terms: list[dict[str, object]]) -> str:
    lines = ["{", '  "terms": [']
    rows = []
    for term, target in _ordered_terms(terms, "scribe"):
        aliases = term.get("aliases")
        if (
            not isinstance(term.get("term_en"), str)
            or not isinstance(target.get("category"), str)
            or not isinstance(target.get("term_vi"), str)
            or not isinstance(aliases, list)
            or not all(isinstance(alias, str) for alias in aliases)
        ):
            raise ValueError(f"{term.get('term_en')!r} has invalid Scribe fields")
        rows.append((term["term_en"], target["category"], target["term_vi"], aliases))
    for index, (term_en, category, term_vi, aliases) in enumerate(rows):
        comma = "," if index + 1 < len(rows) else ""
        lines.extend(
            (
                "    {",
                f'      "term": {json.dumps(term_en, ensure_ascii=False)},',
                f'      "category": {json.dumps(category, ensure_ascii=False)},',
                f'      "vietnamese": {json.dumps(term_vi, ensure_ascii=False)},',
                f'      "aliases": {json.dumps(aliases, ensure_ascii=False)}',
                f"    }}{comma}",
            )
        )
    return "\n".join([*lines, "  ]", "}", "", ""])


def _interpreter_artifact(terms: list[dict[str, object]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=["term_vi", "term_en", "kind", "lasa_group"],
        lineterminator="\n",
    )
    writer.writeheader()
    for term, _target_data in _ordered_terms(terms, "interpreter"):
        flags = term.get("risk_flags")
        if (
            not all(isinstance(term.get(field), str) for field in ("term_vi", "term_en", "kind"))
            or not isinstance(flags, dict)
            or not isinstance(flags.get("lasa_group", ""), str)
        ):
            raise ValueError(f"{term.get('term_en')!r} has invalid risk flags")
        writer.writerow(
            {
                "term_vi": term["term_vi"],
                "term_en": term["term_en"],
                "kind": term["kind"],
                "lasa_group": flags.get("lasa_group", ""),
            }
        )
    return output.getvalue()


def artifacts() -> dict[Path, str]:
    terms = _terms()
    return {SCRIBE_TARGET: _scribe_artifact(terms), INTERPRETER_TARGET: _interpreter_artifact(terms)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated artifacts differ")
    args = parser.parse_args()
    generated = artifacts()
    changed = [path for path, content in generated.items() if path.read_text(encoding="utf-8") != content]
    if args.check:
        if changed:
            raise SystemExit("Generated term artifacts differ: " + ", ".join(map(str, changed)))
        print("Generated term artifacts are current.")
        return
    for path, content in generated.items():
        path.write_text(content, encoding="utf-8")
        print(f"Wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
