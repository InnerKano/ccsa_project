# analysis

**Endpoints:** `POST /api/analysis/{statement_id}`, `GET /api/analysis`, `GET /api/analysis/{id}` (`docs/API.md`)

**Models:** `Analysis`, `DetectedSubscription`, `Recommendation` (`docs/DATA_MODEL.md`)

**Depends on:** `auth` (JWT, per-user isolation) and `statements` (source transactions)

**Pipeline (D2):** Layer 1 (rules) is implemented in the `rules/` package; Layer 2 (LLM) is deferred to Phase B and plugs in at the documented seam in `services.py` with graceful fallback. MVP runs are always `ai_enabled=false`, `layer_used="rules"`.

**Layer 1 rules (`rules/`, D16, bilingual EN+ES):**
- `vocabulary.py` — *data*: known-merchant aliases, EN+ES category keywords, controlled category set (D9), discretionary categories.
- `engine.py` — pure, DB-free logic: canonical merchant (D7), categorization, recurrence detection (≥ 2 months, stable amount), savings + recommendations. Unit-testable without Postgres.

**Persistence rules:**
- Re-analysis appends a new `Analysis` (D10); "current" = latest by `created_at`.
- Running analysis fills `transactions.category` (latest run wins).
- Every query is scoped by `user_id`; a non-owner gets `404` (never `403`).
