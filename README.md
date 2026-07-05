# Credit Card Savings Analyzer (CCSA)

Upload your credit card CSV and discover where your money goes each month: subscriptions and recurring charges are detected automatically, with an estimate of how much you could save by cancelling unused services.

Project for the 72-hour challenge. The goal is a focused prototype that demonstrates product thinking, technical judgment, and the use of AI as an accelerator — not a polished production application.

## What it does

1. Users register and log in.
2. They upload a statement in **CSV** (the raw file is not stored; only the derived transactions are saved).
3. The system analyzes the data in **two layers**:
   - **Layer 1 (rules, no AI):** normalizes transactions, detects recurring merchants/subscriptions, and computes estimated savings.
   - **Layer 2 (LLM, optional):** provides finer categorization and natural-language recommendations. If it fails or is disabled, the product gracefully falls back to Layer 1.
4. Results are saved to the user's account.

## Stack

- **Backend:** FastAPI + PostgreSQL + SQLAlchemy + Alembic (JWT auth)
- **Frontend:** Next.js + Tailwind CSS
- **AI:** provider-agnostic (Ollama local / OpenAI) configurable via `.env`
- **Infra:** Docker Compose (local); Vercel (frontend) + Railway/Render (backend)

## Project status

Bootstrap (Steps 1–5) and Phase A1 are complete. See [`workflows/middle-phases.md`](./workflows/middle-phases.md) for the full delivery plan and current phase boundaries.

| # | Delivery | Status |
|---|---|---|
| A1 | Auth (register/login, JWT) | ✅ Done |
| A2 | Statements (CSV upload) | ⬜ Next |
| A3 | Analysis (Layer 1, rules) | ⬜ Pending |
| A4 | Frontend vertical slice + CORS | ⬜ Pending |
| A5 | Sample CSV fixture | ⬜ Pending |

> CORS is intentionally not configured yet — it ships with A4. Until then, `localhost:3000` can render the auth screens but browser requests to the API will be blocked; use `curl` or Swagger to exercise endpoints manually (see "Trying it out manually" below).

## Quickstart (Docker Compose)

From the **repo root**:

```powershell
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API + Swagger | http://localhost:8000/docs |
| Health | http://localhost:8000/health → `{"status":"healthy"}` |

Verify Postgres is up:

```powershell
docker compose exec db pg_isready -U postgres -d ccsa
```

Apply migrations:

```powershell
docker compose exec backend alembic current        # a1_users_001 (users table) after A1
docker compose exec backend alembic upgrade head   # apply any pending migrations
```

Run the full test suite:

```powershell
docker compose exec backend pytest
```

This one command covers both API tests (in-process `TestClient`, no Postgres required — `SKIP_DB_CHECK` is set automatically in `tests/conftest.py`) and structure tests (`test_structure.py`, bootstrap layout). Feature-specific tests live under `app/modules/<feature>/tests/` (see [`workflows/implement-feature.md`](./workflows/implement-feature.md)).

## Trying it out manually

With Compose running, exercise the current API directly (works over `curl`/Swagger; browser flow arrives with CORS in A4):

```powershell
# Register
curl -X POST http://localhost:8000/api/auth/register `
  -H "Content-Type: application/json" `
  -d '{"email":"test@example.com","password":"changeme123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{"email":"test@example.com","password":"changeme123"}'
```

A successful login returns a JWT. Full endpoint list and request/response shapes: [`docs/API.md`](./docs/API.md).

You can also drive the same requests interactively from Swagger at http://localhost:8000/docs.

## Appendix: alternative backend runtimes

Use these only when iterating on backend code **outside** Compose. Compose remains the recommended and verified path above.

```powershell
cd backend
```

### Option A: venv (IDE + fast iteration)

The venv is local-only (`backend/venv/`, gitignored). For `/health` without Postgres, set `SKIP_DB_CHECK=true` in `.env` or export it for the session.

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Option B: standalone Docker image

```powershell
docker build -t ccsa-backend .
docker run --rm -p 8000:8000 -e SKIP_DB_CHECK=true ccsa-backend
```

### Running tests outside Compose

Same suite, same result, no running server required:

```powershell
cd backend
pytest
```

## Deployment

See [Deployment Guide](./docs/DEPLOYMENT.md) — Vercel (frontend) + Railway/Render (backend + PostgreSQL).

## Documentation

- [Requirements](./docs/REQUIREMENTS.md) — problem interpretation, constraints, risks
- [Project Scope](./docs/PROJECT_SCOPE.md) — Must/Should/Could/Won't Have
- [Architecture](./docs/ARCHITECTURE.md) — structure, modules, and analysis pipeline
- [Data Model](./docs/DATA_MODEL.md) — schema, PII classification, retention, and responsible data handling
- [Decisions](./docs/DECISIONS.md) — technical decisions and trade-offs
- [API Reference](./docs/API.md) — endpoints
- [AI Rules](./docs/AI_RULES.md) · [AI Log](./docs/AI_LOG.md) — responsible AI usage and logging

## Workflows

- [Start a Project](./workflows/start-project.md)
- [Middle Phases](./workflows/middle-phases.md) — post-bootstrap delivery plan and phase status
- [Implement a Feature](./workflows/implement-feature.md)
- [Finish the Project](./workflows/finish-project.md)