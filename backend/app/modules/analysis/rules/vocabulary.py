"""Bilingual (EN + ES) rule data for Layer 1 analysis.

This is deliberately *data*, separate from the logic in ``engine.py``, so the
vocabulary can grow (more merchants, more keywords) without touching the
detection algorithm. Ingestion accepts EN + ES exports (D15), so categorization
must recognize both languages (see middle-phases.md, A3).

All keys are matched against an upper-cased description, so keys are UPPERCASE.
"""

from __future__ import annotations

# Controlled category vocabulary (D9) — validated in app code, not DB enums.
CATEGORIES: frozenset[str] = frozenset(
    {
        "streaming",
        "music",
        "software",
        "gaming",
        "shopping",
        "groceries",
        "food",
        "transport",
        "fuel",
        "utilities",
        "telecom",
        "fitness",
        "insurance",
        "income",
        "other",
    }
)

# Categories a rules-only pass will actively recommend cancelling (D16).
# Everything else recurring is still detected and surfaced, but not auto-flagged
# for cancellation (e.g. utilities, insurance, groceries are usually essential).
DISCRETIONARY_CATEGORIES: frozenset[str] = frozenset(
    {"streaming", "music", "gaming", "software", "fitness"}
)

# Known merchants: (substring, canonical name, category).
# Scanned in order — put more specific substrings first (e.g. "UBER EATS"
# before "UBER", "AMAZON PRIME" before "AMAZON").
MERCHANT_ALIASES: tuple[tuple[str, str, str], ...] = (
    ("NETFLIX", "NETFLIX", "streaming"),
    ("SPOTIFY", "SPOTIFY", "music"),
    ("DISNEY", "DISNEY+", "streaming"),
    ("HBO", "HBO MAX", "streaming"),
    ("PARAMOUNT", "PARAMOUNT+", "streaming"),
    ("YOUTUBE PREMIUM", "YOUTUBE PREMIUM", "streaming"),
    ("YOUTUBE", "YOUTUBE", "streaming"),
    ("APPLE MUSIC", "APPLE MUSIC", "music"),
    ("DEEZER", "DEEZER", "music"),
    ("PRIME VIDEO", "AMAZON PRIME", "streaming"),
    ("AMAZON PRIME", "AMAZON PRIME", "shopping"),
    ("ADOBE", "ADOBE", "software"),
    ("MICROSOFT", "MICROSOFT", "software"),
    ("OFFICE 365", "MICROSOFT 365", "software"),
    ("GOOGLE", "GOOGLE", "software"),
    ("DROPBOX", "DROPBOX", "software"),
    ("ICLOUD", "APPLE ICLOUD", "software"),
    ("APPLE", "APPLE", "software"),
    ("UBER EATS", "UBER EATS", "food"),
    ("RAPPI", "RAPPI", "food"),
    ("UBER", "UBER", "transport"),
    ("DIDI", "DIDI", "transport"),
    ("SMARTFIT", "SMART FIT", "fitness"),
    ("SMART FIT", "SMART FIT", "fitness"),
    ("BODYTECH", "BODYTECH", "fitness"),
)

# Generic keyword → category, bilingual. Used when no known merchant matched.
# Scanned in order; first hit wins.
CATEGORY_KEYWORDS: tuple[tuple[str, str], ...] = (
    # income (also excluded from subscription detection via sign in engine)
    ("PAYROLL", "income"),
    ("SALARY", "income"),
    ("NOMINA", "income"),
    ("NÓMINA", "income"),
    ("SALARIO", "income"),
    # groceries
    ("WHOLE FOODS", "groceries"),
    ("SUPERMARKET", "groceries"),
    ("SUPERMERCADO", "groceries"),
    ("GROCERY", "groceries"),
    ("MARKET", "groceries"),
    ("EXITO", "groceries"),
    ("WALMART", "groceries"),
    ("CARREFOUR", "groceries"),
    ("KROGER", "groceries"),
    ("TIENDA", "groceries"),
    ("D1", "groceries"),
    # fuel
    ("SHELL", "fuel"),
    ("GASOLIN", "fuel"),
    ("GAS STATION", "fuel"),
    ("ESTACION", "fuel"),
    ("COMBUSTIBLE", "fuel"),
    ("TEXACO", "fuel"),
    ("TERPEL", "fuel"),
    # food / dining
    ("RESTAURANT", "food"),
    ("RESTAURANTE", "food"),
    ("COFFEE", "food"),
    ("CAFE", "food"),
    ("STARBUCKS", "food"),
    ("MCDONALD", "food"),
    ("COMIDA", "food"),
    # transport
    ("LYFT", "transport"),
    ("TAXI", "transport"),
    ("METRO", "transport"),
    ("PARKING", "transport"),
    # utilities
    ("ELECTRIC", "utilities"),
    ("ENERGIA", "utilities"),
    ("WATER", "utilities"),
    ("ACUEDUCTO", "utilities"),
    ("LUZ", "utilities"),
    ("AGUA", "utilities"),
    # telecom
    ("INTERNET", "telecom"),
    ("CLARO", "telecom"),
    ("MOVISTAR", "telecom"),
    ("TIGO", "telecom"),
    ("VERIZON", "telecom"),
    ("AT&T", "telecom"),
    # insurance
    ("INSURANCE", "insurance"),
    ("SEGURO", "insurance"),
    # shopping
    ("AMAZON", "shopping"),
    ("MERCADOLIBRE", "shopping"),
    ("MERCADO LIBRE", "shopping"),
    ("STORE", "shopping"),
)
