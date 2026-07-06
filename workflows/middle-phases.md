# Workflow: Middle Phases (Post-Bootstrap Delivery Plan)

Bootstrap (`start-project.md` Steps 1–5) is complete. This document orders the remaining Must/Should Have work. It does not replace or duplicate `PROJECT_SCOPE.md` — it records execution order, dependencies, and phase boundaries so that is not re-derived on every session.

## Where this fits among existing docs

| Document | Role from here on |
|---|---|
| `PROJECT_SCOPE.md` | What to build (Must/Should/Could) — backlog |
| `REQUIREMENTS.md` | Why and strategic order (rules base first, AI layer second) |
| `DATA_MODEL.md` + `API.md` | Contracts per feature |
| `implement-feature.md` | How each piece gets built (1 feature = 1 cycle) |
| `AI_LOG.md` | AI usage evidence (video + evaluation) |
| `finish-project.md` | Closeout (deploy, video, checklist) |
| `middle-phases.md` (this doc) | Order and grouping of the remaining features |

## Status

- [x] Planning + docs
- [x] Scaffold + `/health`
- [x] Compose + Postgres
- [x] Alembic + `get_db`
- [x] Structure validated (bootstrap complete)
- [x] A1 — Auth (register/login, JWT, `users` migration, `get_current_user`) — **committed**
- [x] A2 — Statements (CSV upload + persistence) — **committed**
- [x] A2.1 — Ingestion hardening (modular parser: formats/locales/encoding, EN+ES, US/EU, debit-credit) — **committed**
- [x] A3 — Analysis L1 (rules: recurrence + categorization + savings + persistence) — **committed**
- [ ] A4 — Frontend vertical slice (login → upload → results dashboard) — **implemented, pending your audit of A4.6 docs / final Phase A sign-off**
  - [x] **A4.1** — Foundations + CORS (design system, API client, auth context, Compose npm sync) — **committed**
  - [x] **A4.2** — Auth screens on design system + protected routes + app shell — **committed**
  - [x] **A4.3** — Upload screen (`POST /api/statements`) — **committed**
  - [x] **A4.4** — Dashboard hub (`/dashboard` — list statements, run analysis) — **committed**
  - [x] **A4.5** — Results screen (`/analysis/[id]` — subscriptions, totals, recommendations) — **committed**
  - [ ] **A4.6** — Docs closeout (`middle-phases.md`, `implement-feature.md`, `ARCHITECTURE.md`, `README.md`, `frontend/README.md`, `frontend/DESIGN.md` cross-links) — **implemented, pending your audit/commit**
- [x] A5 — Sample CSV (synthetic `sample.csv` / `sample_es.csv`, shipped with A2/A2.1)
- [ ] Should Have (LLM, category summaries)
- [ ] Deploy + video

## Success criterion (from `PROJECT_SCOPE.md`)

register → upload CSV → see detected subscriptions and estimated savings → return later and find the analysis saved — **without depending on the LLM**.

This defines the boundary of Phase A.

## Feature dependency chain

```
auth ──► statements ──► analysis (Layer 1) ──► frontend (full flow)
                              │
                              └──► Layer 2 LLM (optional, later)
```

| Doing X before Y | Problem |
|---|---|
| `statements` before `auth` | No per-user isolation (Red zone, FinTech) |
| `analysis` before `statements` | No data to analyze |
| Full frontend before backend | Empty UI, nothing to demo |
| LLM before Layer 1 | If AI fails, there is no product (contradicts `REQUIREMENTS.md` §6) |

## Phase A — MVP (Must Have, no LLM)

Each delivery must leave something usable in the browser or via `curl`.

| # | Delivery | Module | Purpose | Visible result |
|---|---|---|---|---|
| A1 | Auth | `modules/auth/` | Identity + isolation | register/login, JWT, first migration (`users`) |
| A2 | Statements | `modules/statements/` | Product input | CSV upload → transactions persisted |
| A3 | Analysis L1 | `modules/analysis/` | Core of the product | rules → subscriptions + savings + persistence |
| A4 | Frontend vertical slice | `frontend/app/`, `frontend/lib/`, `frontend/components/` | End-to-end demo | login → upload → dashboard → results (see A4 sub-phases below) |
| A5 | Sample CSV | `backend/fixtures/` (or similar) | Mitigates risk #1 (format inconsistency) | testable without real data |

One `implement-feature.md` cycle per delivery (A1–A3 backend; **A4 is split into sub-phases A4.1–A4.5** because the frontend slice is large enough to audit incrementally; A5 rides along with A2).

**A4 — frontend vertical slice (sub-phases).** A4 is not a single throwaway UI pass: it follows the stack in `ARCHITECTURE.md` (Next.js + Tailwind CSS + React Context + SWR) and is delivered in auditable slices. Each sub-phase should leave something verifiable at http://localhost:3000 via `docker compose up --build` (see `implement-feature.md` Step 6).

