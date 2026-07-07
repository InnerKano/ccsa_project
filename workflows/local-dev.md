# Workflow: Local Development (venv + Node, no full Docker)

The Docker path (`docker compose up --build`) is the **canonical, verified** way to run
the whole stack (see `README.md` and `implement-feature.md` Step 6). This document is the
ordered alternative for **day-to-day iteration**: run the backend in a Python **venv** and
the frontend with **host Node**, so code changes reload instantly, the IDE resolves imports,
and you can attach a debugger — without rebuilding an image.

Everything here has been run end-to-end on Windows/PowerShell (Python 3.14, Node 24). bash
equivalents are noted where they differ.

---

## The one thing that still needs a container: Postgres

The backend talks to PostgreSQL. You do **not** need a native Postgres install — the simplest
"venv dev loop" runs **only the database** in a container and everything else on the host:

```powershell
# From the repo root — start just Postgres (published on localhost:5432)
docker compose up -d db
docker compose exec db pg_isready -U postgres -d ccsa   # → accepting connections
```

`localhost:5432` reaches that container. This is what `DATABASE_URL` in `.env` points to
(`.env.example` ships with the localhost value). Under Compose that same variable is
overridden to the `db` hostname, so the two workflows do not collide.

Alternatives (pick one, in order of convenience):

| DB source | When | `DATABASE_URL` |
|---|---|---|
| `docker compose up -d db` (recommended) | You have Docker; want a real DB with zero install | `...@localhost:5432/ccsa` |
| Native PostgreSQL install | You want no Docker at all | point at your local instance, DB `ccsa` |
| No DB — `SKIP_DB_CHECK=true` | Editing pure logic / running unit + API tests only | irrelevant (not used) |

With `SKIP_DB_CHECK=true` the app boots and `/health`, structure tests, and in-process API
tests run, but the full happy path (register → upload → analysis persistence) does **not** —
those need Postgres.

---

## Step 0: One-time setup

### Environment file (repo root)

```powershell
cp .env.example .env
```

The default `.env` already targets `localhost:5432`, so the venv backend connects to the
`db` container with no edits.

### Backend venv (`backend/`)

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate                 # bash/macOS: source venv/bin/activate
pip install -r requirements.txt
```

The venv lives at `backend/venv/` and is gitignored. Reinstall only when
`requirements.txt` changes (`pip install -r requirements.txt` again) — no image rebuild.

> **Windows note:** if `.\venv\Scripts\activate` is blocked by execution policy, either run
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` for the session, or skip
> activation entirely and call the interpreter directly: `.\venv\Scripts\python.exe -m ...`.

### Frontend (`frontend/`)

```powershell
cd frontend
npm install
```

On the host, `node_modules` lives on disk (not in the Compose named volume), so a new
dependency is picked up with a plain `npm install` — no volume-sync dance.

---

## Step 1: The daily dev loop

Three processes. Use three terminals (or run the first detached).

```powershell
# 1) Database (once per session; -d leaves it running in the background)
docker compose up -d db

# 2) Backend — auto-reloads on every .py change
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 3) Frontend — auto-reloads on every .tsx/.css change
cd frontend
npm run dev
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API + Swagger | http://localhost:8000/docs |
| Health | http://localhost:8000/health → `{"status":"healthy"}` |

`NEXT_PUBLIC_API_URL` defaults to `http://localhost:8000`, so the browser app talks to the
venv backend with no extra config. CORS already allows `http://localhost:3000`
(`core/config.py`).

> **Port conflict:** if the full Compose stack is already up it owns `3000`/`8000`. Stop it
> (`docker compose down`, keeping `db` up with `docker compose up -d db`) or run the venv
> backend on another port (`--port 8001`) and set `NEXT_PUBLIC_API_URL=http://localhost:8001`.

---

## Step 2: Migrations (venv)

Same Alembic, run from `backend/` with the venv active (mirrors `implement-feature.md`
Step 2, minus the `docker compose exec backend` prefix):

```powershell
cd backend
alembic current                                   # a3_analysis_001 (head) after A3
alembic upgrade head                              # apply pending migrations
alembic revision --autogenerate -m "Add X table"  # after registering the model in core/models.py
```

