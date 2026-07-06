"""Line-oriented PDF transaction extraction (fallback when tables fail).

Many US card/bank statements (Capital One, Bank of America) render transactions
as fixed-width or space-separated *lines* rather than extractable tables.
This module scans page text, tracks statement sections (purchases vs payments),
and emits normalized tabular rows for ``columns.parse_tabular_rows``.

Amount sign follows the checking-account convention used elsewhere in the
project: outflows (purchases, withdrawals) are negative; inflows (payments,
deposits, credits) are positive.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from app.modules.statements.ingest.normalizers import parse_date

# --- section markers (EN + ES) -----------------------------------------------
_PURCHASE_MARKERS = (
    "transactions",
    "transacciones",
    "purchases",
    "compras",
    "withdrawals and other subtractions",
    "retiros y otras substracciones",
    "date purchases amount",
)
_PAYMENT_MARKERS = (
    "payments, credits",
    "payments, credits and adjustments",
    "payments and credits",
    "payments and credits and adjustments",
    "date payments and credits",
    "pagos, créditos",
    "pagos, créditos y ajustes",
    "pagos, creditos",
    "pagos, creditos y ajustes",
)
_DEPOSIT_MARKERS = (
    "deposits and other additions",
    "depósitos y otras adiciones",
    "depositos y otras adiciones",
)
_SKIP_MARKERS = (
    "continued on the next page",
    "continua en la página",
    "continua en la pagina",
    "total ",
    "totals ",
    "totales ",
    "page ",
    "página ",
    "information for you",
    "información adicional",
    "beginning balance",
    "ending balance",
    "previous balance",
    "new balance",
    "minimum payment",
    "account summary",
    "saldo anterior",
    "saldo nuevo",
    "pago mínimo",
    "resumen de la cuenta",
    "balance transfers",
    "fees charged",
    "interest charged",
)

_MONTH = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|"
    r"ene(?:ro)?|feb(?:rero)?|mar(?:zo)?|abr(?:il)?|mayo|jun(?:io)?|jul(?:io)?|"
    r"ago(?:sto)?|sept(?:iembre)?|set(?:iembre)?|oct(?:ubre)?|nov(?:iembre)?|dic(?:iembre)?)"
)

# Capital One card: ``May 17 May 18 MERCHANT $27.99`` or ``- $200.00``
_CAPONE_ROW = re.compile(
    rf"^(?P<m1>{_MONTH})\.?\s+(?P<d1>\d{{1,2}})\s+(?P<m2>{_MONTH})\.?\s+(?P<d2>\d{{1,2}})\s+"
    r"(?P<desc>.+?)\s+(?P<amt>-?\s*\$[\d,]+\.\d{2})\s*$",
    re.IGNORECASE,
)

# BOA checking: ``05/28/19  CHECKCARD ...  -112.10`` (amount may omit $)
_BOA_ROW = re.compile(
    r"^(\d{2}/\d{2}/\d{2})\s+(.+?)\s+(-?\$?[\d,]+\.\d{2})\s*$",
)

# Header row with recognizable column labels (single line).
_HEADER_ROW = re.compile(
    r"(trans\.?\s*date|transaction date|fecha de transacc).*(description|descripci).*(amount|cantidad|monto)",
    re.IGNORECASE,
)

# Billing / statement period → default year for month-only dates.
_PERIOD_YEAR = re.compile(
    rf"(?:{_MONTH})\.?\s+\d{{1,2}},?\s+(\d{{4}})\s*[-–]",
    re.IGNORECASE,
)
_PERIOD_YEAR_ALT = re.compile(
    r"(\d{4})\s*[-–]\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
    re.IGNORECASE,
)
_PERIOD_OPEN_CLOSE = re.compile(
    r"OPEN TO CLOSE DATE:\s*\d{2}/\d{2}/(\d{4})",
    re.IGNORECASE,
)
_PERIOD_NUMERIC = re.compile(
    r"\d{2}/\d{2}/(\d{4})\s*[-–]\s*\d{2}/\d{2}/\d{4}",
)

_AMOUNT_TAIL = re.compile(r"-?\s*\$[\d,]+\.\d{2}\s*$")
_LOOSE_DATE = re.compile(
    r"^(?:\d{1,2}/\d{1,2}/\d{2,4}|"
    rf"{_MONTH}\.?\s+\d{{1,2}}(?:,?\s+\d{{4}})?)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class _LineRow:
    date: str
    description: str
    amount: str


def infer_statement_year(pages: list[str]) -> int | None:
    """Best-effort year from statement period banners."""
    blob = "\n".join(pages)
    for pattern in (_PERIOD_YEAR, _PERIOD_YEAR_ALT, _PERIOD_OPEN_CLOSE, _PERIOD_NUMERIC):
        match = pattern.search(blob)
        if match:
            return int(match.group(1))
    return None


def _month_day_to_iso(month_token: str, day: int, year: int) -> str:
    return parse_date(f"{month_token} {day} {year}").isoformat()


def _normalize_amount(raw: str, section: str) -> str:
    """Return a string parseable by ``parse_amount`` with correct sign."""
    text = raw.strip().replace(" ", "")
    negative = text.startswith("-")
    text = text.lstrip("-").lstrip("$")
    if not text:
        raise ValueError("empty amount")
    value = Decimal(text.replace(",", ""))
    if section in ("purchase", "withdrawal"):
        return str(-abs(value))
    if section in ("payment", "deposit"):
        return str(abs(value))
    if negative:
        return str(-abs(value))
    return str(value)


def _detect_section(line_lower: str) -> str | None:
    for marker in _PAYMENT_MARKERS:
        if marker in line_lower:
            return "payment"
    for marker in _DEPOSIT_MARKERS:
        if marker in line_lower:
            return "deposit"
    for marker in _PURCHASE_MARKERS:
        if marker in line_lower:
            return "purchase"
    if "withdrawals and other" in line_lower or "retiros y otras" in line_lower:
        return "withdrawal"
    return None


def _should_skip(line: str) -> bool:
    lower = line.lower()
    if _detect_section(lower) is not None or _HEADER_ROW.search(line):
        return False
    if any(marker in lower for marker in _SKIP_MARKERS):
        return True
    if lower.startswith("name#") and "transactions" not in lower and "payments" not in lower:
        return True
    if "ending in" in lower and "card" in lower:
        return True
    return False


def _parse_capone_line(line: str, section: str, year: int) -> _LineRow | None:
    match = _CAPONE_ROW.match(line.strip())
    if match is None:
        return None
    month_token = match.group("m1")
    day = int(match.group("d1"))
    desc = match.group("desc").strip()
    amt = _normalize_amount(match.group("amt"), section or "purchase")
    return _LineRow(_month_day_to_iso(month_token, day, year), desc, amt)


def _parse_boa_line(line: str, section: str) -> _LineRow | None:
    match = _BOA_ROW.match(line.strip())
    if match is None:
        return None
    date_str = match.group(1)
    desc = match.group(2).strip()
    # BOA amounts already carry sign; section refines deposit vs withdrawal.
    raw_amt = match.group(3)
    if section == "deposit" and raw_amt.startswith("-"):
        raw_amt = raw_amt.lstrip("-")
    return _LineRow(date_str, desc, _normalize_amount(raw_amt, section or "withdrawal"))


def _parse_discover_line(line: str, section: str, year: int) -> _LineRow | None:
    """Discover row: ``04/17 MERCHANT ... $30.00`` (MM/DD at line start)."""
    match = re.match(r"^(\d{2}/\d{2})\s+(.+)$", line.strip())
    if match is None:
        return None
    mmdd, rest = match.group(1), match.group(2)
    amount_match = re.search(r"-?\$[\d,]+\.\d{2}", rest)
    if amount_match is None:
        return None
    description = rest[: amount_match.start()].strip()
    description = re.sub(r"\s+MERCHANT CATEGORY\s*$", "", description, flags=re.IGNORECASE)
    if not description or description.upper().startswith("SEE DETAILS"):
        return None
    payment_section = section in ("payment", "deposit")
    purchase_section = section in ("purchase", "withdrawal")
    if "PAYMENT" in description.upper() or "CREDIT" in description.upper() or "DIRECTPAY" in description.upper():
        payment_section = True
    effective = "payment" if payment_section and not purchase_section else section or "purchase"
    amt = _normalize_amount(amount_match.group(0), effective)
    return _LineRow(f"{mmdd}/{year}", description, amt)


def _document_is_discover(pages: list[str]) -> bool:
    blob = "\n".join(pages).upper()
    return "DISCOVER" in blob and "DISCOVER.COM" in blob


def _parse_loose_amount_line(line: str, section: str) -> _LineRow | None:
    """Last-resort: line ends with ``$X.XX`` and starts with a date token."""
    stripped = line.strip()
    amt_match = _AMOUNT_TAIL.search(stripped)
    if amt_match is None:
        return None
    amt_raw = amt_match.group(0)
    prefix = stripped[: amt_match.start()].strip()
    if not prefix:
        return None
    parts = prefix.split(None, 1)
    if len(parts) < 2:
        return None
    if not _LOOSE_DATE.match(parts[0]):
        return None
    return _LineRow(parts[0], parts[1], _normalize_amount(amt_raw, section or "purchase"))


def extract_line_rows(pages: list[str]) -> list[list[str]]:
    """Scan page texts and return ``[header, ...data]`` rows for ``columns.py``."""
    year = infer_statement_year(pages)
    if year is None:
        from datetime import date as date_cls

        year = date_cls.today().year

    parsed: list[_LineRow] = []
    section = "purchase"
    is_discover = _document_is_discover(pages)

    for page in pages:
        for raw_line in page.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            lower = line.lower()
            new_section = _detect_section(lower)
            if new_section is not None:
                section = new_section
                continue
            if _should_skip(line) or _HEADER_ROW.search(line):
                continue

            row = (
                _parse_capone_line(line, section, year)
                or _parse_boa_line(line, section)
                or (_parse_discover_line(line, section, year) if is_discover else None)
                or _parse_loose_amount_line(line, section)
            )
            if row is not None and row.description:
                parsed.append(row)

    if not parsed:
        return []

    header = ["date", "description", "amount"]
    data = [[r.date, r.description, r.amount] for r in parsed]
    return [header, *data]


def dedupe_rows(rows: list[list[str]]) -> list[list[str]]:
    """Drop duplicate data rows (e.g. bilingual Capital One statements)."""
    if len(rows) < 2:
        return rows
    header, *data = rows
    seen: set[tuple[str, ...]] = set()
    unique: list[list[str]] = []
    for row in data:
        key = tuple(cell.strip() for cell in row)
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return [header, *unique]
