# Workflow: Start a Project

## Step 1: Complete planning (Commit 1 — no code)

1. **`docs/REQUIREMENTS.md`** — problem interpretation, constraints, assumptions, risks, and chosen approach.
2. **`docs/PROJECT_SCOPE.md`** — Must/Should/Could/Won't Have, derived from `REQUIREMENTS.md`.
3. **`docs/ARCHITECTURE.md`** — explain why the project is organized this way (structure, stack, modular backend) before creating any folders.
4. **`docs/DECISIONS.md`, `docs/AI_RULES.md`** — remaining technical and process planning.
5. **`workflows/*.md`** — how the team will work going forward.

## Step 2: Create the structure (Commit 2 — code, no business logic)

Complete the architectural analysis for backend and frontend before creating the project structure.

## Step 2.1: Infra backend + /health real (walking skeleton, lado backend)

- **requirements.txt** (fastapi, uvicorn, sqlalchemy, alembic, psycopg2-binary, pydantic-settings)
- **main.py** → app FastAPI real con GET /health
- **backend/Dockerfile**
- (venv desde requirements.txt)
- **Verificable**: uvicorn app.main:app local → curl localhost:8000/health

## Step 3: Start services (Compose + Postgres reachable)

Goal: one command brings up backend, frontend, and Postgres. Backend verifies DB on startup; `/health` stays the public contract.

- **`docker-compose.yml`** at repo root (`backend`, `frontend`, `db`)
- **`.env.example`** — copy to `.env` before first run
- **`core/config.py` + `core/database.py`** — `DATABASE_URL` wiring; startup `SELECT 1` (skipped in pytest via `SKIP_DB_CHECK`)
- **Frontend scaffold** — minimal Next.js so the `frontend` service can start
- **Verifiable:**
  ```bash
  cp .env.example .env
  docker compose up --build
  curl http://localhost:8000/health          # → {"status":"healthy"}
  docker compose exec db pg_isready -U postgres -d ccsa
  ```

## Step 4: Database (Alembic wiring — no feature tables yet)

Goal: migration tooling ready and documented. The **first revision ships with the auth feature** (`users` table per `DATA_MODEL.md`) — no empty migrations.

- **`alembic init`** → `backend/alembic/` wired to `core/config` (`DATABASE_URL`) and `Base.metadata`
- **`core/database.py`** → add `get_db()` FastAPI dependency (routes use `Depends(get_db)`)
- **`core/models.py`** → central import registry; each new feature registers its models here for autogenerate
- **No tables yet** — `alembic/versions/` stays empty until auth
- **Verifiable:**
  ```bash
  docker compose exec backend alembic current    # no revision yet
  docker compose exec backend alembic upgrade head   # succeeds (nothing to apply)
  docker compose exec backend pytest
  ```

Next: **auth feature** via `implement-feature.md` (model → register in `core/models.py` → first migration → endpoints).

## Step 5: Validate structure (bootstrap complete)

Goal: confirm code, infra, and docs describe the **same** modular monolith before building features.

### Checklist — backend

- [x] `app/core/` — `config.py`, `database.py` (+ `get_db`), `models.py` (Alembic registry)
- [x] `app/modules/` — README + planned stubs (`auth`, `statements`, `analysis`)
- [x] `app/shared/` — README (LLM layer documented, not implemented yet)
- [x] `app/main.py` — lifespan DB check + router registration pattern commented
- [x] `backend/alembic/` — wired; `versions/` empty until auth
- [x] `backend/tests/test_structure.py` — layout assertions (no Postgres)

### Checklist — repo / infra

- [x] `docker-compose.yml` + `.env.example` at repo root
- [x] Dockerfiles in `backend/` and `frontend/` (D11 — no orphan `docker/` folder)
- [x] `docs/ARCHITECTURE.md` tree matches disk
- [x] `frontend/app/`, `frontend/lib/`, `frontend/components/` present

### Verifiable

```bash
docker compose exec backend pytest          # 7 passed (monorepo mounted at /workspace)
docker compose exec backend alembic current # no revision until auth
```

Compose mounts the repo root at `/workspace` (D12) — not `./backend:/app` alone — so structure tests see `docker-compose.yml` and `frontend/` inside the container.

### Testing policy (bootstrap steps)

| Step | Automated (`pytest`) | Manual smoke |
|---|---|---|
| 2.1 | `test_health` — API contract | `curl /health` |
| 3 | — | `compose up`, `pg_isready` |
| 4 | `test_health` (DB skipped in tests) | `alembic current`, `upgrade head` |
| 5 | `test_structure` — backend + monorepo layout (7 in Docker and host) | Review checklist above |

Feature modules add API tests under `modules/<feature>/tests/` (`implement-feature.md`).

---

## Normal flow after bootstrap

Bootstrap (Steps 1–5) is **one-time per project**. Ongoing work follows this loop:

1. Pick the next **Must Have** from `docs/PROJECT_SCOPE.md`.
2. Execute `workflows/implement-feature.md` end-to-end (plan → migration → backend → tests → frontend → docs → commit).
3. Record non-trivial AI usage in `docs/AI_LOG.md`.

**First feature:** `auth` (`app/modules/auth/`) — first real migration (`users`), Red zone security review.

---

## Reference layout
```
backend/app/
├── main.py
├── core/            # config, security, logging — only modify if it is cross-cutting
├── modules/
│   └── <feature>/   # each new feature: api.py, models.py, schemas.py, services.py
└── shared/          # code reused by 2+ modules

frontend/
├── app/             # routes (Next.js App Router)
├── components/      # reusable UI
└── lib/             # API client, utilities
```

Each new feature is a new folder under `modules/`. Do not add loose files at the root of `api/`, `models/`, or `schemas/`.

---

## Troubleshooting

If issues are found, make the necessary changes. Common problems include Docker, database, or port conflicts.

---
