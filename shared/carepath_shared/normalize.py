import re
import unicodedata

WORD_RE = re.compile(r"\w+", re.UNICODE)

NUMBER_VALUES = {
    "mot": 1,
    "hai": 2,
    "ba": 3,
    "bon": 4,
    "tu": 4,
    "nam": 5,
    "lam": 5,
    "nham": 5,
    "sau": 6,
    "bay": 7,
    "tam": 8,
    "chin": 9,
}
NUMBER_TOKENS = set(NUMBER_VALUES) | {
    "muoi",
    "tram",
    "nghin",
    "ngan",
    "linh",
    "le",
    "ruoi",
    "nua",
}

NUMBER_FOLLOWERS = {
    "vien",
    "goi",
    "ong",
    "lan",
    "ngay",
    "tuan",
    "thang",
    "gio",
    "mg",
    "ml",
    "mcg",
    "tuoi",
}

UNIT_PATTERNS = [
    (r"\bmi\s*-?\s*li\s*-?\s*gam\b|\bmiligrams?\b|\bmilligrams?\b", "mg"),
    (r"\bmi\s*-?\s*li\s*-?\s*lit\b|\bmi\s*-?\s*li\s*-?\s*lít\b|\bmililit(?:s)?\b", "ml"),
    (r"\bmicrograms?\b|\bmcg\b|\bµg\b", "mcg"),
]


def strip_diacritics(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def fold_for_match(text: str) -> str:
    return strip_diacritics(unicodedata.normalize("NFC", text)).casefold()


def contains_folded(haystack: str, needle: str) -> bool:
    return fold_for_match(needle) in fold_for_match(haystack)


def _word_key(word: str) -> str:
    if word.casefold() == "sau":
        return ""
    return fold_for_match(word).replace("đ", "d")


def _parse_under_1000(tokens: list[str]) -> float | None:
    total = 0
    i = 0
    if i + 1 < len(tokens) and tokens[i] in NUMBER_VALUES and tokens[i + 1] == "tram":
        total += NUMBER_VALUES[tokens[i]] * 100
        i += 2
        if i < len(tokens) and tokens[i] in {"linh", "le"}:
            i += 1

    if i >= len(tokens):
        return float(total)
    if tokens[i] == "muoi":
        total += 10
        i += 1
        if i < len(tokens) and tokens[i] in NUMBER_VALUES:
            total += NUMBER_VALUES[tokens[i]]
            i += 1
    elif i + 1 < len(tokens) and tokens[i] in NUMBER_VALUES and tokens[i + 1] == "muoi":
        total += NUMBER_VALUES[tokens[i]] * 10
        i += 2
        if i < len(tokens) and tokens[i] in NUMBER_VALUES:
            total += NUMBER_VALUES[tokens[i]]
            i += 1
    elif tokens[i] in NUMBER_VALUES:
        total += NUMBER_VALUES[tokens[i]]
        i += 1

    if i < len(tokens) and tokens[i] == "ruoi":
        total += 0.5
        i += 1
    return float(total) if i == len(tokens) else None


def parse_vietnamese_number_words(words: list[str]) -> float | None:
    tokens = [_word_key(word) for word in words]
    if tokens == ["nua"]:
        return 0.5
    if "nghin" in tokens or "ngan" in tokens:
        split_at = tokens.index("nghin") if "nghin" in tokens else tokens.index("ngan")
        left = _parse_under_1000(tokens[:split_at])
        right = _parse_under_1000(tokens[split_at + 1 :]) if split_at + 1 < len(tokens) else 0
        if left is None or right is None:
            return None
        return left * 1000 + right
    return _parse_under_1000(tokens)


def _format_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else str(value).rstrip("0").rstrip(".")


def _is_sentence_initial(text: str, start: int) -> bool:
    before = text[:start].rstrip()
    return not before or before[-1] in ".!?\n\r"


def _is_capitalized_name_candidate(text: str, match: re.Match[str]) -> bool:
    word = match.group(0)
    return word[:1].isupper() and not _is_sentence_initial(text, match.start())


def _next_word_key(matches: list[re.Match[str]], index: int) -> str:
    return _word_key(matches[index].group(0)) if index < len(matches) else ""


def _replace_number_words(text: str) -> str:
    parts: list[str] = []
    last = 0
    matches = list(WORD_RE.finditer(text))
    i = 0
    while i < len(matches):
        key = _word_key(matches[i].group(0))
        if key not in NUMBER_TOKENS:
            i += 1
            continue

        j = i
        words: list[str] = []
        while j < len(matches):
            gap = text[matches[j - 1].end() : matches[j].start()] if j > i else ""
            next_key = _word_key(matches[j].group(0))
            if next_key not in NUMBER_TOKENS or (j > i and gap != " "):
                break
            words.append(matches[j].group(0))
            j += 1

        value = parse_vietnamese_number_words(words)
        if value is None:
            i += 1
            continue
        is_single_token = j == i + 1
        if _is_capitalized_name_candidate(text, matches[i]):
            i += 1
            continue
        if is_single_token and _next_word_key(matches, j) not in NUMBER_FOLLOWERS:
            i += 1
            continue
        if (
            is_single_token
            and _word_key(matches[i].group(0)) == "nam"
            and j < len(matches)
            and matches[j].group(0).isdigit()
        ):
            i += 1
            continue
        parts.append(text[last : matches[i].start()])
        parts.append(_format_number(value))
        last = matches[j - 1].end()
        i = j

    parts.append(text[last:])
    return "".join(parts)


def _canonicalize_units(text: str) -> str:
    folded = text
    for pattern, replacement in UNIT_PATTERNS:
        folded = re.sub(pattern, replacement, folded, flags=re.IGNORECASE)
    return folded


def _normalize_relative_dates(text: str) -> str:
    return re.sub(
        r"\bsau\s+(\d+(?:\.\d+)?)\s+ng[aà]y\b",
        lambda match: f"+{match.group(1)} days",
        text,
        flags=re.IGNORECASE,
    )


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text).strip()
    normalized = _canonicalize_units(normalized)
    normalized = _replace_number_words(normalized)
    normalized = _normalize_relative_dates(normalized)
    return re.sub(r"\s+", " ", normalized)


def normalize_for_metrics(text: str) -> str:
    """Preserve the case-insensitive text contract used by GEC scorecards."""

    text = text.lower().strip()
    text = unicodedata.normalize("NFC", text)
    return re.sub(r"\s+", " ", text)


def normalize_for_match(text: str) -> str:
    """Fold text for lexical medical-term retrieval."""

    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("đ", "d")
    text = re.sub(r"[^a-z0-9%/.,]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()
