"""Generic multi-bank line profile — the original A2.2/D17 line scan.

Handles Capital One *card* (two-date rows), Bank of America checking
(``MM/DD/YY`` rows), Discover (``MM/DD`` rows), and a last-resort "loose" row
whose amount is the trailing ``$X.XX`` token. Section headers (purchases vs
payments/deposits) drive the sign, matching the checking-account convention
used across the project.

This profile is the fallback: ``matches`` is always True, so it runs last in
the registry after the bank-specific profiles.
"""

from __future__ import annotations

import re
from decimal import Decimal

from app.modules.statements.ingest.normalizers import parse_date
from app.modules.statements.ingest.pdf.profiles.base import MONTH, LineRow

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

# Capital One card: ``May 17 May 18 MERCHANT $27.99`` or ``- $200.00``
_CAPONE_ROW = re.compile(
    rf"^(?P<m1>{MONTH})\.?\s+(?P<d1>\d{{1,2}})\s+(?P<m2>{MONTH})\.?\s+(?P<d2>\d{{1,2}})\s+"
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

_AMOUNT_TAIL = re.compile(r"-?\s*\$[\d,]+\.\d{2}\s*$")
_LOOSE_DATE = re.compile(
    r"^(?:\d{1,2}/\d{1,2}/\d{2,4}|"
    rf"{MONTH}\.?\s+\d{{1,2}}(?:,?\s+\d{{4}})?)",
    re.IGNORECASE,
)


def _month_day_to_iso(month_token: str, day: int, year: int) -> str:
    return parse_date(f"{month_token} {day} {year}").isoformat()


def _normalize_amount(raw: str, section: str) -> str:
    """Return a string parseable by ``parse_amount`` with the correct sign."""
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


def _parse_capone_line(line: str, section: str, year: int) -> LineRow | None:
    match = _CAPONE_ROW.match(line.strip())
    if match is None:
        return None
    month_token = match.group("m1")
    day = int(match.group("d1"))
    desc = match.group("desc").strip()
    amt = _normalize_amount(match.group("amt"), section or "purchase")
    return LineRow(_month_day_to_iso(month_token, day, year), desc, amt)


def _parse_boa_line(line: str, section: str) -> LineRow | None:
    match = _BOA_ROW.match(line.strip())
    if match is None:
        return None
    date_str = match.group(1)
    desc = match.group(2).strip()
    raw_amt = match.group(3)
    if section == "deposit" and raw_amt.startswith("-"):
        raw_amt = raw_amt.lstrip("-")
    return LineRow(date_str, desc, _normalize_amount(raw_amt, section or "withdrawal"))


def _parse_discover_line(line: str, section: str, year: int) -> LineRow | None:
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
    return LineRow(f"{mmdd}/{year}", description, amt)


def _document_is_discover(pages: list[str]) -> bool:
    blob = "\n".join(pages).upper()
    return "DISCOVER" in blob and "DISCOVER.COM" in blob


def _parse_loose_amount_line(line: str, section: str) -> LineRow | None:
    """Last resort: line ends with ``$X.XX`` and starts with a date token."""
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
    return LineRow(parts[0], parts[1], _normalize_amount(amt_raw, section or "purchase"))


class GenericLineProfile:
    """Fallback line profile (Capital One card / BoA / Discover / loose)."""

    name = "generic-lines"
    dedupe = True  # Capital One card reprints each transaction on ES + EN pages.

    def matches(self, pages: list[str]) -> bool:
        return True

    def extract(self, pages: list[str], year: int) -> list[LineRow]:
        parsed: list[LineRow] = []
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
        return parsed
