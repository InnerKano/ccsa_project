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
- **Frontend:** Next.js + Tailwind CSS + React Context + SWR — see [`frontend/DESIGN.md`](./frontend/DESIGN.md) and [`frontend/README.md`](./frontend/README.md)
- **AI:** provider-agnostic (Ollama local / OpenAI) configurable via `.env`
- **Infra:** Docker Compose (local); Vercel (frontend) + Railway/Render (backend)

## Project status

Bootstrap (Steps 1–5) and **Phase A** (A1–A4.5) are implemented — backend + full browser flow on Layer 1 only (no LLM). See [`workflows/middle-phases.md`](./workflows/middle-phases.md).

| # | Delivery | Status |
|---|---|---|
| A1 | Auth (register/login, JWT) | ✅ Done |
| A2 | Statements (CSV upload) | ✅ Done |
| A2.1 | Ingestion hardening (formats/locales, EN+ES, US/EU) | ✅ Done |
| A3 | Analysis (Layer 1, rules) | ✅ Done |
| A4.1 | Frontend foundations + CORS | ✅ Done |
| A4.2 | Auth screens + protected routes | ✅ Done |
| A4.3 | Upload screen | ✅ Done |
| A4.4 | Dashboard hub (list + run analysis) | ✅ Done |
| A4.5 | Results breakdown (`/analysis/[id]`) | ✅ Done |
| A4.6 | Docs closeout | ⬜ Pending audit |
| A5 | Sample CSV fixtures (US + LatAm, synthetic) | ✅ Done (with A2/A2.1) |

**Manual verification:** `docker compose up --build` → http://localhost:3000. Details: [`workflows/implement-feature.md`](./workflows/implement-feature.md) Step 6.

## Phase A happy path (browser, no LLM)

With Compose running:

1. Open http://localhost:3000 → **Register** (or log in).
2. **Upload** → select `backend/fixtures/sample.csv` → submit.
3. **Dashboard** → confirm the statement → **Run analysis**.
4. **Results** → verify subscriptions (NETFLIX, SPOTIFY, AMAZON PRIME), recommendations, and savings totals.
5. **Sign out** → **Sign in** → **View results** on the same statement (saved analysis, D6).

Expected from `sample.csv` (rules-only): ~**$41.47/mo** recurring, ~**$26.48** estimated savings (`backend` integration tests).

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
docker compose exec backend alembic current        # a3_analysis_001 after A3
docker compose exec backend alembic upgrade head   # apply any pending migrations
```

Run the full test suite:

```powershell
docker compose exec backend pytest
```

This one command covers both API tests (in-process `TestClient`, no Postgres required — `SKIP_DB_CHECK` is set automatically in `tests/conftest.py`) and structure tests (`test_structure.py`, bootstrap layout). Feature-specific tests live under `app/modules/<feature>/tests/` (see [`workflows/implement-feature.md`](./workflows/implement-feature.md)).

## Trying it out manually

With Compose running, exercise the API from the browser (CORS allow-list includes `http://localhost:3000` since A4.1) or via `curl`/Swagger:

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

**Statements (A2)** — requires a JWT from login:

```powershell
# Upload sample CSV (replace TOKEN)
curl -X POST http://localhost:8000/api/statements `
  -H "Authorization: Bearer TOKEN" `
  -F "file=@backend/fixtures/sample.csv"

# List statements
curl http://localhost:8000/api/statements -H "Authorization: Bearer TOKEN"
```

You can also drive the same requests interactively from Swagger at http://localhost:8000/docs.

## Local development without full Docker (venv + host Node)

For fast day-to-day iteration you can run the backend in a Python **venv** and the frontend
with **host Node**, keeping only Postgres in a container. Code reloads instantly and the IDE
resolves imports. The full ordered guide (setup → run → migrations → tests → verify) is in
[`workflows/local-dev.md`](./workflows/local-dev.md). Quick version, from the repo root:

```powershell
cp .env.example .env            # DATABASE_URL already targets localhost:5432
docker compose up -d db         # only Postgres in a container

cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000   # http://localhost:8000/health

cd frontend
npm install
npm run dev                     # http://localhost:3000
```

Compose remains the **canonical, verified** path for a clean-from-scratch run and final
per-feature verification (`implement-feature.md` Step 6).

### Running tests outside Compose

Same suite, same result, no running server required:

```powershell
cd backend
pytest
```

Unit and API tests set `SKIP_DB_CHECK` automatically and pass without Postgres; DB-backed
integration tests skip unless `docker compose up -d db` is running.

### Standalone Docker image (backend only)

```powershell
cd backend
docker build -t ccsa-backend .
docker run --rm -p 8000:8000 -e SKIP_DB_CHECK=true ccsa-backend
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
- [Frontend Design System](./frontend/DESIGN.md) — UI/UX tokens and component rules
- [AI Rules](./docs/AI_RULES.md) · [AI Log](./docs/AI_LOG.md) — responsible AI usage and logging

## Workflows

- [Start a Project](./workflows/start-project.md)
- [Middle Phases](./workflows/middle-phases.md) — post-bootstrap delivery plan and phase status
- [Implement a Feature](./workflows/implement-feature.md)
- [Local Development](./workflows/local-dev.md) — venv + host Node dev loop (fast iteration without full Docker)
- [Finish the Project](./workflows/finish-project.md)