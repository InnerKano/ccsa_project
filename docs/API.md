# API Reference — Credit Card Savings Analyzer (CCSA)

## Base URL

Development: `http://localhost:8000`
Production: defined in `docs/DEPLOYMENT.md`

## Response format

**Fixed rule: no envelope.** Endpoints return the resource directly — not wrapped in `data`/`message`/`status`. This is the FastAPI/Pydantic default and avoids unnecessary boilerplate.

Success:
```json
{
  "id": "uuid",
  "filename": "statement_march.csv",
  "uploaded_at": "2026-07-04T00:00:00Z"
}
```

Lists: direct array, not `{"data": [...]}`.

The HTTP status code already communicates state — `status` is not repeated inside the body.

**Monetary / decimal fields are serialized as JSON strings** (e.g. `"15.49"`, `"41.47"`), not floats. Amounts are `Decimal` end-to-end (`NUMERIC(12,2)`, never `float` — `DATA_MODEL.md` §2); serializing as strings preserves exact precision. Clients parse them as decimals. The numeric examples below are illustrative of the value, not the JSON type.

## Errors

Single format (FastAPI `HTTPException` default):
```json
{ "detail": "Error message" }
```

For validation errors (422), FastAPI returns field-level detail automatically. **Error messages never include transaction or statement content** (sensitive data).

## Authentication

JWT in the header:
```
Authorization: Bearer <token>
```

All `statements` and `analysis` endpoints require authentication and operate **only on resources owned by the token holder**.

## CORS

Browser requests from the Next.js app require an explicit allow-list. The backend reads `CORS_ORIGINS` (comma-separated) from the environment — default in development: `http://localhost:3000`.

| Setting | Development | Production |
|---|---|---|
| `CORS_ORIGINS` | `http://localhost:3000` | Frontend deploy URL (e.g. `https://your-project.vercel.app`) |
| Wildcard `*` | **Never** | **Never** |

`allow_credentials` is enabled because the frontend sends the JWT via the `Authorization` header on cross-origin requests. Preflight (`OPTIONS`) is handled by FastAPI's `CORSMiddleware`.

Shipped in **A4.1** (`core/config.py`, `main.py`). For deploy, set `CORS_ORIGINS` on the backend platform — see `DEPLOYMENT.md`.

## Status codes used

- `200 OK` — successful read or update
- `201 Created` — resource created
- `204 No Content` — successful deletion
- `400 Bad Request` — invalid input (business rule, e.g. malformed CSV)
- `401 Unauthorized` — missing or invalid token
- `403 Forbidden` — valid token, no permission on the resource
- `404 Not Found` — resource does not exist
- `422 Unprocessable Entity` — schema validation failure (FastAPI automatic)
- `500 Internal Server Error` — unhandled error

---

## Endpoints

### Health

#### GET /health
Verifies the backend is running. No authentication required.

**Response**: `200 OK`
```json
{ "status": "healthy" }
```

---

### Auth

Register / login are the fixed kit base; password recovery (D23) and the strength policy (D24) are CCSA additions.

#### POST /api/auth/register
Passwords are validated against the strength policy (D24): min 8 / max 128 chars, not a common/blocklisted password, and must not contain the email local-part. Violations return `422` (schema validation).

**Request**:
```json
{ "email": "user@example.com", "password": "a strong passphrase" }
```
**Response**: `201 Created`
```json
{ "id": "uuid", "email": "user@example.com", "token": "jwt_token" }
```

#### POST /api/auth/login
**Request**:
```json
{ "email": "user@example.com", "password": "a strong passphrase" }
```
**Response**: `200 OK`
```json
{ "token": "jwt_token" }
```

#### POST /api/auth/forgot-password
Starts password recovery (D23). If an account exists for the email, a reset link (`${FRONTEND_URL}/reset-password?token=...`) is emailed. The token is a short-lived JWT bound to the user's current password hash (single-use, self-invalidating; no DB row). **The response is identical whether or not the email exists** — no account enumeration. In development (`EMAIL_ENABLED=false`) the link is logged to the backend console instead of sent.

**Request**:
```json
{ "email": "user@example.com" }
```
**Response**: `200 OK` (always, for any well-formed email)
```json
{ "message": "If an account exists for that email, a password reset link has been sent." }
```

