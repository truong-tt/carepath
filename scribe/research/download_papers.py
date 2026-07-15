"""Download and verify the CarePath Scribe research paper snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "papers.json"
PAPERS_DIR = ROOT / "papers"
SHA256_RE = re.compile(r"[0-9a-f]{64}")
REQUIRED_FIELDS = {
    "title",
    "filename",
    "url",
    "research_question",
    "dataset",
    "method",
    "strongest_result",
    "limitations",
    "status",
    "license",
    "carepath_hypothesis",
    "carepath_experiment",
    "sha256",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest() -> list[dict[str, Any]]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    papers = payload.get("papers")
    if not isinstance(papers, list) or not papers:
        raise ValueError("papers.json must contain a non-empty 'papers' list")

    filenames: set[str] = set()
    for index, paper in enumerate(papers, start=1):
        if not isinstance(paper, dict):
            raise ValueError(f"paper {index} must be an object")
        missing = REQUIRED_FIELDS - paper.keys()
        if missing:
            raise ValueError(f"paper {index} is missing: {', '.join(sorted(missing))}")
        filename = paper["filename"]
        if Path(filename).name != filename or not filename.endswith(".pdf"):
            raise ValueError(f"unsafe PDF filename: {filename!r}")
        if filename in filenames:
            raise ValueError(f"duplicate filename: {filename}")
        if not paper["url"].startswith("https://"):
            raise ValueError(f"paper URL must use HTTPS: {paper['url']}")
        if not SHA256_RE.fullmatch(paper["sha256"]):
            raise ValueError(f"invalid SHA-256 for {filename}")
        filenames.add(filename)
    return papers


def verify_pdf(path: Path, expected_hash: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"missing: {path}")
    with path.open("rb") as source:
        if source.read(5) != b"%PDF-":
            raise ValueError(f"not a PDF: {path}")
    actual_hash = sha256(path)
    if actual_hash != expected_hash:
        raise ValueError(
            f"SHA-256 mismatch for {path.name}: expected {expected_hash}, got {actual_hash}"
        )


def download(paper: dict[str, Any]) -> Path:
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    target = PAPERS_DIR / paper["filename"]
    if target.exists():
        verify_pdf(target, paper["sha256"])
        return target

    temporary = target.with_suffix(".pdf.part")
    request = urllib.request.Request(
        paper["url"], headers={"User-Agent": "CarePath-Research/1.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response, temporary.open(
            "wb"
        ) as destination:
            while chunk := response.read(1024 * 1024):
                destination.write(chunk)
        verify_pdf(temporary, paper["sha256"])
        temporary.replace(target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the local snapshot without network access",
    )
    args = parser.parse_args()

    try:
        papers = load_manifest()
        for paper in papers:
            path = PAPERS_DIR / paper["filename"]
            if args.check:
                verify_pdf(path, paper["sha256"])
            else:
                path = download(paper)
            print(f"ok  {path.name}  {paper['sha256']}")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"verified {len(papers)} papers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
