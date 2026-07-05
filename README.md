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

> **Current phase: Step 2.1 — backend walking skeleton.** FastAPI app with `GET /health`, modular folder layout, Dockerfile, and pytest. Full stack (Compose, DB, auth, features) comes in Steps 3+ per [`workflows/start-project.md`](./workflows/start-project.md).

## Backend — run locally
```powershell
cd backend/
```

All commands assume you are in `backend/`.

### Option A: venv (IDE + fast iteration)

Use this for editor autocomplete and quick runs. The venv is local-only (`backend/venv/`, gitignored).

```powershell
python -m venv venv
# activate venv
.\venv\Scripts\activate

.\venv\Scripts\pip install -r requirements.txt
.\venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Option B: Docker (matches production-like runtime)

```powershell
docker build -t ccsa-backend .
docker run --rm -p 8000:8000 ccsa-backend
```

### Option C: Docker Compose (Step 3 — not yet)

Once `docker-compose.yml` exists at repo root:

```bash
cp .env.example .env   # edit values
docker-compose up
docker-compose exec backend alembic upgrade head
```

### Verify the server is up

```powershell
curl http://localhost:8000/health
# → {"status":"healthy"}
```

- API docs → http://localhost:8000/docs
- Frontend → http://localhost:3000 (once Step 3 scaffold is complete)

## Backend — tests

**One test suite, any runtime.** Tests use FastAPI's `TestClient` (in-process — no running server required). You do not need separate tests for venv vs Docker; the same `pytest` runs in whichever environment has the dependencies installed.

| Type | What it covers | When |
|---|---|---|
| **API test** (`pytest`) | HTTP contract in-process (`/health`, later auth/statements) | Every feature commit |
| **Manual smoke** (`curl`) | Server actually listening (venv or Docker) | After infra changes |
| **End-to-end** | Full flow in browser or deployed URL | Before submission (`finish-project.md`) |

```powershell
# from backend/ with venv active or venv\Scripts\ prefix
pytest

# later, inside Compose (Step 3+)
docker-compose exec backend pytest
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
