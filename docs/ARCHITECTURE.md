# Architecture — Credit Card Savings Analyzer (CCSA)

## Why this structure?

Before creating any code folders, these are the organizational decisions and the reasoning behind them for this project:

- **Monorepo (`backend/` + `frontend/` in the same repo):** a single project, a single developer, a single deployment cycle. Splitting into two repos would add coordination overhead without clear benefit in this context.
- **`docs/` separated from code:** product and architecture decisions should be readable without opening code, for reviewers and for future maintenance.
- **`workflows/` as an explicit process:** under a tight deadline it's easy to skip steps (tests, documentation). Having the process written reduces that risk.
- **Modular backend (by feature, not by technical layer):** with few features but multiple artifacts each (model, schema, endpoint, logic), grouping by feature keeps related code together. Adding a feature means creating a folder, not touching five different places.
- **REST over GraphQL, JWT over sessions:** pragmatic defaults that allow fast progress with minimal learning curve for this project.
- **Document decisions, not exhaustive how-tos:** record what is not obvious or what was decided between alternatives in `DECISIONS.md`.

This section is the justification written before creating the physical structure.

---

## Overview

This document is the single source of truth about how the project is organized and how it should evolve.

The approach is a full-stack monorepo with a modular backend and a modern frontend. For CCSA, the core logic is a **two-layer analysis pipeline** (rules → LLM) operating on transactions uploaded by the user as CSV.

---

## Project Structure

```text
ccsa_project/
├── backend/                 # FastAPI app, Dockerfile, Alembic, requirements.txt
├── frontend/                # Next.js app, Dockerfile, package.json
├── docker-compose.yml       # Local stack: backend + frontend + Postgres
├── .env.example             # Copy to .env before first run
├── workflows/               # Engineering processes
└── docs/                    # Project documentation
```

Dockerfiles live **next to each service** (`backend/Dockerfile`, `frontend/Dockerfile`), not in a separate `docker/` folder — see `DECISIONS.md` D11.

**Local development:** Compose mounts the **full monorepo** at `/workspace` (D12) so backend and frontend run from `/workspace/backend` and `/workspace/frontend` with the same tree pytest and docs expect.

Each application owns its implementation, configuration, and documentation within the same repository.

---

## Technology Stack

### Backend

- **FastAPI** as the primary framework for its async model and typed API support.
- **PostgreSQL** as the database for reliability and production readiness.
- **SQLAlchemy** as the ORM and **Alembic** for schema migrations.
- **JWT authentication** (stateless) for simplicity and scalability.
- **CSV parsing** with standard libraries; use `pandas` only if it provides clear value (decision tracked in `DECISIONS.md`).
- **LLM layer behind a provider-agnostic interface** (Ollama local / OpenAI) selectable via environment variable.

### Frontend

**Next.js** for a solid developer experience. Styling with **Tailwind CSS** (v4, CSS-first tokens in `app/globals.css`). For state and data fetching, a lightweight approach using **React Context + SWR** is sufficient for upload and dashboard flows.

### Frontend layout (built — Phase A4)

```text
frontend/
├── DESIGN.md                # UI/UX source of truth (tokens, components, states)
├── app/
│   ├── globals.css          # Tailwind @theme tokens
│   ├── layout.tsx           # root shell + Providers
│   ├── providers.tsx        # SWRConfig + AuthProvider
│   ├── page.tsx             # landing (auth-aware)
│   ├── login/               # register / login (AuthLayout)
│   ├── register/
│   ├── dashboard/           # statement list + run analysis
│   ├── upload/              # CSV upload
│   └── analysis/[id]/       # results breakdown
├── components/
│   ├── auth/                # RequireAuth, GuestOnly
│   ├── layout/              # AppShell, AuthLayout
│   ├── ui/                  # Button, Field, Card, Alert, Spinner, …
│   ├── statements/          # StatementUploadForm
│   ├── dashboard/           # StatementCard, StatementList
│   └── analysis/            # AnalysisDetailView, SubscriptionList, RecommendationList, …
└── lib/
    ├── api/                 # client.ts, auth.ts, statements.ts, analysis.ts
    ├── auth/                # session.ts, context.tsx
    ├── cn.ts
    └── format.ts
```

**Rules:** screens compose primitives and call `lib/api/<feature>.ts`; they do not call `fetch` directly. New backend features get a matching `lib/api/` module. JWT is attached by `apiFetch`, not passed manually per call.

**Visual/UX consistency:** the design tokens, component usage, and interaction conventions are defined in [`frontend/DESIGN.md`](../frontend/DESIGN.md). Entry point for frontend developers: [`frontend/README.md`](../frontend/README.md).

**Local Compose note:** `node_modules` for the frontend lives in a named Docker volume (`frontend_node_modules`). The compose service runs `npm install && npm run dev` on startup so dependency changes in `package.json` sync without a manual reinstall — see `implement-feature.md` Step 6.

### Infrastructure

**Docker** + **Docker Compose** for local development. **GitHub Actions** for CI/CD. Frontend deploy to **Vercel**; backend to **Railway** or **Render**; managed PostgreSQL for the database.

---

## Backend Architecture

Modular monolith: each business feature is organized as its own module to keep related code together and reduce coupling.

### Recommended layout

```text
backend/
└── app/
    ├── main.py              # application entry point
    ├── core/                # cross-cutting configuration (config, security, logging)
    ├── modules/             # feature modules
    └── shared/              # reusable components across modules
```

### CCSA modules

