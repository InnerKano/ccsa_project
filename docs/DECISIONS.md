# Engineering Decisions — Credit Card Savings Analyzer (CCSA)

This document captures key architectural and technical decisions. The first part lists default choices inherited from the starter kit; the second part contains CCSA-specific decisions that deviate from or extend those defaults.

## Technology Choices (starter kit defaults)

### FastAPI for Backend
**Decision**: Use FastAPI instead of Django or Flask

**Rationale**:
- Fast async support out of the box
- Excellent auto-generated API documentation
- Type hints reduce bugs
- Great for building APIs quickly
- Easy dependency injection

### Next.js for Frontend
**Decision**: Use Next.js instead of Create React App

**Rationale**:
- Built-in routing
- API routes capability
- Server-side rendering option
- Great developer experience
- Easy deployment to Vercel

### PostgreSQL for Database
**Decision**: Use PostgreSQL for relational data

**Rationale**:
- Industry standard
- Strong ACID guarantees
- Rich query language
- Good integration with Python/Node ecosystems
- Widely supported hosting

### Docker for Development
**Decision**: Use Docker Compose for local development

**Rationale**:
- Consistent environment across team
- Close to production environment
- Easy onboarding for new developers
- Service isolation
- Simple CI/CD integration

## Architectural Decisions

### Monorepo Structure
**Decision**: Keep frontend and backend in the same repository

**Rationale**: Easier to manage for small projects, coordinated deployments, shared documentation, and a single git history.

### JWT Authentication
**Decision**: Implement JWT-based authentication

**Rationale**: Stateless, works well with modern SPAs, no session storage, and simple to implement.

### RESTful API
**Decision**: Use REST instead of GraphQL

**Rationale**: Simpler to implement and understand, better HTTP caching, mature tooling, easier to test.

## Development Practices

### API-First Development
**Decision**: Define API contracts before implementation.

### Migrations as Code
**Decision**: Manage database schema with Alembic.

### Containerized Deployment
**Decision**: Deploy all services as containers.

---

## CCSA-specific decisions

These decisions extend or deviate from the defaults and directly answer questions from the challenge (scope, trade-offs, AI usage, risks).

### D1 — CSV input only (no PDF or Plaid for MVP)
**Decision**: The MVP accepts a CSV file uploaded by the user only.

**Alternatives considered**: Plaid (bank aggregator suggested by the brief), PDF parsing with OCR. The system should remain modular and extensible to accept other alternatives in a future implementation.

**Rationale**:
- Most banks allow exporting transactions to CSV → sufficient coverage without external dependencies.
- Plaid in production requires application, approval, and possible costs; the sandbox does not provide real user data.
- Bank PDFs vary too much in format to parse reliably within 72 hours.

**Consequence**: Plaid and PDF support are "Could Have" items (see `PROJECT_SCOPE.md`). Choosing CSV eliminates the project's largest technical risk.

### D2 — Two-layer analysis with graceful degradation
**Decision**: Layer 1 = rules-based detection (regex/keywords + recurrence). Layer 2 = optional LLM that enriches results with finer categorization and natural-language recommendations. If Layer 2 fails or is disabled, return Layer 1 results.

**Rationale**:
- Guarantees a deliverable MVP even if AI fails on demo day (rate limits, inconsistent prompts).
- Aligns with the strategy "solid base first, AI as layer 2".
- Provides demonstrable evidence in the deliverable of where AI helped and where it failed: the fallback is explicit.

### D3 — Provider-agnostic LLM via `.env`
**Decision**: The AI layer is behind a common interface (`LLMProvider`) with implementations for Ollama (local) and OpenAI, selectable via `LLM_PROVIDER`.

**Rationale**:
- Local development is free with Ollama; production/demo can use OpenAI without code changes.
- Avoids vendor lock-in and exposure to a single provider's costs/limits.
- Reuses a familiar pattern validated by the developer.

### D4 — Do not persist raw files; minimize sensitive data
**Decision**: Parse the CSV in memory and store only normalized transactions needed for analysis. Do not log transactions or statement content.

**Rationale**: As a FinTech-related project, security and privacy are explicit evaluation criteria. Minimizing stored data reduces the attack surface and compliance risk.

**Note (Red zone in `AI_RULES.md`)**: Any change that touches user isolation, authentication, or handling of financial data must be reviewed line by line.

### D5 — No automatic subscription cancellation
**Decision**: The "extra" feature (automatic cancellation) is out of scope. The product recommends and explains; the user executes cancellations.

