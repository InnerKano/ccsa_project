# CCSA Frontend

Next.js 15 (App Router) client for the Credit Card Savings Analyzer. Consumes the FastAPI backend at `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

## Stack

- **Next.js 15** + **React 19**
- **Tailwind CSS v4** (CSS-first tokens in `app/globals.css`)
- **React Context** (`AuthProvider`) + **SWR** (authenticated reads)
- **TypeScript** strict mode

## Routes (Phase A)

| Route | Auth | Purpose |
|---|---|---|
| `/` | Public | Landing (SaaS hero — see `DESIGN.md` §2.2); redirects signed-in users to `/dashboard` |
| `/login`, `/register` | Guest only | Auth forms (`AuthLayout`) |
| `/dashboard` | Protected | Statement list, run/re-run analysis |
| `/upload` | Protected | CSV upload (`POST /api/statements`) |
| `/analysis/[id]` | Protected | Subscriptions, savings, recommendations |

Protected routes use client-side `RequireAuth` (JWT in `localStorage` — see `ARCHITECTURE.md` § Authentication).

## Where to look

| Topic | Document / path |
|---|---|
| Visual design (tokens, components, states) | [`DESIGN.md`](./DESIGN.md) — **read before any new screen** |
| API client & auth | [`lib/README.md`](./lib/README.md) |
| Feature components | [`components/README.md`](./components/README.md) |
| Architecture & folder rules | [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) § Frontend layout |
| Build & verify | [`workflows/implement-feature.md`](../workflows/implement-feature.md) Step 5–6 |

## Local development

From repo root (recommended):

```powershell
docker compose up --build
# → http://localhost:3000
```

The Compose `frontend` service runs `npm install && npm run dev` so the `frontend_node_modules` volume stays in sync with `package.json`.

Standalone (host Node — fast iteration alongside a venv backend):

```powershell
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL` in the repo `.env` if the API is not on `localhost:8000`. Full
venv + host Node dev loop (backend, migrations, tests): [`workflows/local-dev.md`](../workflows/local-dev.md).

## Phase A happy path

Register → upload `backend/fixtures/sample.csv` → dashboard → run analysis → view results → sign out → sign in → view results again. Full steps: root [`README.md`](../README.md) § Phase A happy path.