Review the generated migration by hand (`AI_RULES.md`, Yellow zone) before `upgrade head`.
`alembic` reads `DATABASE_URL` from `.env` via `core/config`, so it hits the same
`localhost:5432` database the app uses. (`python -m alembic ...` works too if you skip
activation.)

---

## Step 3: Testing (venv)

The whole suite runs from `backend/` with no server running:

```powershell
cd backend
pytest                       # full suite
pytest app/modules/analysis  # one feature's tests
pytest -q -k recurrence      # by keyword
```

- **Unit + API tests** use FastAPI's in-process `TestClient` and set `SKIP_DB_CHECK` in
  `tests/conftest.py`, so they pass **without Postgres**.
- **Integration tests** under `app/modules/<feature>/tests/` that need a real DB **skip
  automatically** when Postgres is unavailable. To exercise them, keep `docker compose up -d db`
  running.

This is the same command and the same result as `docker compose exec backend pytest`.

---

## Step 4: Verify a feature end-to-end (venv equivalent of `implement-feature.md` Step 6)

1. Ensure the three processes from Step 1 are up (`db` + backend + frontend).
2. Apply migrations if the feature added any: `alembic upgrade head`.
3. Exercise the happy path at http://localhost:3000, or hit the API via Swagger / `curl`.
4. Inspect persistence directly in Postgres:

```powershell
docker compose exec db psql -U postgres -d ccsa -c "SELECT id FROM analyses LIMIT 3;"
```

**Phase A browser happy path** (no LLM): register → **Upload** `backend/fixtures/sample.csv` →
**Dashboard** → **Run analysis** → **Results** (NETFLIX, SPOTIFY, AMAZON PRIME; ~$41.47/mo
recurring, $97.48 estimated savings = $26.48 subscriptions + $71.00 avoidable fees, D21) →
sign out → sign in → **View results** again (D6 persistence). Full script: `README.md` § Phase A
happy path.

---

## Step 5: Quality pass (venv)

```powershell
cd backend && black app        # if black is installed in the venv
cd frontend && npm run lint
```

`black` is not in `requirements.txt`; install it in the venv only if you want it locally
(`pip install black`). Do not block a feature on minor warnings — security issues (Red zone,
`AI_RULES.md`) do block.

---

## When to still use full Docker

- **Final verification before commit** — `implement-feature.md` Step 6 remains the canonical
  "did this actually work?" pass: `docker compose up --build` from a clean state.
- **Frontend dependency changes** you want to confirm behave in the Compose volume setup.
- **Parity with deploy** — the image is closer to what ships (`DEPLOYMENT.md`).

The venv loop is for speed while building; Compose is the source of truth for "it runs
clean from scratch."

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `could not translate host name "db"` on venv startup | `.env` still has `DATABASE_URL=...@db:5432` | Use `localhost:5432` (see `.env.example`), or `docker compose up -d db` and keep localhost |
| `connection refused` on `localhost:5432` | Postgres container not running | `docker compose up -d db` |
| `Address already in use` on `:8000`/`:3000` | Full Compose stack still up | `docker compose down` (keep `db`), or use `--port 8001` + matching `NEXT_PUBLIC_API_URL` |
| `ModuleNotFoundError` after startup | Deps not installed in the active venv | `.\venv\Scripts\activate` then `pip install -r requirements.txt` |
| `activate` blocked on Windows | PowerShell execution policy | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, or call `.\venv\Scripts\python.exe` directly |
| Frontend can't reach API (CORS / network) | `NEXT_PUBLIC_API_URL` mismatch | Match it to the backend port; restart `npm run dev` after changing env |

---

## Checklist

- [ ] `.env` present (from `.env.example`, `DATABASE_URL` → `localhost:5432`)
- [ ] `backend/venv` created, `requirements.txt` installed
- [ ] `frontend` `npm install` done
- [ ] Postgres reachable (`docker compose up -d db` → `pg_isready`)
- [ ] `alembic upgrade head` applied
- [ ] `uvicorn --reload` + `npm run dev` running; `/health` green
- [ ] `pytest` green from `backend/`
- [ ] Feature verified in the browser and persisted in Postgres