**Rationale**: Automatic cancellations require merchant integrations, per-service OAuth, and legal/operational implications that are unrealistic to implement in 72 hours. This is documented as a "Won't Have" to answer the question confidently in the demo.

### D6 — Persist analysis history
**Decision**: Each analysis is saved and associated with the user's account and can be retrieved later.

**Rationale**: The brief asks for "results saved" and enabling month-to-month tracking adds value (foundation for the "Could Have" of temporal comparisons).

### D7 — Merchant normalization lives in the analysis layer
**Decision**: `transactions` stores the bank's raw `description` only. There is no `merchant` column on `transactions`. Canonical merchant names (e.g. `"NETFLIX.COM *SF"` → `"NETFLIX"`) are derived during analysis and stored on `detected_subscriptions.merchant`.

**Alternatives considered**: Persisting a normalized `merchant` on each transaction at ingest time.

**Rationale**:
- Ingest should stay faithful to the source CSV; canonicalization is an interpretation, not raw data.
- Merchant grouping logic belongs in the analysis pipeline (Layer 1 rules / Layer 2 LLM), not in the upload path.
- Avoids duplicating the same merchant string on every recurring row before analysis runs.

**Consequence**: Joining a recommendation back to its source transaction(s) goes through `detected_subscriptions`, not a direct field on `transactions`. See open item in `DATA_MODEL.md` §7 for structured recommendation → subscription links.

### D8 — Email stored lowercase (case-insensitive uniqueness)
**Decision**: Normalize `email` to lowercase on register and login before lookup/persist. Uniqueness is enforced on the stored lowercase value.

**Alternatives considered**: PostgreSQL `citext` type; case-sensitive unique constraint.

**Rationale**: Prevents duplicate accounts for `User@x.com` vs `user@x.com` — a common auth bug with minimal implementation cost (one `.lower()` in the auth service).

### D9 — Controlled vocabulary validated in application code, not DB enums
**Decision**: Fields such as `layer_used`, `cadence`, and `category` are `VARCHAR` columns without PostgreSQL `CHECK` constraints or native enums in the MVP. Allowed values are enforced in Pydantic schemas and service logic.

**Alternatives considered**: DB-level `CHECK` or `ENUM` types.

**Rationale**:
- Faster schema iteration under a 72-hour deadline (no migration per new category).
- Pydantic already validates at the API boundary; invalid values cannot enter through normal endpoints.
- Trade-off accepted: direct DB writes could bypass validation — acceptable in MVP with a single application writer.

### D10 — Re-analysis appends a new row (does not replace)
**Decision**: Calling `POST /api/analysis/{statement_id}` again on the same statement **creates a new `Analysis` row** with its own children. Previous analyses are retained.

**Alternatives considered**: Upsert / replace the latest analysis in place.

**Rationale**:
- Consistent with D6 (persisted history) and enables comparing rule-only vs LLM-enriched runs over time.
- The UI treats the **latest analysis by `created_at`** as the current result unless the user explicitly picks an older one from history (Could Have).

**Consequence**: Multiple analyses per statement are expected; list/detail endpoints should order by `created_at DESC` when showing "current" results.

### D11 — Dockerfiles colocated with services (no top-level `docker/` folder)
**Decision**: `docker-compose.yml` lives at the repo root; each service keeps its own `Dockerfile` in `backend/` and `frontend/`.

**Alternatives considered**: Central `docker/Dockerfile.backend` pattern from generic starter kits.

**Rationale**:
- Smaller context paths (`build: ./backend`) and less indirection under a 72-hour deadline.
- Volume mounts in Compose map cleanly to service directories.
- `ARCHITECTURE.md` project tree reflects what is actually on disk after Step 5 validation.

### D12 — Compose mounts the full monorepo in development
**Decision**: Local Compose mounts the repository root at `/workspace` with `working_dir` set to `/workspace/backend` (and `/workspace/frontend`). Not `./backend:/app` alone.

**Alternatives considered**: Backend-only mount with `pytest.skip` for monorepo structure tests; separate `tests/repository/` suite.

**Rationale**:
- CCSA is a monorepo; Docker is the official local runtime — it should see the same tree as the host.
- Avoids skipped tests and `REPO_ROOT = /` bugs inside containers.
- Alembic, pytest, and docs remain addressable consistently from `docker compose exec backend`.

### D13 — bcrypt for password hashing
**Decision**: Hash passwords with **bcrypt** (`bcrypt.hashpw` / `checkpw`). Plaintext passwords are never stored or logged.

