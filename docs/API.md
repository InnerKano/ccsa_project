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

Fixed kit base — does not change between projects.

#### POST /api/auth/register
**Request**:
```json
{ "email": "user@example.com", "password": "securepassword" }
```
**Response**: `201 Created`
```json
{ "id": "uuid", "email": "user@example.com", "token": "jwt_token" }
```

#### POST /api/auth/login
**Request**:
```json
{ "email": "user@example.com", "password": "securepassword" }
```
**Response**: `200 OK`
```json
{ "token": "jwt_token" }
```

---

### Statements (CSV upload and parsing)

#### POST /api/statements
Uploads a **delimited** transaction export (CSV/TSV; `.csv`/`.tsv`/`.txt`). Parsed in memory; **the raw file is not stored**, only normalized transactions. Delimiter, locale (date orientation, decimal style), and column names are auto-detected, with optional overrides. Raw PDF/statement dumps are not supported (D15).

**Request**: `multipart/form-data`
- `file`: delimited file (required)
- `date_column`, `description_column`, `amount_column`: column names (optional; inferred from an EN+ES vocabulary if omitted)
- `debit_column`, `credit_column`: use instead of `amount_column` when charges/credits are in separate columns (debit → negative, credit → positive)
- `date_format`: explicit strptime format (optional, e.g. `%d/%m/%Y`)
- `dayfirst`: `true`/`false` to force `DD/MM` vs `MM/DD` (optional; auto-detected otherwise)
- `decimal_style`: `auto` (default) | `us` (`1,234.56`) | `eu` (`1.234,56`)
- `currency`: 3-letter statement currency code (optional, default `USD`)

Errors: `400` if the format is unrecognized (e.g. a PDF dump), the file is empty/non-delimited, or a row cannot be parsed. Error messages never include row content.

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
Lists statements for the authenticated user.

**Response**: `200 OK` → array of statements (metadata only, no transactions).

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
Deletes a statement and its derived data.

**Response**: `204 No Content`.

---

### Analysis (two-layer pipeline)

#### POST /api/analysis/{statement_id}
Runs analysis on an uploaded statement: **Layer 1 (rules)** detects recurring charges/subscriptions and estimates savings; **Layer 2 (LLM, optional)** adds finer categorization and natural-language recommendations. If Layer 2 fails or is disabled, Layer 1 results are returned with `ai_enabled: false`.

In the MVP only Layer 1 is active, so `ai_enabled` is always `false` (Layer 2 arrives in Phase B — `middle-phases.md`). Detection groups transactions by canonical merchant (D7); a charge recurring in ≥ 2 months with a stable amount is a subscription. `recommendations` and `estimated_savings` cover only **discretionary** recurring categories (streaming, music, gaming, software, fitness — D16); essential recurring charges are still listed under `detected_subscriptions` but not flagged for cancellation. Re-running appends a new analysis (D10). `404` if the statement does not exist or is not owned by the caller.

**Response**: `201 Created`
```json
{
  "id": "uuid",
  "statement_id": "uuid",
  "ai_enabled": true,
  "monthly_recurring_total": 62.97,
  "estimated_savings": 30.98,
  "detected_subscriptions": [
    { "merchant": "NETFLIX", "amount": 15.49, "cadence": "monthly", "category": "streaming" }
  ],
  "recommendations": [
    { "title": "Cancel Netflix", "detail": "No recent usage detected; you could save ~$15.49/mo.", "estimated_saving": 15.49 }
  ],
  "created_at": "2026-07-04T00:00:00Z"
}
```

#### GET /api/analysis
Lists saved analyses for the user.

**Response**: `200 OK` → array of analysis summaries.

#### GET /api/analysis/{id}
Retrieves a saved analysis with full detail.

**Response**: `200 OK` → full analysis (same shape as POST). `404` if it does not exist or does not belong to the user.

---

## Interactive documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Versioning

Routes are ready for `/api/v1` (see `ARCHITECTURE.md`), but remain unversioned while there is a single consumer (the kit frontend).

## Rate limiting

Not implemented in the MVP. If exposed publicly, document the decision in `DECISIONS.md` before adding it.
