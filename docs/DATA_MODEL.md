# Data Model & Responsible Data Handling — CCSA

Single source of truth for **what data is stored, how, and under which rules**. This document defines the schema materialized later in each module's `models.py` and the first Alembic migration. It complements the high-level model in `ARCHITECTURE.md` Database and the decisions in `DECISIONS.md` (D4, D6).

Because CCSA handles financial data, this is treated as a **Red zone** artifact (`AI_RULES.md`): any change to entities, isolation, or classification must be reviewed line by line.

---

## 1. Data classification

Every stored field is classified. This drives logging, encryption, and what may appear in API responses or be sent to a third party (LLM).

| Level | Meaning | Examples |
|---|---|---|
| **Public** | No risk if exposed | `currency`, HTTP status |
| **Internal** | Operational, not personal | `id`, `created_at`, `transaction_count`, `cadence` |
| **PII** | Identifies a person | `email` |
| **Sensitive (financial)** | Financial detail of a person | `description`, `amount`, `merchant`, `estimated_savings`, aggregates |
| **Secret** | Never stored in readable form | `password` → only `password_hash` |

**Rule:** `Sensitive` and `PII` fields are never written to application logs, never included in error messages, and never returned to a user other than the owner.

---

## 2. Entities (field-by-field)

Types are PostgreSQL / SQLAlchemy targets. `PK` = primary key, `FK` = foreign key. `Sens.` = classification.

### `users` (module `auth`)

| Field | Type | Null | Sens. | Notes |
|---|---|---|---|---|
| `id` | UUID | no (PK) | Internal | Server-generated |
| `email` | VARCHAR(255) | no, unique | PII | Stored **lowercase**; normalized on register/login (D8) |
| `password_hash` | VARCHAR(255) | no | Secret | **bcrypt/argon2 only** — plaintext is never stored, returned, or logged |
| `created_at` | TIMESTAMP | no | Internal | Default `now()` |

### `statements` (module `statements`)

| Field | Type | Null | Sens. | Notes |
|---|---|---|---|---|
| `id` | UUID | no (PK) | Internal | |
| `user_id` | UUID | no (FK → `users.id`) | Internal | **Indexed**, `ON DELETE CASCADE` |
| `filename` | VARCHAR(255) | no | Internal | Original name only; **the raw file is not stored** (D4) |
| `currency` | VARCHAR(3) | no | Public | Default `USD`; single currency per statement |
| `transaction_count` | INTEGER | no | Internal | Derived at parse time |
| `uploaded_at` | TIMESTAMP | no | Internal | Default `now()` |
| `deleted_at` | TIMESTAMP | yes | Internal | **Indexed**. Soft-archive marker (D22): `NULL` = active/visible to the owner; a timestamp = archived (hidden from the client and its analyses, retained server-side, restorable). Distinct from permanent erasure |

### `transactions` (module `statements`)

| Field | Type | Null | Sens. | Notes |
|---|---|---|---|---|
| `id` | UUID | no (PK) | Internal | |
| `statement_id` | UUID | no (FK → `statements.id`) | Internal | **Indexed**, `ON DELETE CASCADE` |
| `date` | DATE | no | Sensitive | Transaction date |
| `description` | VARCHAR(512) | no | Sensitive | Bank text as ingested — trimmed/normalized only (see §5). **No `merchant` column**; canonical merchant is derived at analysis time (D7) |
| `amount` | NUMERIC(12,2) | no | Sensitive | Fixed precision — never `float` for money |
| `category` | VARCHAR(64) | yes | Internal | Filled by Layer 1 (rules) or Layer 2 (LLM); null before analysis. App-validated vocabulary (D9) |

### `analyses` (module `analysis`)

| Field | Type | Null | Sens. | Notes |
|---|---|---|---|---|
| `id` | UUID | no (PK) | Internal | |
| `statement_id` | UUID | no (FK → `statements.id`) | Internal | **Indexed**, `ON DELETE CASCADE` |
| `user_id` | UUID | no (FK → `users.id`) | Internal | Denormalized for fast per-user scoping; **indexed** |
| `ai_enabled` | BOOLEAN | no | Internal | `false` when Layer 2 failed or was disabled (D2) |
| `layer_used` | VARCHAR(16) | no | Internal | `rules` or `llm` — app-validated (D9), not a DB enum |
| `monthly_recurring_total` | NUMERIC(12,2) | no | Sensitive | |
| `estimated_savings` | NUMERIC(12,2) | no | Sensitive | |
| `created_at` | TIMESTAMP | no | Internal | Default `now()` |

