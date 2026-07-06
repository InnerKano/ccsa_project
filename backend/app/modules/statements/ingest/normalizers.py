"""Field-level normalization shared by all parsers.

Handles the real-world variability the MVP commits to: encoding fallbacks,
multiple date formats (EN + ES month names, numeric with locale orientation),
and amounts in US (1,234.56) or EU/LatAm (1.234,56) notation with several sign
conventions (-, (…), + prefix, trailing -, currency symbols).

Deliberately NOT handled here: multi-line rows, fixed-width columns, and page
noise from PDF-statement dumps — those belong to a future adapter (D15).
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app.modules.statements.ingest.base import IngestError

# Month name → number, English and Spanish (full + 3-letter abbreviations).
_MONTHS: dict[str, int] = {
    # English
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
    # Spanish
    "ene": 1, "enero": 1, "febrero": 2, "marzo": 3, "abr": 4, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "ago": 8, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "set": 9, "octubre": 10,
    "noviembre": 11, "dic": 12, "diciembre": 12,
}

_NUMERIC_DATE = re.compile(r"^(\d{1,4})[/\-.](\d{1,2})[/\-.](\d{1,4})$")
_TEXT_DATE = re.compile(r"^([A-Za-zÁÉÍÓÚáéíóúñÑ]+)\.?\s+(\d{1,2})(?:,?\s+(\d{4}))?$")
_TEXT_DATE_DAY_FIRST = re.compile(r"^(\d{1,2})\s+(?:de\s+)?([A-Za-zÁÉÍÓÚáéíóúñÑ]+)\.?(?:\s+(?:de\s+)?(\d{4}))?$")


def decode_bytes(content: bytes) -> str:
    """Decode upload bytes, tolerating non-UTF-8 exports (e.g. Windows/Latin-1)."""
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise IngestError("File encoding not supported (expected UTF-8 or Latin-1)")


def normalize_description(raw: str) -> str:
    """Trim, collapse whitespace, truncate to the column limit — DATA_MODEL.md §5."""
    return re.sub(r"\s+", " ", raw.strip())[:512]


def detect_dayfirst(values: list[str]) -> bool:
    """Infer whether a numeric date column is day-first (DD/MM) or month-first.

    Votes across the whole column: a part > 12 can only be a day. Ties or
    ambiguity default to month-first (US), matching the MVP default.
    """
    dayfirst_votes = 0
    monthfirst_votes = 0
    for value in values:
        match = _NUMERIC_DATE.match(value.strip())
        if match is None:
            continue
        first, second, third = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        if len(match.group(1)) == 4:  # YYYY-MM-DD, orientation is unambiguous
            continue
        if first > 12 and second <= 12:
            dayfirst_votes += 1
        elif second > 12 and first <= 12:
            monthfirst_votes += 1
    return dayfirst_votes > monthfirst_votes


def _parse_text_date(text: str) -> date | None:
    """Parse 'Sep 4', 'Sep 4 2023', '4 de abril de 2026', '4 abril'."""
    match = _TEXT_DATE.match(text)
    if match is not None:
        month = _MONTHS.get(match.group(1).lower())
        if month is not None:
            day = int(match.group(2))
            year = int(match.group(3)) if match.group(3) else date.today().year
            return _safe_date(year, month, day)

    match = _TEXT_DATE_DAY_FIRST.match(text)
    if match is not None:
        month = _MONTHS.get(match.group(2).lower())
        if month is not None:
            day = int(match.group(1))
            year = int(match.group(3)) if match.group(3) else date.today().year
            return _safe_date(year, month, day)
    return None


def _parse_numeric_date(text: str, dayfirst: bool | None) -> date | None:
    match = _NUMERIC_DATE.match(text)
    if match is None:
        return None
    g1, g2, g3 = match.group(1), match.group(2), match.group(3)

    if len(g1) == 4:  # ISO: YYYY-MM-DD
        return _safe_date(int(g1), int(g2), int(g3))

    first, second = int(g1), int(g2)
    year = int(g3)
    if year < 100:  # two-digit year → 2000s
        year += 2000

    if first > 12:
        day, month = first, second
    elif second > 12:
        day, month = second, first
    elif dayfirst:
        day, month = first, second
    else:
        month, day = first, second
    return _safe_date(year, month, day)


def _safe_date(year: int, month: int, day: int) -> date:
    try:
        return date(year, month, day)
    except ValueError as exc:
        raise IngestError("Invalid calendar date") from exc


def parse_date(value: str, *, date_format: str | None = None, dayfirst: bool | None = None) -> date:
    text = value.strip()
    if not text:
        raise IngestError("Empty date value")

    if date_format:
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError as exc:
            raise IngestError("Date does not match the provided format") from exc

    parsed = _parse_numeric_date(text, dayfirst) or _parse_text_date(text)
    if parsed is None:
        raise IngestError("Unrecognized date format")
    return parsed


def _resolve_decimal_text(text: str, style: str) -> str:
    """Return a Python-parseable decimal string from a cleaned numeric token."""
    has_comma = "," in text
    has_dot = "." in text

    if style == "us":
        return text.replace(",", "")
    if style == "eu":
        return text.replace(".", "").replace(",", ".")

    # auto-detect
    if has_comma and has_dot:
        # The right-most separator is the decimal point.
        if text.rfind(",") > text.rfind("."):
            return text.replace(".", "").replace(",", ".")  # eu
        return text.replace(",", "")  # us
    if has_comma:
        # One comma: decimal if it has 1-2 trailing digits, else thousands.
        integer, _, fraction = text.rpartition(",")
        if integer and len(fraction) in (1, 2):
            return text.replace(",", ".")
        return text.replace(",", "")
    return text  # only dots or plain integer → treat dot as decimal point


def parse_amount(value: str, style: str = "auto") -> Decimal:
    text = value.strip()
    if not text or text in {"-", "+"}:
        raise IngestError("Empty amount value")

    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]

    # Strip currency symbols, spaces, and letters (e.g. "$", "COP", "USD").
    text = re.sub(r"[^\d,.\-+]", "", text)

    if text.startswith("+"):
        text = text[1:]
    if text.startswith("-"):
        negative = True
        text = text[1:]
    if text.endswith("-"):  # some exports put the sign after the number
        negative = True
        text = text[:-1]

    if not text:
        raise IngestError("Invalid amount format")

    try:
        amount = Decimal(_resolve_decimal_text(text, style))
    except InvalidOperation as exc:
        raise IngestError("Invalid amount format") from exc

    if negative:
        amount = -amount
    return amount.quantize(Decimal("0.01"))
