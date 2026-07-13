import json

from app.glossary import lookup_glossary, seed_glossary
from app.risk.engine import LEXICON_DIR


def test_seed_glossary_loads_clinician_editable_csv(db_session) -> None:
    inserted = seed_glossary(db_session)

    assert inserted >= 150
    assert seed_glossary(db_session) == 0


def test_lookup_glossary_exact_folded_fuzzy_and_lasa(db_session) -> None:
    seed_glossary(db_session)

    folded = lookup_glossary(db_session, "benh nhan di ung thuoc khang sinh")
    fuzzy = lookup_glossary(db_session, "Uong Augmentn sau an")
    lasa = lookup_glossary(db_session, "Dang dung Lasix")

    assert any(entry.term_vi == "thuốc kháng sinh" for entry in folded)
    assert any(entry.term_vi == "Augmentin" for entry in fuzzy)
    assert any(entry.lasa_group == "Lasix" for entry in lasa)


def test_required_lexicon_files_are_clinician_editable_data() -> None:
    expected = {
        "red_flags.json",
        "negation_cues.json",
        "units_forms.json",
        "routes.json",
        "laterality.json",
        "pregnancy.json",
        "lasa_pairs.json",
        "abbreviations_vi.json",
        "pronoun_cues.json",
        "subject_omission.json",
        "symptom_severity.json",
        "medical_history.json",
        "body_locations.json",
    }

    assert expected == {path.name for path in LEXICON_DIR.glob("*.json")}
    abbreviations = json.loads((LEXICON_DIR / "abbreviations_vi.json").read_text(encoding="utf-8"))
    assert abbreviations["HA"] == "huyết áp"