### `detected_subscriptions` (module `analysis`)

| Field | Type | Null | Sens. | Notes |
|---|---|---|---|---|
| `id` | UUID | no (PK) | Internal | |
| `analysis_id` | UUID | no (FK → `analyses.id`) | Internal | **Indexed**, `ON DELETE CASCADE` |
| `merchant` | VARCHAR(255) | no | Sensitive | Canonical name derived from `transactions.description` during analysis (D7) |
| `amount` | NUMERIC(12,2) | no | Sensitive | |
| `cadence` | VARCHAR(32) | no | Internal | e.g. `monthly` — app-validated (D9) |
| `category` | VARCHAR(64) | yes | Internal | App-validated (D9) |

### `recommendations` (module `analysis`)

| Field | Type | Null | Sens. | Notes |
|---|---|---|---|---|
| `id` | UUID | no (PK) | Internal | |
| `analysis_id` | UUID | no (FK → `analyses.id`) | Internal | **Indexed**, `ON DELETE CASCADE` |
| `title` | VARCHAR(255) | no | Sensitive | May reference a merchant |
| `detail` | VARCHAR(1024) | no | Sensitive | Natural-language text; may include amounts/merchant |
| `estimated_saving` | NUMERIC(12,2) | no | Sensitive | `0.00` for `review_subscription` (surfaced, not counted) |
| `kind` | VARCHAR(32) | no | Internal | D21: `cancel_subscription` \| `review_subscription` \| `avoid_fee`. App-validated (D9). `server_default='cancel_subscription'` |

_No `detected_subscription_id` in MVP — link to a detected subscription lives in free text only. See §7 if structured traceability is needed later._

---

## 3. Relationships & lifecycle

```text
users (1) ──< statements (1) ──< transactions
                      └──< analyses (1) ──< detected_subscriptions
                                     └──< recommendations
```

- **Cascade deletes are enforced at the schema level** (`ON DELETE CASCADE`), not only in application code:
- Delete a `statement` → its `transactions` and `analyses` (and their children) are removed.
- Delete a `user` → all their statements/analyses cascade. This is the mechanism behind account deletion ("right to be forgotten").
- The **permanent** delete endpoint (`DELETE /api/statements/{id}/permanent`) relies on this cascade; see `API.md`.
- **Soft archive (D22).** The everyday dashboard "delete" (`DELETE /api/statements/{id}`) sets `statements.deleted_at` instead of removing rows. An archived statement — and every `Analysis` derived from it — is hidden from the owner (queries filter `deleted_at IS NULL`) but retained. It is reversible (`POST /api/statements/{id}/restore`). No child rows are touched; visibility is scoped through the parent statement.
- Re-running analysis on the same statement **does not replace** prior rows — each run appends a new `Analysis` (D10). "Current" result = latest by `created_at`.

---

## 4. Responsible data handling

### Purpose limitation
Stored data is used **only** to produce the owning user's analysis. It is **not shared, sold, or used to train external models**.

### Data minimization (D4)
- The uploaded CSV is parsed **in memory**; the raw file is never persisted.
- Only the fields above are stored — no card numbers, no account numbers, no balances beyond per-transaction amounts.

### Third-party (LLM) exposure — important
When **Layer 2 (LLM)** runs, `Sensitive` fields (`description`, `amount`) may be sent to the configured provider:
- With **Ollama (local)**, data stays on our infrastructure — preferred for sensitive input.
- With **OpenAI**, data leaves our infrastructure to a third party. This is a conscious trade-off, disable-able via `LLM_ENABLED=false` (falls back to Layer 1). Documented so it can be stated plainly in the demo.
- Only the minimum fields needed for categorization are sent — never `email`, `user_id`, or `password_hash`.

### Encryption
- **In transit:** TLS/HTTPS everywhere (see `DEPLOYMENT.md`).
- **At rest:** relies on the managed PostgreSQL provider's disk-level encryption (Railway/Render). No application-level column encryption in the MVP; if introduced, it is recorded in `DECISIONS.md` first.

