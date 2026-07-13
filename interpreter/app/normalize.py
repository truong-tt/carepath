"""Compatibility imports for the shared CarePath normalizers."""

from carepath_shared.normalize import (
    contains_folded,
    fold_for_match,
    normalize_text,
    parse_vietnamese_number_words,
    strip_diacritics,
)

__all__ = [
    "contains_folded",
    "fold_for_match",
    "normalize_text",
    "parse_vietnamese_number_words",
    "strip_diacritics",
]