| Sub | Scope | Touch points | Visible result |
|---|---|---|---|
| A4.1 | Foundations + CORS | `core/config.py` + `main.py` (CORS allow-list), `frontend/app/globals.css`, `frontend/lib/api/client.ts`, `frontend/lib/auth/`, `frontend/components/ui/`, `docker-compose.yml` (`npm install` on frontend startup) | Browser can call the API from `localhost:3000`; design tokens + UI primitives + shared API/auth layer compile |
| A4.2 | Auth UX | `app/login`, `app/register`, `app/page`, protected-route guard, app shell/header | Login/register on the design system; signed-in users reach `/dashboard` |
| A4.3 | Upload | `lib/api/statements.ts`, `app/upload` | CSV upload → `201` + redirect to dashboard |
| A4.4 | Dashboard | `lib/api/analysis.ts`, `app/dashboard` | List statements; run `POST /api/analysis/{statement_id}`; link to latest result |
| A4.5 | Results | `app/analysis/[id]`, `components/analysis/` | Render `detected_subscriptions`, `monthly_recurring_total`, `estimated_savings`, `recommendations` |
| A4.6 | Docs closeout | `workflows/`, `README.md`, `ARCHITECTURE.md`, `frontend/README.md` | Workflows and READMEs reflect how A4 was actually built; `DESIGN.md` linked as UI source of truth |

Commit convention for A4: **one commit per sub-phase** (e.g. `Add frontend foundations and CORS (A4.1)`), same imperative style as backend deliveries. A4.6 is docs-only.

**A2.1 — ingestion hardening (inserted between A2 and A3).** After A2 shipped a working upload against an idealized CSV, real bank exports (see `backend/fixtures/` real samples) showed the contract was too optimistic: different delimiters, languages (EN/ES), date orientations, decimal styles (US `1,234.56` vs LatAm `1.234,56`), sign conventions, and encodings. A2.1 refactors parsing into a **pluggable pipeline** (`modules/statements/ingest/`) that handles delimited exports robustly and leaves PDF/statement-dump parsing as a future adapter (D15). This is a scoped realism pass, not scope creep — it keeps the MVP usable by real users without chasing per-bank PDF parsing.

Touch points:
- Backend: `modules/<feature>/`, `core/models.py`, `main.py` (router registration), `API.md`
- Frontend: routes under `app/`, client in `lib/api/`, feature components in `components/<feature>/`, primitives in `components/ui/`, visual rules in `frontend/DESIGN.md`
- DB: migration ships **with** the model (auth brings the first one)

Commit convention: one commit per feature, with an imperative summary matching the repo history (`Add auth module ...`, `Add statements module ...`) — no `feat(scope):` prefix.

**Phase A exit:** a test user completes the full flow on Layer 1 only. This is the point at which a first video draft can be recorded.

## Phase B — Should Have

Starts only once Phase A is stable and time allows.

| # | Delivery | Purpose |
|---|---|---|
| B1 | `shared/llm/` + Layer 2 | AI enrichment with fallback (D2) |
| B2 | Category summaries | Richer UI |
| B3 | Deploy smoke test | Public demo (`DEPLOYMENT.md`) — CORS allow-list is wired in A4.1; production adds the Vercel origin to `CORS_ORIGINS` |

Constraint: `LLM_ENABLED=false` must keep producing the same result as the end of Phase A.

## Phase C — Close (`finish-project.md`)

- Full happy-path test coverage
- Deploy frontend + backend + DB
- `AI_LOG.md` updated
- 10-minute video, scripted from scope + log

## Applying `implement-feature.md` within each phase

The workflow itself does not change — one feature at a time:

```
Plan (API.md + DATA_MODEL.md)
  → migration (if new models)
  → backend (full module)
  → tests (happy path)
  → frontend (minimal screen)
  → API.md + AI_LOG.md
  → commit
```

Notes specific to this stretch:
- A1 (auth): backend first; a minimal login form shipped in the same cycle — JWT verified before A4.
- A3 (analysis): the densest backend delivery; no LLM mixed in — rules only (`REQUIREMENTS.md` §6).
- A4: delivered as **A4.1–A4.5** (see table above). Stack matches `ARCHITECTURE.md` (Tailwind + Context + SWR). MVP goal is a working end-to-end flow, not pixel-perfect polish — but the foundation is modular so later UI work extends `components/ui/` and `lib/api/` rather than rewriting screens.

## Cross-cutting concerns (live inside features, not as separate deliveries)

| Concern | When | Where |
|---|---|---|
| JWT + password hashing (bcrypt) | A1 | `core/security.py` or `modules/auth/services.py` |
| CORS | A4.1 (browser calls API) | `main.py` / `core/config` — `CORS_ORIGINS` comma-separated allow-list, never `*` |
| `get_current_user` dependency | A1 | reused in statements/analysis |
| Per-user scoping in queries | A2, A3 | each module's `services.py` |
| Synthetic sample CSV | A2 or A5 | no real PII |

## Explicit exclusions for this stretch

- No new `docs/PHASES.md` — ordering lives in `PROJECT_SCOPE.md` + this workflow
- Plaid, PDF parsing, multi-currency (Won't/Could Have — see `PROJECT_SCOPE.md`)
- Microservices, RBAC, caching (`PROJECT_SCOPE.md` secondary list)
- Infra refactors unless something breaks Compose or tests

## Next step

**Phase A browser MVP is complete** (A1–A4.5 committed). Finish **A4.6 docs closeout** audit/commit, then record a first video draft (`finish-project.md`) or start **Phase B** (LLM Layer 2) if time allows. Deploy smoke test (B3) can run in parallel with Phase B planning.

**Phase A verification** (browser, no LLM): register → upload `backend/fixtures/sample.csv` → dashboard → run analysis → view subscriptions + savings on `/analysis/{id}` → sign out → sign in → view results again. See `README.md` § Phase A happy path and `implement-feature.md` Step 6.
