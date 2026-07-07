"""PNC Virtual Wallet statement profile (D19).

PNC groups transactions under section headers and, unlike every other layout,
prints columns in ``Date  Amount  Description`` order — the amount comes
*before* the description and carries no sign or currency symbol::

    Deposits and Other Additions ...
    Date Amount Description
    11/14 1,052.50 Direct Deposit - Payroll Example Co
    690387
    11/19 26.65 Recurring Debit Card Netflix, Inc.

The sign is implied by the active section (additions positive; withdrawals,
purchases, and electronic deductions negative). Dates are ``MM/DD``; the year
comes from the statement-period banner. Balance tables (``Daily Balance
Detail``) and summaries are excluded.

Only the primary ``MM/DD amount description`` line is captured. Wrapped
description tails (reference codes like ``690387`` or ``Bevera``) are dropped on
purpose: PNC renders two columns, so summary-sentence fragments interleave with
transaction rows and cannot be reliably attached. The primary description still
identifies the merchant (NETFLIX, AMAZON, CTLP*MILL CREEK, …), which is what the
analysis layer canonicalizes (D17). Genuine repeated charges are preserved
(``dedupe = False``).
"""

from __future__ import annotations

import re
from decimal import Decimal

from app.modules.statements.ingest.pdf.profiles.base import LineRow

# ``MM/DD  amount  description`` — amount is US style (comma thousands).
_ROW = re.compile(r"^(?P<mm>\d{2})/(?P<dd>\d{2})\s+(?P<amt>[\d,]+\.\d{2})\s+(?P<desc>\S.*)$")

_POSITIVE_SECTIONS = (
    "deposits and other additions",
    "deposits and additions",
)
_NEGATIVE_SECTIONS = (
    "banking / debit card withdrawals and purchases",
    "banking/debit card withdrawals and purchases",
    "checks and substitute checks",
    "online and electronic banking deductions",
    "debit card withdrawals and purchases",
)
# Headers/sections that end transaction capture until the next section header.
_STOP_SECTIONS = (
    "daily balance detail",
    "transaction summary",
    "balance summary",
    "account summary",
    "overdraft and returned item",
    "important account information",
    "important deposit transaction",
)
_COLUMN_HEADER = "date amount description"


class PncProfile:
    name = "pnc-virtual-wallet"
    dedupe = False  # Repeated identical vending charges are distinct transactions.

    def matches(self, pages: list[str]) -> bool:
        blob = "\n".join(pages).lower()
        return "pnc bank" in blob or "virtual wallet" in blob

    def extract(self, pages: list[str], year: int) -> list[LineRow]:
        rows: list[LineRow] = []
        sign = 0  # +1 additions, -1 deductions, 0 = not inside a transaction section

        for page in pages:
            for raw_line in page.splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                lower = line.lower()

                section_sign = self._section_sign(lower)
                if section_sign is not None:
                    sign = section_sign
                    continue
                if any(stop in lower for stop in _STOP_SECTIONS):
                    sign = 0
                    continue
                if _COLUMN_HEADER in lower or sign == 0:
                    continue

                match = _ROW.match(line)
                if match is not None:
                    amount = self._signed_amount(match.group("amt"), sign)
                    date_str = f"{match.group('mm')}/{match.group('dd')}/{year}"
                    rows.append(LineRow(date_str, match.group("desc").strip(), amount))

        return rows

    @staticmethod
    def _section_sign(lower: str) -> int | None:
        for marker in _POSITIVE_SECTIONS:
            if marker in lower:
                return 1
        for marker in _NEGATIVE_SECTIONS:
            if marker in lower:
                return -1
        return None

    @staticmethod
    def _signed_amount(raw_amount: str, sign: int) -> str:
        value = Decimal(raw_amount.replace(",", ""))
        if sign < 0:
            value = -value
        return str(value)