**Alternatives considered**: argon2 (stronger, extra dependency/setup); passlib wrapper (unmaintained; incompatible with bcrypt 5.x).

**Rationale**:
- Closes `DATA_MODEL.md` open item; bcrypt is widely understood and sufficient for MVP.
- Direct `bcrypt` usage avoids passlib maintenance issues while keeping the API surface minimal in `core/security.py`.
- argon2 can replace bcrypt later with a migration + re-hash strategy if requirements change.

### D14 — Single-role model 
**Decision**: No admin/supervisor roles.

**Rationale**: single-consumer product per REQUIREMENTS §1, no organizational use case; user isolation via user_id scoping is sufficient. RBAC listed as secondary/optional in PROJECT_SCOPE, not required for this MVP.

### D15 — Supported input = delimited transaction export (not raw statement dumps)
**Decision**: The MVP ingests a **delimited** file (CSV/TSV) whose header row exposes a date, a description, and either an amount column or a debit/credit pair. Real inputs vary, so the parser handles: encoding fallbacks (UTF-8 / Latin-1), multiple date formats (ISO, DD/MM, MM/DD, English **and** Spanish month names), locale-aware amounts (US `1,234.56` and EU/LatAm `1.234,56`), several sign conventions (`-`, `(…)`, `+` prefix, currency symbols, debit/credit columns), delimiter sniffing, and a small header preamble. Column names are inferred from an EN+ES vocabulary or provided via explicit mapping.

**This refines** REQUIREMENTS §3's assumption "the user can export CSV". The realistic distinction: a **transaction export** (delimited, from online banking) is supported; a **statement PDF** — or a PDF exported to `.csv` as fixed-width, multi-line, page-noise text (see the real fixtures) — is **not** parsed in the MVP. Per REQUIREMENTS's own policy, that history is not rewritten there; this decision records the refinement.

**Alternatives considered**:
- Parse the raw PDF/statement dump now → rejected: fixed-width + multi-line + watermark noise + per-bank layout is effectively PDF extraction; high effort and brittle, contradicts D1 and Risk #3 (over-engineering), and jeopardizes the MVP.
- Keep the idealized single sample → rejected: not representative; demo would look like a toy.

**Design consequence (modularity)**: ingestion is a pluggable pipeline under `modules/statements/ingest/` — `base.py` (contracts), `normalizers.py`, `delimited.py`, `registry.py`. A future **PDF-dump parser** or **bank-specific profile** is added by implementing `StatementParser` and registering it in `registry.py`; `api.py` and the persistence path do not change. This is how D1's "remain modular and extensible" is honored concretely.

**Data-handling consequence**: real bank statements contain PII/financial data. Repo fixtures are **synthetic** (`sample.csv` US, `sample_es.csv` LatAm); `.gitignore` keeps `*.csv` out by default and only whitelists those two. Real exports must never be committed (`DATA_MODEL.md` §4, `AI_RULES.md` Red zone).

**Deferred to Could Have** (`PROJECT_SCOPE.md`): PDF/statement-dump parsing, per-bank format profiles, and multi-currency conversion (a `currency` per statement is stored but not converted, per REQUIREMENTS §5).

### D16 — Layer 1 detection & savings rules (rules-only MVP)
**Decision**: The A3 analysis pipeline (`modules/analysis/`) ships Layer 1 only. Its rule set is:
- **Recurrence** — a canonical merchant (D7) charged in **≥ 2 distinct months** with a **stable amount** (spread between min and max ≤ 25% of the median) is a `detected_subscription`; cadence is labelled `monthly` in the MVP. Inflows (`amount ≥ 0`, e.g. payroll) are never subscriptions.
- **Estimated savings** — Layer 1 has no usage signal, so it does **not** claim a subscription is unused. It recommends reviewing only **discretionary** categories (`streaming`, `music`, `gaming`, `software`, `fitness`); `estimated_savings` is their sum. Essential recurring charges (utilities, telecom, insurance, groceries, shopping…) are surfaced in `detected_subscriptions` but not recommended for cancellation. This is why `estimated_savings ≤ monthly_recurring_total`.
- **Transaction categorization** — running an analysis fills `transactions.category` (bilingual EN+ES keyword/merchant rules, D15), so a categorized statement is visible in `GET /api/statements/{id}`. Re-running (D10) re-applies the latest run's categories.

