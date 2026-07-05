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

> **Current phase: Step 3 — local stack via Docker Compose.** Backend, frontend, and Postgres start together. Backend verifies DB connectivity on startup; Alembic migrations and feature modules come in Steps 4+ per [`workflows/start-project.md`](./workflows/start-project.md).

## Local development (recommended: Docker Compose)

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

Run tests inside Compose:

```powershell
docker compose exec backend pytest
```

> Migrations (`alembic upgrade head`) are Step 4 — not required yet for `/health`.

## Backend — alternative runtimes

Use these when iterating on backend code outside Compose.

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

## Backend — tests

**One test suite, any runtime.** Tests use FastAPI's `TestClient` (in-process — no running server required). `SKIP_DB_CHECK` is set automatically in `tests/conftest.py` so pytest does not need Postgres.

| Type | What it covers | When |
|---|---|---|
| **API test** (`pytest`) | HTTP contract in-process (`/health`, later auth/statements) | Every feature commit |
| **Manual smoke** (`curl`) | Server listening + DB reachable (Compose) | After infra changes |
| **End-to-end** | Full flow in browser or deployed URL | Before submission (`finish-project.md`) |

```powershell
# from backend/ (venv)
pytest

# inside Compose
docker compose exec backend pytest
```

Feature-specific tests live under `app/modules/<feature>/tests/` (see `workflows/implement-feature.md`).

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
- [Implement a Feature](./workflows/implement-feature.md)
- [Finish the Project](./workflows/finish-project.md)
