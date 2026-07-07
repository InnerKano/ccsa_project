"""Capital One 360 *checking/savings* statement profile (D19).

Different from the Capital One *card* layout handled by ``GenericLineProfile``:
360 transaction lines carry a single ``Mon Day`` date, a ``Debit``/``Credit``
marker, the amount, and a trailing running-balance column::

    Jun 1 Withdrawal from EXAMPLE MERCHANT Debit - $127.00 $1,916.72
    Jun 1 Deposit from Payroll XXXXXXX2016 Credit + $4,648.44 $6,565.16

The sign comes from the ``Debit``/``Credit`` marker (outflows negative, inflows
positive); the amount is the money token *before* the balance. Non-transaction
lines (Opening/Closing Balance, Interest Rate Change) have no marker and are
ignored — so summary-only 360 statements still yield nothing (D18 behaviour).

Long descriptions occasionally wrap across lines; a small pending buffer merges
the fragment with the amount line (best effort).
"""

from __future__ import annotations

import re

from app.modules.statements.ingest.normalizers import parse_date
from app.modules.statements.ingest.pdf.profiles.base import MONTH, LineRow

_MONEY = r"\$[\d,]+\.\d{2}"

# ``Debit|Credit  [-+]  $amount  $balance`` at end of line.
_TAIL = re.compile(
    rf"(?P<kind>Debit|Credit)\s*(?P<sign>[-+])\s*(?P<amt>{_MONEY})\s+(?P<bal>{_MONEY})\s*$",
    re.IGNORECASE,
)
# Leading ``Mon Day`` date, capturing any description that follows on the line.
_LEAD_DATE = re.compile(rf"^(?P<mon>{MONTH})\.?\s+(?P<day>\d{{1,2}})\b\s*(?P<rest>.*)$", re.IGNORECASE)

# Lines that are never transactions and must reset the pending buffer.
_RESET_MARKERS = (
    "opening balance",
    "closing balance",
    "interest rate change",
    "monthly interest",  # kept only when it also carries Credit/Debit (handled by _TAIL first)
    "annual percentage yield",
    "date description category amount",
    "statement period",
    "account summary",
    "cashflow summary",
    "total ending balance",
    "capitalone.com",
)
_ACCOUNT_HEADER = re.compile(r"-\s*\d{6,}\s*$")  # e.g. "Gastos - 36349161926"
_PAGE_MARKER = re.compile(r"^(?:page\b|-{2}\s*\d+\s+of)", re.IGNORECASE)


class CapitalOne360Profile:
    name = "capital-one-360"
    dedupe = False  # Single-column ledger; repeated charges are distinct.

    def matches(self, pages: list[str]) -> bool:
        blob = "\n".join(pages)
        upper = blob.upper()
        has_360 = "360 CHECKING" in upper or "360 PERFORMANCE SAVINGS" in upper or "CAPITAL ONE 360" in upper
        has_ledger = "DESCRIPTION CATEGORY AMOUNT BALANCE" in upper
        return has_360 and has_ledger

    def extract(self, pages: list[str], year: int) -> list[LineRow]:
        rows: list[LineRow] = []
        pending: list[str] = []

        for page in pages:
            for raw_line in page.splitlines():
                line = raw_line.strip()
                if not line:
                    continue

                tail = _TAIL.search(line)
                if tail is None:
                    # Not an amount line: maybe a wrapped-description fragment.
                    if self._is_noise(line):
                        pending.clear()
                    else:
                        pending.append(line)
                    continue

                prefix = line[: tail.start()].strip()
                lead = _LEAD_DATE.match(prefix)

                if lead is not None:
                    date_str = f"{lead.group('mon')} {lead.group('day')} {year}"
                    desc = lead.group("rest").strip() or self._pending_desc(pending)
                else:
                    # No date on the amount line — it came from the pending buffer.
                    date_str = self._pending_date(pending, year)
                    desc = " ".join(
                        part for part in (self._pending_desc(pending), prefix) if part
                    ).strip()

                pending.clear()
                if not date_str or not desc:
                    continue

                amount = self._signed_amount(tail.group("amt"), tail.group("kind"))
                rows.append(LineRow(_iso(date_str), desc, amount))

        return rows

    @staticmethod
    def _is_noise(line: str) -> bool:
        lower = line.lower()
        if _PAGE_MARKER.match(line) or _ACCOUNT_HEADER.search(line):
            return True
        return any(marker in lower for marker in _RESET_MARKERS)

    def _pending_desc(self, pending: list[str]) -> str:
        text = " ".join(pending).strip()
        lead = _LEAD_DATE.match(text)
        return lead.group("rest").strip() if lead else text

    def _pending_date(self, pending: list[str], year: int) -> str:
        text = " ".join(pending).strip()
        lead = _LEAD_DATE.match(text)
        if lead is None:
            return ""
        return f"{lead.group('mon')} {lead.group('day')} {year}"

    @staticmethod
    def _signed_amount(raw_amount: str, kind: str) -> str:
        value = raw_amount.replace("$", "").replace(",", "").strip()
        if kind.lower() == "debit":
            return f"-{value}"
        return value


def _iso(date_str: str) -> str:
    return parse_date(date_str).isoformat()
