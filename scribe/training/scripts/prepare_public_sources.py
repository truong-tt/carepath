"""Fetch immutable public SOAP sources into ephemeral Colab storage."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scribe" / "training"))

from soap.data import load_manifest  # noqa: E402


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, output: Path, expected_sha256: str) -> None:
    if output.is_file() and _sha256(output) == expected_sha256:
        return
    if not url.startswith("https://"):
        raise ValueError("public source URL must use HTTPS")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "CarePath-research/1"})
    digest = hashlib.sha256()
    try:
        with (
            urllib.request.urlopen(request, timeout=60) as response,
            temporary.open("wb") as handle,
        ):  # noqa: S310 - HTTPS is checked above
            for chunk in iter(lambda: response.read(1024 * 1024), b""):
                digest.update(chunk)
                handle.write(chunk)
    except (OSError, urllib.error.URLError):
        temporary.unlink(missing_ok=True)
        raise
    if digest.hexdigest() != expected_sha256:
        temporary.unlink(missing_ok=True)
        raise ValueError(f"public source hash mismatch: {url}")
    temporary.replace(output)


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def _term_pattern(values: set[str]) -> re.Pattern[str]:
    alternatives = "|".join(
        re.escape(value) for value in sorted(values, key=len, reverse=True)
    )
    return re.compile(rf"(?<!\w)(?:{alternatives})(?!\w)")


def derive_medev_terms(
    english_path: Path,
    vietnamese_path: Path,
    canonical_path: Path,
    output: Path,
) -> int:
    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))["terms"]
    pairs = [
        (_normalize(str(item["term_vi"])), _normalize(str(item["term_en"])))
        for item in canonical
        if str(item.get("term_vi", "")).strip() and str(item.get("term_en", "")).strip()
    ]
    vi_indexes: dict[str, set[int]] = {}
    en_indexes: dict[str, set[int]] = {}
    for index, (vi, en) in enumerate(pairs):
        vi_indexes.setdefault(vi, set()).add(index)
        en_indexes.setdefault(en, set()).add(index)
    vi_pattern = _term_pattern(set(vi_indexes))
    en_pattern = _term_pattern(set(en_indexes))
    found: set[int] = set()
    with (
        english_path.open(encoding="utf-8") as english,
        vietnamese_path.open(encoding="utf-8") as vietnamese,
    ):
        for en_line, vi_line in zip(english, vietnamese, strict=True):
            en_matches = {
                index
                for match in en_pattern.finditer(_normalize(en_line))
                for index in en_indexes[match.group()]
            }
            if not en_matches:
                continue
            vi_matches = {
                index
                for match in vi_pattern.finditer(_normalize(vi_line))
                for index in vi_indexes[match.group()]
            }
            found.update(en_matches & vi_matches)
    if not found:
        raise ValueError("MedEV contains no aligned canonical CarePath terms")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("vi", "en"))
        writer.writerows(pairs[index] for index in sorted(found))
    return len(found)


def prepare(
    manifest_path: Path, canonical_path: Path, output_root: Path
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    sources = {source["source_id"]: source for source in manifest["sources"]}
    outputs: dict[str, Any] = {}
    for source_id, relative_path in (
        ("mts-dialog-train", Path("mts-dialog/train.csv")),
        ("aci-bench-train", Path("aci-bench/train.csv")),
    ):
        source = sources[source_id]
        output = output_root / relative_path
        download(source["download_url"], output, source["sha256"])
        outputs[source_id] = {"path": str(output), "sha256": _sha256(output)}

    medev = sources["medev-terms"]
    downloaded: dict[str, Path] = {}
    for item in medev["input_files"]:
        path = output_root / "medev" / item["path"]
        download(item["download_url"], path, item["sha256"])
        downloaded[item["path"]] = path
    terms = output_root / "medev" / "terms.csv"
    count = derive_medev_terms(
        downloaded["train.en.txt"],
        downloaded["train.vi.txt"],
        canonical_path,
        terms,
    )
    if count != medev["derived_rows"]:
        raise ValueError(
            "derived MedEV terminology row count does not match the manifest"
        )
    if _sha256(terms) != medev["sha256"]:
        raise ValueError("derived MedEV terminology hash does not match the manifest")
    outputs["medev-terms"] = {
        "path": str(terms),
        "sha256": _sha256(terms),
        "rows": count,
    }
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument(
        "--output-root", type=Path, default=Path("/content/carepath_data")
    )
    args = parser.parse_args()
    print(
        json.dumps(
            prepare(args.manifest, args.canonical, args.output_root),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
