# AI Log

Record of AI usage in the project. This file is filled in whenever AI contributes something non-trivial (Yellow/Red zone or architectural decisions), according to the `AI_RULES.md` protocol.

It is the direct input for answering in the video: "where did AI help most? where did it fail?" with real evidence instead of memory.

## Format

```
YYYY-MM-DD | [module] | What was asked | Usefulness (1-5) | What was fixed manually
```

## Entries

| Date | Module | What was asked | Usefulness (1-5) | Manual correction |
|---|---|---|---|---|
| 2026-07-04 | architecture | Create the initial backend/frontend folder structure and decide which placeholder modules to keep | 4 | Kept the scaffold minimal and avoided premature feature-specific files; only the core structure and entrypoint were preserved. |
| 2026-07-04 | backend | Step 2.1 walking skeleton: FastAPI app, GET /health, requirements.txt, Dockerfile | 5 | No corrections needed; health endpoint matches API.md contract, no DB/CORS yet (deferred to Steps 3–4). |
| 2026-07-05 | backend | Add pytest health test + README run/test instructions | 5 | Clarified single test suite for venv and Docker; no duplicate e2e for Step 2.1. |
| 2026-07-05 | infra | Step 3 Docker Compose: backend + frontend + Postgres, core/config + database wiring | 5 | DB check on startup in Compose; SKIP_DB_CHECK for pytest/venv-only; no migrations yet (Step 4). |
| 2026-07-05 | database | Step 4 Alembic wiring: env.py, get_db(), core/models registry; no feature tables | 5 | First migration deferred to auth feature per DATA_MODEL.md; no empty revisions. |
| 2026-07-05 | architecture | Step 5 validate structure: module stubs, test_structure, docs alignment, D11 | 5 | ARCHITECTURE tree updated to match disk; bootstrap complete, next = auth. |
| 2026-07-05 | auth | A1 auth module: User model, bcrypt/JWT, register/login, first migration, integration tests, minimal login/register UI | 4 | Switched from passlib to direct bcrypt (bcrypt 5.x incompatibility); pending Red-zone review before commit. |
| 2026-07-05 | statements | A2 statements module: CSV parse in memory, Statement/Transaction models, migration, per-user CRUD, sample.csv fixture, integration + unit tests | 4 | Pending Red-zone review (per-user isolation, no sensitive data in errors); no frontend upload UI yet (A4). |
| 2026-07-05 | statements | A2.1 ingestion hardening: analyze real bank exports vs idealized CSV, design pluggable `ingest/` pipeline (formats/locales/encoding, EN+ES, US/EU, debit-credit), synthetic ES fixture, D15 | 4 | Kept PDF/statement-dump parsing out of MVP (scope/Risk #3); flagged PII in real fixtures → gitignored, only synthetic samples versioned; refined REQUIREMENTS assumption via D15 (not by rewriting REQUIREMENTS). |
| 2026-07-05 | testing | Fix cross-run test isolation for DB-backed suites | 5 | Root cause: app-level commit() leaked past the outer transaction; fixed with SQLAlchemy `join_transaction_mode="create_savepoint"` in auth + statements conftests. |
| 2026-07-05 | analysis | A3 analysis module (Layer 1, rules-only): recurrence detection, bilingual categorization, savings + recommendations, `analyses`/`detected_subscriptions`/`recommendations` models + migration, per-user isolation, POST/GET endpoints, unit + integration tests | 4 | Defined explainable rule thresholds by hand (≥2 months, 25% amount spread) and a discretionary-only savings heuristic (D16) instead of flagging all recurring charges; kept LLM out (rules-only, D2) leaving a documented Layer 2 seam; pending Red-zone review (per-user scoping on analysis + no sensitive data in errors). |
| 2026-07-05 | frontend | A4.1 foundations: CORS allow-list (`CORS_ORIGINS`), Tailwind v4 design tokens, `components/ui/` primitives, shared `apiFetch` client, `AuthProvider` + SWR, Compose `npm install` on frontend startup | 4 | Red-zone: reviewed CORS config (no `*`, explicit origins). Yellow: reconciled `middle-phases.md` with `ARCHITECTURE.md` frontend stack (Tailwind + SWR + Context, not inline-only MVP). Login/register screens still pre-design-system until A4.2. |
| 2026-07-05 | frontend | A4.2 auth UX: login/register on design system, `GuestOnly`/`RequireAuth`, `AppShell`, landing page, protected `/dashboard` | 4 | Migrated forms to `useAuth()` (no direct `saveToken` in pages); client-side guards only (JWT in localStorage — no middleware). Nav items extended in A4.3+ via `AppShell` `NAV_ITEMS`. |
| 2026-07-05 | frontend | Author `frontend/DESIGN.md` — design system & UX/UI guide (principles, tokens, component/layout catalog, state & a11y conventions, future recommendations) reverse-documented from the A4.1–A4.2 implementation | 4 | Documented only what is actually built (tokens/components verified against source); recommended future items kept as "not yet built" to avoid scope creep; linked from ARCHITECTURE.md, implement-feature.md, components README as the UI source of truth. |
| 2026-07-05 | frontend | A4.3 upload: `lib/api/statements.ts`, `/upload` + `StatementUploadForm` (multipart POST, currency, advanced mapping in `<details>`), `AppShell` nav, dashboard upload success feedback | 4 | Included `listStatements()` in API module for A4.4 reuse; client validates extension only (parse errors from API `detail`); no raw file content in UI/errors. |
| 2026-07-06 | frontend | A4.4 dashboard: `lib/api/analysis.ts`, SWR statement/analysis lists, run/re-run analysis, `StatementCard`/`StatementList`, `/analysis/[id]` headline KPIs | 4 | Latest analysis per statement via map on DESC-ordered list (D10); redirect to `/analysis/{id}` after POST; full subscription UI deferred to A4.5 on same route. |
| 2026-07-06 | frontend | A4.5 results: `AnalysisDetailView`, `SubscriptionList`, `RecommendationList`, currency from `getStatement`, empty states (D16 copy) | 4 | Composable `components/analysis/` per DESIGN.md; closes Phase A browser flow (upload → analyze → view subscriptions + savings + recommendations). |
| 2026-07-06 | docs | A4.6 closeout: align `middle-phases.md`, `implement-feature.md` (A4 sub-phases, SWR pattern, Phase A happy path), `ARCHITECTURE.md` frontend tree, root `README.md`, new `frontend/README.md` | 5 | Docs now reflect how A4 was actually built (not aspirational); `DESIGN.md` remains UI source of truth; Phase A marked complete pending A4.6 commit. |

