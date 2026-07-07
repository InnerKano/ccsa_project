"""Bilingual (EN + ES) rule data for Layer 1 analysis.

This is deliberately *data*, separate from the logic in ``engine.py``, so the
vocabulary can grow (more merchants, more keywords) without touching the
detection algorithm. Ingestion accepts EN + ES exports (D15), so categorization
must recognize both languages (see middle-phases.md, A3).

The merchant/keyword coverage was expanded (D17) after analyzing real US bank
and card statements in ``backend/fixtures/real_samples/`` (Capital One, Discover,
Bank of America). It now recognizes the common US merchants those statements
contain so categorization is not mostly ``other`` on realistic data.

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
        # Transaction-type categories (D20): classify by the stable structural
        # part of the description (transfers, cash, fees) even when the specific
        # merchant is unknown. This keeps most rows off "other" without guessing.
        "transfer",
        "cash",
        "fees",
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
# before "UBER", "AMAZON PRIME" before "AMAZON", "XBOX GAME PASS" before "XBOX").
MERCHANT_ALIASES: tuple[tuple[str, str, str], ...] = (
    # --- streaming ---
    ("NETFLIX", "NETFLIX", "streaming"),
    ("DISNEY", "DISNEY+", "streaming"),
    ("HBO", "HBO MAX", "streaming"),
    ("PARAMOUNT", "PARAMOUNT+", "streaming"),
    ("HULU", "HULU", "streaming"),
    ("YOUTUBE PREMIUM", "YOUTUBE PREMIUM", "streaming"),
    ("YOUTUBE", "YOUTUBE", "streaming"),
    ("PRIME VIDEO", "AMAZON PRIME", "streaming"),
    # --- music ---
    ("SPOTIFY", "SPOTIFY", "music"),
    ("APPLE MUSIC", "APPLE MUSIC", "music"),
    ("DEEZER", "DEEZER", "music"),
    # --- gaming ---
    ("XBOX GAME PASS", "XBOX GAME PASS", "gaming"),
    ("XBOX", "XBOX", "gaming"),
    ("PLAYSTATION", "PLAYSTATION", "gaming"),
    ("NINTENDO", "NINTENDO", "gaming"),
    # --- software / SaaS ---
    ("AMAZON PRIME", "AMAZON PRIME", "shopping"),
    ("ADOBE", "ADOBE", "software"),
    ("OFFICE 365", "MICROSOFT 365", "software"),
    ("MICROSOFT", "MICROSOFT", "software"),
    ("QUICKBOOKS", "QUICKBOOKS", "software"),
    ("IDENTITYGUARD", "IDENTITY GUARD", "software"),
    ("GODADDY", "GODADDY", "software"),
    ("DROPBOX", "DROPBOX", "software"),
    ("ICLOUD", "APPLE ICLOUD", "software"),
    ("GOOGLE ONE", "GOOGLE ONE", "software"),  # storage subscription (before bare GOOGLE)
    ("GOOGLE", "GOOGLE", "software"),
    ("APPLE", "APPLE", "software"),
    # --- fitness ---
    ("PLANET FITNESS", "PLANET FITNESS", "fitness"),
    ("LA FITNESS", "LA FITNESS", "fitness"),
    ("24 HOUR FITNESS", "24 HOUR FITNESS", "fitness"),
    ("CRUNCH FITNES", "CRUNCH FITNESS", "fitness"),
    ("SMARTFIT", "SMART FIT", "fitness"),
    ("SMART FIT", "SMART FIT", "fitness"),
    ("BODYTECH", "BODYTECH", "fitness"),
    # --- telecom ---
    ("MINT MOBILE", "MINT MOBILE", "telecom"),
    ("SPECTRUM", "SPECTRUM", "telecom"),
    ("XFINITY", "XFINITY", "telecom"),
    ("COMCAST", "COMCAST", "telecom"),
    ("T-MOBILE", "T-MOBILE", "telecom"),
    # --- food delivery / transport ---
    ("UBER EATS", "UBER EATS", "food"),
    ("RAPPI", "RAPPI", "food"),
    ("UBER", "UBER", "transport"),
    ("DIDI", "DIDI", "transport"),
    # --- shopping / retail memberships ---
    ("FABLETICS", "FABLETICS", "shopping"),
    # --- grocery delivery membership ---
    ("INSTACART", "INSTACART", "groceries"),
)

# Canonical merchant names (as produced via MERCHANT_ALIASES) that are inherently
# subscription/membership services. Used by the engine to flag a *single-statement*
# occurrence as a suspected subscription even without the ≥2-month evidence the
# strong recurrence rule requires (D17). Kept honest: these are marked with a
# ``suspected`` cadence, not ``monthly`` (see engine.py / DECISIONS.md D17).
KNOWN_SUBSCRIPTIONS: frozenset[str] = frozenset(
    {
        "NETFLIX",
        "SPOTIFY",
        "DISNEY+",
        "HBO MAX",
        "PARAMOUNT+",
        "HULU",
        "YOUTUBE PREMIUM",
        "APPLE MUSIC",
        "DEEZER",
        "AMAZON PRIME",
        "ADOBE",
        "MICROSOFT 365",
        "QUICKBOOKS",
        "IDENTITY GUARD",
        "DROPBOX",
        "APPLE ICLOUD",
        "GOOGLE ONE",
        "XBOX GAME PASS",
        "PLAYSTATION",
        "NINTENDO",
        "PLANET FITNESS",
        "LA FITNESS",
        "24 HOUR FITNESS",
        "CRUNCH FITNESS",
        "SMART FIT",
        "BODYTECH",
        "MINT MOBILE",
        "SPECTRUM",
        "FABLETICS",
        "INSTACART",
    }
)

# Explicit "this is a recurring charge" markers some banks print on the line
# itself (e.g. Bank of America appends "RECURRING"). A high-confidence signal
# that a charge is a subscription even from a single statement (D17). Matched as
# a substring against the upper-cased description.
RECURRING_MARKERS: tuple[str, ...] = (
    "RECURRING",
    "RECURRENTE",
    "SUBSCRIPTION",
    "SUSCRIPCION",
    "SUSCRIPCIÓN",
)

# Human-readable labels for the different avoidable bank/card fees (D21). Used to
# group `fees` transactions into one recommendation per fee type ("You paid $X in
# overdraft fees") instead of one per raw description. Scanned in order — put the
# more specific substrings first (e.g. "ATM FEE" before the generic fallback).
# Matched as a substring against the upper-cased description. The keys mirror the
# fee cues already in CATEGORY_KEYWORDS below, so any charge categorized as `fees`
# resolves to a label here.
FEE_LABELS: tuple[tuple[str, str], ...] = (
    ("WIRE TRANSFER FEE", "wire transfer fees"),
    ("WIRE FEE", "wire transfer fees"),
    ("OVERDRAFT FEE", "overdraft fees"),
    ("SOBREGIRO", "overdraft fees"),
    ("NSF FEE", "NSF/returned-item fees"),
    ("INSUFFICIENT FUNDS", "NSF/returned-item fees"),
    ("RETURNED ITEM", "NSF/returned-item fees"),
    ("LATE FEE", "late-payment fees"),
    ("ATM FEE", "ATM fees"),
    ("FOREIGN TRANSACTION FEE", "foreign transaction fees"),
    ("CASH ADVANCE FEE", "cash advance fees"),
    ("STOP PAYMENT", "stop-payment fees"),
    ("ANNUAL FEE", "annual card fees"),
    ("MAINTENANCE FEE", "account maintenance fees"),
    ("MONTHLY FEE", "monthly account fees"),
    ("MEMBERSHIP FEE", "membership fees"),
    ("SERVICE FEE", "service fees"),
    ("SVC FEE", "service fees"),
    ("SERVICEFEE", "service fees"),
    ("CLUB FEES", "membership/club fees"),
)

# High-confidence fee cues scanned before transfer/cash keywords (D21.1).
# Real BOA lines use abbreviations ("SVC FEE", "SERVICEFEE") and compound names
# ("Wire Transfer Fee") that lose to "WIRE TRANSFER" → transfer without this pass.
# Order matters — more specific phrases first. Bare "OVERDRAFT" is omitted so
# "OVERDRAFT PROTECTION FROM …" (an inflow) is not mis-tagged. The engine also
# accepts a trailing FEE/FEES token via regex (e.g. "M&T Bank … WITHDRWL … FEE").
FEE_DESCRIPTION_KEYWORDS: tuple[str, ...] = tuple(keyword for keyword, _ in FEE_LABELS)

# Fallback when a charge is categorized as `fees` but matches no specific label.
DEFAULT_FEE_LABEL = "bank fees"

# Bank/processor boilerplate tokens that pollute merchant canonicalization on
# real statements (e.g. "CHECKCARD 0524 GO CLEANERS ...", "PMNT SENT ...",
# "SQ *COLDSTONE"). Dropped before deriving a canonical merchant name (D17).
# Kept conservative — only tokens that are clearly transaction plumbing, not
# part of a merchant name.
MERCHANT_NOISE_TOKENS: frozenset[str] = frozenset(
    {
        "CHECKCARD",
        "PURCHASE",
        "POS",
        "PMNT",
        "PYMT",
        "SENT",
        "RCVD",
        "ACH",
        "WITHDRWL",
        "WITHDRAWAL",
        "DEPOSIT",
        "DES",
        "ID",
        "INDN",
        "CO",
        "WEB",
        "PPD",
        "TEL",
        "REF",
        "CONF",
        "RECURRING",
        "SQ",
        "TST",
        "SP",
        "DNH",
        "INT",
        "WF",
        "ABC",
        "IN",
        # Transaction-structure words that are not part of a merchant name (D20).
        # Removing them stops garbage/merged canonical names like "FROM CAPITAL
        # ONE", "TO FONDO DE", "DEBIT CARD CTLP", "ZELLE MONEY TO".
        "FROM",
        "TO",
        "ZELLE",
        "ZEL",
        "MONEY",
        "CARD",
        "DEBIT",
        "CREDIT",
        "MOBILE",
        "ONLINE",
        "PMT",
        "PMTS",
        "PAYMENT",
        "PAYMENTS",
        "TRANSFER",
        "ATM",
        "RECEIVED",
        # Spanish articles / prepositions (e.g. "Fondo de Emergencia").
        "DE",
        "DEL",
        "LA",
        "EL",
        "PARA",
        "POR",
    }
)

# Generic keyword → category, bilingual. Used when no known merchant matched.
# Scanned in order; first hit wins.
CATEGORY_KEYWORDS: tuple[tuple[str, str], ...] = (
    # income (also excluded from subscription detection via sign in engine)
    ("PAYROLL", "income"),
    ("SALARY", "income"),
    ("DIR DEP", "income"),
    ("DIRECT DEP", "income"),
    ("NOMINA", "income"),
    ("NÓMINA", "income"),
    ("SALARIO", "income"),
    ("SUELDO", "income"),
    ("INTEREST PAID", "income"),
    ("INTEREST EARNED", "income"),
    ("MONTHLY INTEREST", "income"),
    ("INTERÉS", "income"),
    ("INTERES", "income"),
    ("DIVIDEND", "income"),
    # transaction-type: transfers (Zelle / wires / internal fund & card payments),
    # bilingual (D20). Placed before merchant keywords so structural cues win.
    ("ZELLE", "transfer"),
    ("ZEL FROM", "transfer"),
    ("ZEL TO", "transfer"),
    ("WIRE TRANSFER", "transfer"),
    ("TRANSFERENCIA", "transfer"),
    ("REMITLY", "transfer"),
    ("REMITTANCE", "transfer"),
    ("REMESA", "transfer"),
    ("FONDO", "transfer"),
    ("INVERSIÓN", "transfer"),
    ("INVERSION", "transfer"),
    ("AHORRO", "transfer"),
    ("MOBILE PMT", "transfer"),
    ("ONLINE PMT", "transfer"),
    ("WEB PMT", "transfer"),
    ("MOBILE PAYMENT", "transfer"),
    ("OVERDRAFT PROTECTION", "transfer"),  # inflow from linked account — not a fee (D21.1)
    # transaction-type: bank fees — also detected via FEE_DESCRIPTION_KEYWORDS in
    # engine._is_fee() before this list runs; kept here as fallback for categorize().
    ("WIRE TRANSFER FEE", "fees"),
    ("OVERDRAFT FEE", "fees"),
    ("SOBREGIRO", "fees"),
    ("SERVICE FEE", "fees"),
    ("SVC FEE", "fees"),
    ("SERVICEFEE", "fees"),
    ("MONTHLY FEE", "fees"),
    ("MAINTENANCE FEE", "fees"),
    ("ANNUAL FEE", "fees"),
    ("LATE FEE", "fees"),
    ("ATM FEE", "fees"),
    ("CLUB FEES", "fees"),
    ("FEES", "fees"),
    ("COMISIÓN", "fees"),
    ("COMISION", "fees"),
    # transaction-type: cash withdrawals
    ("ATM", "cash"),
    ("CAJERO", "cash"),
    ("CASH WITHDRAWAL", "cash"),
    ("EFECTIVO", "cash"),
    # groceries
    ("WHOLE FOODS", "groceries"),
    ("WHOLEFDS", "groceries"),
    ("TRADER JOE", "groceries"),
    ("SAFEWAY", "groceries"),
    ("ALDI", "groceries"),
    ("VONS", "groceries"),
    ("PUBLIX", "groceries"),
    ("KROGER", "groceries"),
    ("SUPERMARKET", "groceries"),
    ("SUPERMERCADO", "groceries"),
    ("GROCERY", "groceries"),
    ("MARKET", "groceries"),
    ("EXITO", "groceries"),
    ("WAL-MART", "groceries"),
    ("WALMART", "groceries"),
    ("CARREFOUR", "groceries"),
    ("TIENDA", "groceries"),
    ("D1", "groceries"),
    # fuel
    ("EXXON", "fuel"),
    ("CHEVRON", "fuel"),
    ("SUNOCO", "fuel"),
    ("SPEEDWAY", "fuel"),
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
    ("CHIPOTLE", "food"),
    ("SUBWAY", "food"),
    ("BURGER KING", "food"),
    ("EL POLLO LOCO", "food"),
    ("BLAZE PIZZA", "food"),
    ("PANERA", "food"),
    ("WAFFLE HOUSE", "food"),
    ("DUNKIN", "food"),
    ("STARBUCKS", "food"),
    ("MCDONALD", "food"),
    ("COFFEE", "food"),
    ("CAFE", "food"),
    ("CAFÉ", "food"),
    ("COMIDA", "food"),
    # transport
    ("LYFT", "transport"),
    ("TAXI", "transport"),
    ("METRO", "transport"),
    ("PARKING", "transport"),
    # utilities
    ("PACIFIC GAS", "utilities"),
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
    ("GEICO", "insurance"),
    ("STATE FARM", "insurance"),
    ("LIBERTY MUTUAL", "insurance"),
    ("PROGRESSIVE", "insurance"),
    ("ALLSTATE", "insurance"),
    ("INSURANCE", "insurance"),
    ("SEGURO", "insurance"),
    # shopping
    ("AMAZON", "shopping"),
    ("TARGET", "shopping"),
    ("BEST BUY", "shopping"),
    ("HOME DEPOT", "shopping"),
    ("WAYFAIR", "shopping"),
    ("SHEIN", "shopping"),
    ("ROSS", "shopping"),
    ("MACY", "shopping"),
    ("MERCADOLIBRE", "shopping"),
    ("MERCADO LIBRE", "shopping"),
    ("STORE", "shopping"),
)