**Alternatives considered**:
- Treat every recurring charge as savings → rejected: overstates savings and recommends cancelling essentials.
- Infer "unused" from cadence gaps → rejected: not enough signal in a single statement; belongs to Layer 2 / month-over-month (Could Have).

**Rationale**: keeps Layer 1 honest and explainable (Yellow zone, `AI_RULES.md`) and guarantees value with no AI (`REQUIREMENTS.md` §6). The bilingual vocabulary lives as data in `rules/vocabulary.py`, separate from the algorithm in `rules/engine.py`, so it can grow without touching detection logic.

**Design consequence (Layer 2 seam)**: `analysis/services.py` runs `rules.engine.run_layer_one` and marks results `ai_enabled=false`, `layer_used="rules"`. A future Layer 2 wraps that result and only upgrades those flags on success — never removing the Layer 1 guarantee (D2). No LLM code is introduced now (the seam is a comment + structure, not an abstraction — per `implement-feature.md`, introduce the seam when the second variant lands).

### D17 — Analyzer realism pass on real statements (delimited hardening + single-statement subscription signals)
**Decision (dev branch)**: After analyzing real US bank/card statements collected in `backend/fixtures/real_samples/` (Capital One card + 360, Discover, Bank of America), refine Layer 1 **without changing the schema, API, or the D15 ingestion contract**:
- **Merchant-noise stripping** — `canonical_merchant` now drops transaction plumbing tokens (`CHECKCARD`, `PMNT`, `SENT`, `SQ`, `TST`, `DES`, `ID`, `INDN`, `CO`, …) and any token containing a digit (store #s, reference IDs, city/state-glued codes) before deriving the canonical name, so the same real-world merchant is not split into several groups. Noise tokens live as data in `rules/vocabulary.py` (`MERCHANT_NOISE_TOKENS`).
- **Expanded bilingual vocabulary** — `MERCHANT_ALIASES` / `CATEGORY_KEYWORDS` now cover the common US merchants seen in the samples (HULU, MINT MOBILE, SPECTRUM, CRUNCH FITNESS, CHIPOTLE, EXXON, CHEVRON, GEICO, STATE FARM, TARGET, BEST BUY, TRADER JOE'S, WHOLEFDS, …) so categorization is not mostly `other` on realistic data.
- **Single-statement subscription signals** — a lone upload is one month, so the strong ≥2-month recurrence rule (D16) alone finds nothing. Two extra signals now apply: (a) an explicit **bank recurring marker** on the line (e.g. Bank of America prints `RECURRING`) → cadence `monthly`; (b) a **known subscription service** (`KNOWN_SUBSCRIPTIONS`, e.g. NETFLIX, MINT MOBILE) seen even once → cadence **`suspected`**. The strong multi-month path is unchanged and still labelled `monthly`.

**Alternatives considered**:
- Treat any known-merchant single charge as `monthly` → rejected: dishonest, one occurrence is not proof of cadence. Hence the distinct `suspected` cadence.
- Wait for month-over-month history before detecting anything → rejected: makes a single real upload produce empty results, which the demo needs to avoid.

**Rationale**: keeps Layer 1 honest and explainable (Yellow zone, `AI_RULES.md`) while making the analyzer actually useful on a *single real statement*. All new coverage is **data** in `rules/vocabulary.py`; `rules/engine.py` gained only the two extra signals. `savings` stays discretionary-only (D16), so `estimated_savings ≤ monthly_recurring_total` still holds.

**Scope boundary (unchanged for D17)**: D17 was a realism pass on Layer 1 analysis. PDF ingestion landed separately in **D18**.

### D18 — PDF statement ingestion adapter (shared column mapping)
**Decision (dev branch)**: Add a second `StatementParser` for bank/card statement PDFs, registered before the delimited parser in `ingest/registry.py`. The design goal: **detect date, description, and amount columns regardless of whether the source is CSV or PDF** — format-specific code only *extracts rows*; `ingest/columns.py` maps columns and normalizes fields (same path as D15 delimited exports).

**Architecture**:
```text
ingest/
├── columns.py          # shared: header vocabulary, ColumnPlan, parse_tabular_rows
├── delimited.py        # CSV/TSV → rows → columns.py
├── pdf/
│   ├── extract.py      # pdfplumber table + page text
│   ├── lines.py        # line-oriented fallback + bank row profiles (CapOne, BoA, Discover)
│   └── parser.py       # PdfStatementParser — picks best extraction strategy
└── registry.py         # PdfStatementParser first, then DelimitedStatementParser
```

**PDF pipeline**:
1. Extract table rows (pdfplumber) and/or line-oriented rows (page text scan with section-aware sign normalization).
2. Score each candidate by how many valid transactions `columns.parse_tabular_rows` produces (`skip_invalid_rows=True` for PDF noise).
3. Deduplicate bilingual/repeated pages (Capital One ES+EN).
4. Fail cleanly when no transactions are found (e.g. Capital One 360 summary-only statements).

**Dependency**: `pdfplumber` (PyPI, maintained) — justified because text-only PDF extraction is insufficient for column-collapsed layouts; table extraction requires a PDF layout library (D18, Yellow zone — verified before adding).

**Alternatives considered**:
- OCR for scanned PDFs → deferred (Won't Have in `PROJECT_SCOPE.md`; these samples are text-based).
- One regex parser per bank in a monolith → rejected: profiles live in `pdf/lines.py` today; a future `pdf/profiles/<bank>.py` registry is the extension point when a fourth layout appears.
- LLM PDF→JSON as primary path → deferred to Layer 2 seam (D2/D3); rules-first ingestion stays deterministic.

**Validated against** (local only, git-ignored): Capital One Savor card, Discover It, Bank of America checking, Capital One 360 (correctly rejected). Real samples never committed (`real_samples/`, `*.pdf` in `.gitignore`).

**API/frontend**: `POST /api/statements` and upload UI accept `.pdf`; advanced column mapping applies to both CSV and PDF.

### D19 — Per-bank PDF row profiles (`pdf/profiles/`) + Capital One 360 & PNC support
**Decision (dev branch)**: Realize the extension point D18 anticipated. The line-oriented PDF parser is refactored from a single `pdf/lines.py` scan into a **profile registry** (`pdf/profiles/`), and two new layouts are supported: **Capital One 360 checking/savings** and **PNC Virtual Wallet**. `api.py`, persistence, and the shared column mapper (`columns.py`) are unchanged.

**Why these two failed before** (confirmed by running the parser, not by inspection):
- **Capital One 360 checking** — transaction lines carry a *single* `Mon Day` date, a `Debit`/`Credit` marker, the amount, and a trailing **running-balance** column (`Jun 1 Withdrawal from … Debit - $127.00 $1,916.72`). None of the four D18 profiles matched: the card profile needs *two* dates; the generic "loose" profile grabbed the last `$` (the balance) and rejected the bare `Jun` date token. Table extraction shattered the columns. Some long descriptions wrap across lines.
- **PNC Virtual Wallet** — columns are `Date, Amount, Description` (amount **before** description), amounts carry **no sign or `$`** (the sign is implied by the section: additions positive; withdrawals/purchases/electronic deductions negative), dates are `MM/DD` with the year only in the period banner, and a `Daily Balance Detail` table of `date balance` pairs must be excluded. No profile matched and there were no ruled tables.

**Architecture**:
```text
ingest/pdf/
├── extract.py          # unchanged: pdfplumber tables + page text
├── lines.py            # thin orchestrator: infer year → registry → rows_to_table
└── profiles/
    ├── base.py             # RowProfile contract, LineRow, MONTH, rows_to_table
    ├── generic.py          # existing Capital One card / BoA / Discover / loose scan
    ├── capital_one_360.py  # NEW — single date + Debit/Credit + balance column
    ├── pnc.py              # NEW — section-driven sign, date/amount/desc order
    └── registry.py         # PNC, Capital One 360, then Generic (fallback)
```
A profile that recognizes a document but extracts nothing (e.g. a summary-only 360 statement) falls through to the next profile, preserving D18's "fail cleanly, never invent rows" guarantee.

**Two correctness rules discovered on the real samples**:
- **De-duplication is per-profile, not global.** The D18 exact-row dedupe existed to collapse Capital One card's bilingual (ES+EN) reprints. PNC legitimately prints the *same* small charge several times a day (e.g. four `$2.15` vending purchases), so global dedupe silently dropped real transactions. Dedupe is now a profile opt-in (`dedupe = True` only for the generic/card profile); PNC and 360 keep every row. Verified against PNC's own totals: 5 deposits = \$2,288.99, 19 card purchases = \$312.73, 3 electronic deductions = \$2,014.84 — all exact.
- **PNC descriptions are not line-joined.** PNC's two-column layout interleaves left-column summary sentences (`"…Machine/Debit Card deductions…"`) between transaction rows, so attaching wrapped fragments is unreliable. Only the primary `MM/DD amount description` line is kept; trailing reference codes (`690387`, `Bevera`) are dropped. The primary description still names the merchant (NETFLIX, AMAZON, CTLP\*MILL CREEK…), which is all the analysis layer canonicalizes (D17).

**Alternatives considered**:
- Add two more functions inside `pdf/lines.py` → rejected: D18 already flagged `pdf/profiles/` as the seam "when a fourth layout appears"; we are at layouts #5–#6.
- Keep global dedupe and special-case PNC → rejected: silently wrong on any statement with genuine repeats; per-profile opt-in is the honest fix.
- Reconstruct wrapped PNC descriptions via column geometry → rejected: over-engineering (Risk #3) for no analytical gain; the merchant is already in the primary line.

**Data-handling consequence**: the two new fixtures contain **real PII** (names, addresses, account numbers). They were moved out of `backend/fixtures/no support now/` into `backend/fixtures/real_samples/` (git-ignored via `*.pdf` + `real_samples/`, D15/D4, `AI_RULES.md` Red zone). Committed tests use **synthetic, PII-free** page text (`test_pdf_profiles.py`); real files are exercised only by `skipif` integration tests when present locally.

**Validated** (local only, git-ignored): Capital One 360 *checking* (46 transactions, wrapped rows merged, Opening/Closing/Interest-Rate lines excluded) and PNC Virtual Wallet (27 transactions, totals match the statement exactly). The four D18 layouts and the summary-only 360 "fails cleanly" test are unchanged. Full suite: 97 tests green.

### D20 — Transaction-type categorization (`transfer`/`cash`/`fees`) + canonical-merchant hardening
**Decision (dev branch)**: The analysis layer (`analysis/rules/`) now categorizes by the **stable structural part** of a description — the transaction *type* — not only by known merchants. This is a data-only extension of the D9/D17 vocabulary plus a bug fix in `canonical_merchant`; the engine algorithm and DB schema are unchanged.

**Why** (confirmed by running Layer 1 on the two real D19 statements, not by inspection):
- On Capital One 360, **40/46** rows were `other`; on PNC, **21/27**. The vocabulary was **merchant-centric**, but these statements are dominated by rows that have *no merchant to identify*: Zelle/`Zel` transfers, internal fund/savings transfers (`Withdrawal to Fondo de Emergencia`), card/bill payments (`… MOBILE PMT`), ATM cash, interest paid, and bank fees (`IClub Fees`). Partly a **language** gap too (bilingual ES: `Deposit from Sueldo`, `Fondo de …`).
- `canonical_merchant` kept transaction-structure words that are not part of a merchant name (`FROM`, `TO`, `ZELLE`, `CARD`, `DEBIT`, ES articles `DE`/`LA`…), producing garbage/merged canonical names like `TO FONDO DE` (which **collapsed distinct funds** — Emergencia/Deseos/Educacion — into one group and would corrupt future multi-month recurrence) and `DEBIT CARD CTLP`.

**What changed** (all in `analysis/rules/vocabulary.py`, engine untouched):
- New controlled categories `transfer`, `cash`, `fees` (income already existed) + bilingual `CATEGORY_KEYWORDS` rules for them, placed **before** merchant keywords so structural cues win (e.g. `ATM Withdrawal - CVS STORE` → `cash`, not `shopping`). Interest and `Sueldo` added to `income`.
- Extended `MERCHANT_NOISE_TOKENS` with structural/ES-article tokens so canonical names group and label correctly.
- Added `GOOGLE ONE` as a known subscription (a real recurring charge on the 360 that was being missed).

**Principle**: *categorize without necessarily identifying the specific merchant.* Merchant-specific vocabulary (e.g. PNC's `Ctlp*Mill Creek` vending, `Affirm`) is intentionally left to grow later; those rows stay `other` rather than being guessed.

**Honesty invariants kept (D16/D17)**: no new subscription heuristics — a single statement is still one month, so nothing is invented; the intra-month "repeated small charge" signal was **explicitly rejected** (a vending repeat is not a subscription). `GOOGLE ONE` is surfaced as `suspected`, not `monthly`. Savings stays discretionary-only, so `estimated_savings ≤ monthly_recurring_total` still holds.

**Result** (local, git-ignored): 360 `other` 40 → 10, PNC `other` 21 → 16, both with clean canonical names and no over-detection. Added `test_rules.py` cases (bilingual type categorization, structural-token stripping, Google One suspected). Full suite: 100 tests green.