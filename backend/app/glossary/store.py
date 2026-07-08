import csv
from pathlib import Path

from rapidfuzz import fuzz
from sqlmodel import Field, Session, SQLModel, select

from app.normalize import fold_for_match
from app.providers.base import GlossaryEntry

SEED_CSV = Path(__file__).with_name("data") / "seed_glossary.csv"


class GlossaryRecord(SQLModel, table=True):
    __tablename__ = "glossary"

    id: int | None = Field(default=None, primary_key=True)
    term_vi: str = Field(index=True)
    term_en: str = Field(index=True)
    kind: str
    lasa_group: str | None = None


def _entry(record: GlossaryRecord) -> GlossaryEntry:
    return GlossaryEntry(
        term_vi=record.term_vi,
        term_en=record.term_en,
        kind=record.kind,
        lasa_group=record.lasa_group,
    )


def seed_glossary(db: Session, csv_path: Path = SEED_CSV) -> int:
    if db.exec(select(GlossaryRecord).limit(1)).first() is not None:
        return 0
    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = [
            GlossaryRecord(
                term_vi=row["term_vi"],
                term_en=row["term_en"],
                kind=row["kind"],
                lasa_group=row["lasa_group"] or None,
            )
            for row in csv.DictReader(handle)
        ]
    db.add_all(rows)
    db.commit()
    return len(rows)


def lookup_glossary(db: Session, text: str, *, fuzzy_threshold: int = 90) -> list[GlossaryEntry]:
    folded_text = fold_for_match(text)
    folded_words = folded_text.split()
    matches: list[GlossaryEntry] = []
    seen: set[int] = set()
    for record in db.exec(select(GlossaryRecord)):
        terms = [record.term_vi, record.term_en]
        if any(fold_for_match(term) in folded_text for term in terms):
            matches.append(_entry(record))
            seen.add(record.id or -1)
            continue
        if any(
            fuzz.ratio(fold_for_match(term), word) >= fuzzy_threshold
            for term in terms
            for word in folded_words
        ):
            if record.id not in seen:
                matches.append(_entry(record))
                seen.add(record.id or -1)
    return matches
