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
- [x] A1 — Auth (register/login, JWT, `users` migration, `get_current_user`) — **pending your audit/commit**
- [ ] A2 — Statements (CSV upload + persistence) — **implemented, pending audit/commit**
- [ ] A2.1 — Ingestion hardening (modular parser: formats/locales/encoding, EN+ES, US/EU, debit-credit) — **implemented, pending audit/commit**
- [ ] Should Have (LLM, sample CSV, category summaries)
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
| A4 | Frontend vertical slice | `frontend/app/`, `lib/api/` | End-to-end demo | login → upload → results dashboard |
| A5 | Sample CSV | `backend/fixtures/` (or similar) | Mitigates risk #1 (format inconsistency) | testable without real data |

One `implement-feature.md` cycle per delivery (A1–A3 backend; A4 integrated frontend; A5 rides along with A2).

**A2.1 — ingestion hardening (inserted between A2 and A3).** After A2 shipped a working upload against an idealized CSV, real bank exports (see `backend/fixtures/` real samples) showed the contract was too optimistic: different delimiters, languages (EN/ES), date orientations, decimal styles (US `1,234.56` vs LatAm `1.234,56`), sign conventions, and encodings. A2.1 refactors parsing into a **pluggable pipeline** (`modules/statements/ingest/`) that handles delimited exports robustly and leaves PDF/statement-dump parsing as a future adapter (D15). This is a scoped realism pass, not scope creep — it keeps the MVP usable by real users without chasing per-bank PDF parsing.

Touch points:
- Backend: `modules/<feature>/`, `core/models.py`, `main.py` (router registration), `API.md`
- Frontend: routes under `app/`, client in `lib/api/`, minimal components
- DB: migration ships **with** the model (auth brings the first one)

Commit convention: one commit per feature (`feat(auth): ...`, `feat(statements): ...`).

**Phase A exit:** a test user completes the full flow on Layer 1 only. This is the point at which a first video draft can be recorded.

## Phase B — Should Have

Starts only once Phase A is stable and time allows.

| # | Delivery | Purpose |
|---|---|---|
| B1 | `shared/llm/` + Layer 2 | AI enrichment with fallback (D2) |
| B2 | Category summaries | Richer UI |
| B3 | CORS + deploy smoke test | Public demo (`DEPLOYMENT.md`) |

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
- A1 (auth): backend first; a minimal login form ships in the same cycle or immediately after — JWT gets verified before A4.
- A3 (analysis): the densest delivery; no LLM mixed in here — rules only (`REQUIREMENTS.md` §6).
- A4: two screens (upload + results) satisfy the Must Have; UI polish is not a goal at this stage.

## Cross-cutting concerns (live inside features, not as separate deliveries)

| Concern | When | Where |
|---|---|---|
| JWT + password hashing (bcrypt) | A1 | `core/security.py` or `modules/auth/services.py` |
| CORS | A4 (frontend calls the API) | `main.py` / `core/config` |
| `get_current_user` dependency | A1 | reused in statements/analysis |
| Per-user scoping in queries | A2, A3 | each module's `services.py` |
| Synthetic sample CSV | A2 or A5 | no real PII |

## Explicit exclusions for this stretch

- No new `docs/PHASES.md` — ordering lives in `PROJECT_SCOPE.md` + this workflow
- No Tailwind/CSS polish before the flow works end-to-end
- Plaid, PDF parsing, multi-currency (Won't/Could Have — see `PROJECT_SCOPE.md`)
- Microservices, RBAC, caching (`PROJECT_SCOPE.md` secondary list)
- Infra refactors unless something breaks Compose or tests

## Next step

**A3 — analysis (Layer 1, rules)**, via `implement-feature.md`, after A2 + A2.1 are audited and committed. A3 must be **bilingual-ready** in its category/merchant rules (EN + ES keywords), since ingestion now accepts both. Then A4 in order, each with a verifiable demo. LLM work starts only once Phase A meets the success criterion. Documentation updates during this stretch are limited to `API.md`, `AI_LOG.md`, and `DECISIONS.md` (only for non-obvious changes) — no new docs beyond this one.