```text
backend/app/modules/
├── auth/                    # Starter kit auth: register / login (JWT)
├── statements/              # CSV upload & parsing → normalized transactions
│   ├── api.py               #   POST /api/statements, GET /api/statements, GET /{id}
│   ├── models.py            #   Statement, Transaction
│   ├── schemas.py           #   input/output contracts
│   └── services.py          #   CSV parsing, column mapping, validation
└── analysis/                # Two-layer analysis pipeline + persistence
    ├── api.py               #   POST /api/analysis/{statement_id}, GET /api/analysis/{id}
    ├── models.py            #   Analysis, DetectedSubscription, Recommendation
    ├── schemas.py
    └── services.py          #   Layer 1 (rules) + Layer 2 (LLM) + fallback
```

### LLM layer (provider-agnostic)

The LLM integration lives behind a common interface in `shared/` (or `core/`) and is not coupled to a specific vendor:

```text
backend/app/shared/llm/
├── base.py                  # LLMProvider interface (methods like .analyze(...) / .categorize(...))
├── openai_provider.py       # OpenAI implementation
├── ollama_provider.py       # Ollama (local) implementation
└── factory.py               # selects provider based on .env (LLM_PROVIDER)
```

**Graceful degradation rule:** if Layer 2 (LLM) fails or is disabled, `analysis/services.py` returns Layer 1 results. The product never fails to produce output due to an AI failure.

### core/

Cross-cutting concerns: configuration, dependency wiring, startup hooks, security, logging.

### shared/

Components reused by two or more modules: utilities, common exceptions, shared schemas, and the LLM abstraction. Business logic should not live here unless intentionally shared.

---

## API Design

- Resource-based URLs
- Standard HTTP methods
- JSON bodies, no envelope
- Consistent errors (`{"detail": "..."}`)
- Routes prepared for versioning (`/api/v1`) but not versioned yet

---

## Database

PostgreSQL. Schema changes are always versioned with Alembic migrations. Never modify production schema by hand.

Alembic lives in `backend/alembic/` and reads `DATABASE_URL` from `core/config.py`. All module models must be imported in `core/models.py` so autogenerate detects them. The first migration ships with the auth feature (`users`), not as an empty scaffold — see `workflows/start-project.md` Step 4.

**High-level CCSA data model:**

- `Statement` — a statement uploaded by a user (metadata: filename, upload date, currency). **The raw file is not stored**, only the derived transactions.
- `Transaction` — normalized row (date, description, amount, category). Linked to a `Statement`.
- `Analysis` — the result of running the pipeline on a `Statement` (totals, estimated savings, which layer produced the result).
- `DetectedSubscription` / `Recommendation` — actionable findings linked to an `Analysis`.

All resources are scoped to `user_id`: a user must never access another user's data (enforced in each query).

> The **field-by-field schema, PII classification, cascade/deletion rules, encryption, retention, and scaling** live in [`DATA_MODEL.md`](./DATA_MODEL.md). That document is the source of truth for what is stored and under which responsible-data rules.

---

## Authentication

JWT with Bearer tokens.

1. User credentials are exchanged for a JWT.
2. The frontend stores the token in `localStorage` via `lib/auth/session.ts` (MVP; swap here if httpOnly cookies are adopted later).
3. `apiFetch` attaches the token in the `Authorization` header on every authenticated request.
4. The backend validates the token and returns only resources owned by the token's user.

---

## Sensitive data security (FinTech)

Because this project handles financial data, these rules are part of the architecture:

- **Do not persist raw files:** parse in memory and store only the normalized transactions needed.
- **Do not log transactions or statement content** (neither in application logs nor in error messages).
- **Strict per-user isolation** on every endpoint and query.
- **Secrets out of code** (`.env` in `.gitignore`); LLM provider keys never in the repository.
- **Explicit CORS** (no `*` in production). Development allow-list: `CORS_ORIGINS=http://localhost:3000` in `.env` (wired in A4.1 — `core/config.py` + `CORSMiddleware` in `main.py`). Production adds the deployed frontend origin (see `DEPLOYMENT.md`).

---

## Deployment

Deployment choices depend on the hosting platform, available resources, cost, and the project timeline.

**Development:** Docker Compose local (canonical, verified). For fast day-to-day iteration, a venv + host Node loop (only Postgres in a container) is documented in [`workflows/local-dev.md`](../workflows/local-dev.md) — same code, hot reload, IDE-friendly.

**Production:**
- Frontend → Vercel
- Backend → Railway or Render
- Database → Managed PostgreSQL

---

## Architectural pattern clarification

This project is a **modular monolith**: a single backend deployment organized by feature (`modules/<feature>/`) rather than by technical layer.

The backend is a pure API (FastAPI) consumed by a decoupled frontend (Next.js). Each module typically follows the controller → service → model flow:

- `api.py` — validates and receives the HTTP request (controller role).
- `services.py` — business logic (the analysis pipeline lives here).
- `models.py` — data access via SQLAlchemy.
- `schemas.py` — Pydantic input/output shapes.

Apply SOLID pragmatically (single responsibility per file, dependency injection via `Depends`) without a full hexagonal architecture: the project size and lifetime do not justify that complexity.

---

## Architecture Rules

When extending the project:

- add features by creating new modules
- reuse shared components where appropriate
- keep clear boundaries between features
- avoid unnecessary abstractions
- prioritize maintainability over complexity

The architecture grows by adding focused modules, not by increasing coupling across existing code.
