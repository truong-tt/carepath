import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a licensed Meddict CSV to glossary rows.")
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--i-understand-license", action="store_true")
    args = parser.parse_args()
    if not args.i_understand_license:
        raise SystemExit("Meddict license is unverified; pass --i-understand-license to import.")

    with args.source.open(encoding="utf-8", newline="") as source, args.target.open(
        "w", encoding="utf-8", newline=""
    ) as target:
        reader = csv.DictReader(source)
        writer = csv.DictWriter(target, fieldnames=["term_vi", "term_en", "kind", "lasa_group"])
        writer.writeheader()
        for row in reader:
            writer.writerow(
                {
                    "term_vi": row.get("term_vi") or row.get("vi") or "",
                    "term_en": row.get("term_en") or row.get("en") or "",
                    "kind": row.get("kind") or "med_term",
                    "lasa_group": row.get("lasa_group") or "",
                }
            )


if __name__ == "__main__":
    main()