### Retention & deletion
- No fixed retention window in the MVP: data lives while the user keeps it.
- **Two-tier deletion (D22).** The dashboard trash action is a **soft archive**: the statement (and its analyses) disappears from the client's view but is **retained** server-side (`deleted_at`), so it can be restored and so operational/analytical data is not lost by an accidental click. This is the default because it is reversible and low-risk.
- **Permanent deletion / right to be forgotten** stays available and is a true hard delete (`DELETE /api/statements/{id}/permanent`), cascading to transactions and analyses. Account deletion (future, Could Have) cascades the same way. Erasure is therefore **explicit and irreversible** — archiving never silently substitutes for it.
- **Responsible-data note (Red zone).** Retaining archived data is a deliberate trade-off against strict data minimization (D4). It is only acceptable if it is **disclosed** to the user (the archive UI/copy must not imply permanent erasure) and if a genuine erasure path exists — which is why the permanent delete above is kept. Any change here is reviewed line by line (`AI_RULES.md`).
- Post-MVP candidate (Could Have): configurable auto-purge of archived statements / analyses older than N months.

### Logging & error messages
- `Sensitive`/`PII`/`Secret` fields are never logged and never appear in error responses (`{"detail": "..."}` stays generic). Enforced per `ARCHITECTURE.md` Sensitive data security.

### Per-user isolation
- Every query on `statements` and `analysis` filters by `user_id`. A valid token for user A can never read user B's rows (returns `404`, not `403`, to avoid leaking existence).

---

## 5. Ingest normalization

Parsing is a pluggable pipeline in `modules/statements/ingest/` (D15). Supported input is a **delimited** transaction export; raw PDF/statement dumps are out of MVP.

**`transactions.description`** — to avoid storing noisy or oversized sensitive strings:
- Trim whitespace and collapse repeated spaces.
- Truncate to the column limit (512).
- No enrichment that adds new PII (e.g. no geolocation lookups).
- Faithful to the source (D7): no merchant canonicalization at ingest.

**`transactions.date`** — accepted formats: ISO (`YYYY-MM-DD`), numeric with auto-detected orientation (`DD/MM` vs `MM/DD`, voting across the column; overridable via `dayfirst`/`date_format`), and English/Spanish month names (`Sep 4 2023`, `4 de abril de 2026`). Stored as a normalized `DATE`.

**`transactions.amount`** — parsed as `Decimal` (never float, §2). Handles US (`1,234.56`) and EU/LatAm (`1.234,56`) notation (auto-detected or forced via `decimal_style`), sign conventions (`-`, `(…)`, leading `+`, trailing `-`), and currency symbols. Debit/credit column pairs are combined into a signed amount (debit negative, credit positive).

**Encoding** — decoded with UTF-8 first, falling back to Latin-1/CP1252 so non-UTF-8 exports do not fail. Parse errors never echo row content (`API.md`).

---

## 6. Creation, evolution & scaling

### Creation
The schema is created exclusively through **Alembic migrations** — never by hand, never against production directly (`ARCHITECTURE.md`, `implement-feature.md` Step 2).

### Evolution (modify)
- Each schema change = one reviewed migration; verify `downgrade()` truly reverses `upgrade()` before applying (Yellow zone, `AI_RULES.md`).
- Changes touching `Sensitive`/`PII` fields or isolation are Red zone → line-by-line review.

### Scaling (specific to CCSA, not generic)
- **Indexes** on every FK used for scoping/joins: `statements.user_id`, `transactions.statement_id`, `analyses.statement_id`, `analyses.user_id`, and `analysis_id` on both child tables.
- **Volume assumption:** tens–hundreds of transactions per statement → processed in memory, no streaming/async jobs needed (`REQUIREMENTS.md` 3).
- **Pagination** on `GET /api/statements` and `GET /api/analysis` as history grows (offset/limit). Not premature — added when list size warrants it.
- **Connection pooling** via SQLAlchemy engine defaults; tune pool size only if the deploy platform shows contention.
- Not in scope for the MVP: read replicas, sharding, caching layers (kept in `PROJECT_SCOPE.md` secondary list).

---

## 7. Open items to confirm before scaffolding

- [x] Confirm password hashing library (bcrypt vs argon2) → **bcrypt** (D13)
- [x] Confirm whether `analyses.user_id` denormalization stays or scoping goes through `statement.user_id` → **keep denormalized `user_id` on `analyses`** for fast per-user queries (see §2)
- [ ] Confirm account-deletion endpoint is in scope for the MVP or deferred (Could Have).
- [ ] **`recommendations` → `detected_subscriptions` link:** no FK today; the relationship lives in free text (`title`/`detail`). Sufficient for MVP (show + explain). Add optional `detected_subscription_id` if "mark as applied" or structured savings tracking is needed (Could Have).
- [ ] **Analysis history UI:** D10 keeps all runs; confirm whether the MVP shows only the latest analysis or a simple history picker (Could Have).