#### POST /api/auth/reset-password
Consumes a reset token and sets a new password (validated by the D24 policy). The token is single-use by construction — succeeding invalidates it and any other outstanding token for the user. Does **not** log the user in (force re-login, D23).

**Request**:
```json
{ "token": "reset_jwt", "password": "a new strong passphrase" }
```
**Response**: `200 OK`
```json
{ "message": "Your password has been reset. You can now sign in." }
```
Errors: `400 { "detail": "Invalid or expired reset link" }` for a malformed, expired, tampered, or already-used token (the cause is never distinguished). `422` if the new password fails the strength policy.

---

### Statements (statement upload and parsing)

#### POST /api/statements
Uploads a **delimited export** (CSV/TSV/TXT) or a **bank/card statement PDF** (`.pdf`). Parsed in memory; **the raw file is not stored**, only normalized transactions. Both paths map the same three fields — **date, description, amount** — via shared column detection (`ingest/columns.py`, D18). Delimiter, locale (date orientation, decimal style), and column names are auto-detected for CSV; PDF uses table extraction (pdfplumber) with a line-oriented fallback and bank-specific row profiles (Capital One, Discover, Bank of America). Optional column overrides apply to both.

**Request**: `multipart/form-data`
- `file`: `.csv`, `.tsv`, `.txt`, or `.pdf` (required)
- `date_column`, `description_column`, `amount_column`: column names (optional; inferred from an EN+ES vocabulary if omitted)
- `debit_column`, `credit_column`: use instead of `amount_column` when charges/credits are in separate columns (debit → negative, credit → positive)
- `date_format`: explicit strptime format (optional, e.g. `%d/%m/%Y`)
- `dayfirst`: `true`/`false` to force `DD/MM` vs `MM/DD` (optional; auto-detected otherwise)
- `decimal_style`: `auto` (default) | `us` (`1,234.56`) | `eu` (`1.234,56`)
- `currency`: 3-letter statement currency code (optional, default `USD`)

Errors: `400` if the format is unrecognized, the file is empty, or no rows could be mapped to date/description/amount. PDFs that contain only account summaries (no transaction table) fail cleanly. Error messages never include row content.

**Response**: `201 Created`
```json
{
  "id": "uuid",
  "filename": "statement_march.csv",
  "currency": "USD",
  "transaction_count": 87,
  "uploaded_at": "2026-07-04T00:00:00Z"
}
```
Errors: `400` if the CSV cannot be parsed or minimum column mapping is missing.

#### GET /api/statements
Lists statements for the authenticated user (metadata only, no transactions). Each item includes `deleted_at` (`null` for active statements).

**Query params**:
- `archived`: `false` (default) → active statements only; `true` → the archived (soft-deleted, D22) statements for the "Archived" view, most-recently-archived first.

**Response**: `200 OK` → array of statements.

#### GET /api/statements/{id}
Statement detail including normalized transactions.

**Response**: `200 OK`
```json
{
  "id": "uuid",
  "filename": "statement_march.csv",
  "currency": "USD",
  "uploaded_at": "2026-07-04T00:00:00Z",
  "transactions": [
    { "id": "uuid", "date": "2026-03-02", "description": "NETFLIX.COM", "amount": 15.49, "category": "subscription" }
  ]
}
```
`404` if it does not exist or does not belong to the user.

#### DELETE /api/statements/{id}
**Archives** a statement (soft delete, D22). Sets `deleted_at`; the statement and all its derived analyses are hidden from the owner (reads and lists filter them out) but **retained** server-side and restorable. This is the everyday dashboard "delete". The pre-existing contract holds: a subsequent `GET /api/statements/{id}` returns `404`.

**Response**: `204 No Content`. `404` if it does not exist or is not owned by the caller.

#### POST /api/statements/{id}/restore
Restores an archived statement (undo, D22): clears `deleted_at`, making the statement and its analyses visible again.

**Response**: `200 OK` → the statement (same shape as `GET /api/statements` items). `404` if it does not exist or is not owned by the caller.

#### DELETE /api/statements/{id}/permanent
**Permanently deletes** a statement and all derived data — transactions and analyses — via schema cascade (D22, right to be forgotten, `DATA_MODEL.md` §3–§4). Irreversible. Works whether or not the statement was archived first.

**Response**: `204 No Content`. `404` if it does not exist or is not owned by the caller.

---

### Analysis (two-layer pipeline)

