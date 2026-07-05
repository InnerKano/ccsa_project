# analysis (planned)

**Endpoints:** `POST /api/analysis/{statement_id}`, `GET /api/analysis`, `GET /api/analysis/{id}` (`docs/API.md`)

**Models:** `Analysis`, `DetectedSubscription`, `Recommendation` (`docs/DATA_MODEL.md`)

**Depends on:** `auth`, `statements`

**Pipeline:** Layer 1 (rules) in `services.py`; Layer 2 (LLM) via `shared/llm/` with graceful fallback (D2).