#### POST /api/analysis/{statement_id}
Runs analysis on an uploaded statement: **Layer 1 (rules)** detects recurring charges/subscriptions and estimates savings; **Layer 2 (LLM, optional)** adds finer categorization and natural-language recommendations. If Layer 2 fails or is disabled, Layer 1 results are returned with `ai_enabled: false`.

In the MVP only Layer 1 is active, so `ai_enabled` is always `false` (Layer 2 arrives in Phase B — `middle-phases.md`). Detection groups transactions by canonical merchant (D7); a charge recurring in ≥ 2 months with a stable amount is a subscription. `estimated_savings` is split (D21) into `potential_subscription_savings` (cancelling **discretionary** recurring categories — streaming, music, gaming, software, fitness, D16) and `avoidable_fees_total` (bank/card **fees**/commissions already paid — overdraft, ATM, maintenance, annual, etc., aggregated by fee type regardless of recurrence). `recommendations` carry a `kind`: `cancel_subscription` (discretionary, counted savings), `avoid_fee` (fees, counted savings), or `review_subscription` (essential recurring surfaced for review, `estimated_saving: 0`). Essential recurring charges are still listed under `detected_subscriptions`. `spending_comparison` aggregates `detected_subscriptions` by category for before/after charts: **before** is current recurring spend; **after** zeros discretionary categories (same D16 rule; fees are not subscriptions and do not appear here). Category names are open-ended (D9) — new categories added to the vocabulary appear automatically without API changes. Re-running appends a new analysis (D10). `404` if the statement does not exist or is not owned by the caller.

**Response**: `201 Created`
```json
{
  "id": "uuid",
  "statement_id": "uuid",
  "ai_enabled": false,
  "monthly_recurring_total": 41.47,
  "estimated_savings": 97.48,
  "avoidable_fees_total": 71.00,
  "potential_subscription_savings": 26.48,
  "detected_subscriptions": [
    { "merchant": "NETFLIX", "amount": 15.49, "cadence": "monthly", "category": "streaming" }
  ],
  "recommendations": [
    { "title": "Review NETFLIX subscription", "detail": "Recurring streaming charge of about 15.49 detected every month. Cancelling it would save about 15.49 per month.", "estimated_saving": 15.49, "kind": "cancel_subscription" },
    { "title": "Avoid overdraft fees", "detail": "You paid about 35.00 in overdraft fees (once on this statement). These charges are usually avoidable...", "estimated_saving": 35.00, "kind": "avoid_fee" },
    { "title": "Review recurring AMAZON PRIME charge", "detail": "Recurring shopping charge of about 14.99 from AMAZON PRIME. Likely essential, but worth reviewing...", "estimated_saving": 0.00, "kind": "review_subscription" }
  ],
  "spending_comparison": {
    "before": [
      { "category": "streaming", "amount": "15.49", "percentage": "37.4" }
    ],
    "after": [
      { "category": "streaming", "amount": "0.00", "percentage": "0.0" }
    ]
  },
  "created_at": "2026-07-04T00:00:00Z"
}
```

#### GET /api/analysis
Lists saved analyses for the user.

**Response**: `200 OK` → array of analysis summaries.

#### GET /api/analysis/{id}
Retrieves a saved analysis with full detail.

**Response**: `200 OK` → full analysis (same shape as POST). Includes `spending_comparison` (not present on list summaries). `404` if it does not exist or does not belong to the user.

#### GET /api/analysis/{analysis_id}/export.csv
Downloads a saved analysis as CSV (`text/csv`). Includes summary totals, detected subscriptions, and recommendations. Built in memory; the file is not persisted. Reuses the same ownership rules as `GET /api/analysis/{id}` (including hiding analyses of archived statements — D22).

**Response**: `200 OK` with `Content-Type: text/csv` and `Content-Disposition: attachment; filename="analysis-{id}.csv"`.

**Errors**: `404` `{"detail": "Analysis not found"}` if missing or not owned. `401` if unauthenticated.
---

## Interactive documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Versioning

Routes are ready for `/api/v1` (see `ARCHITECTURE.md`), but remain unversioned while there is a single consumer (the kit frontend).

## Rate limiting

Not implemented in the MVP. If exposed publicly, document the decision in `DECISIONS.md` before adding it. The highest-priority target is `POST /api/auth/forgot-password` (public + sends email) — see D23; add a per-IP/per-email limiter there first.
