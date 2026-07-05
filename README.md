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

> **Current phase: planning.** This commit contains design documentation (`docs/`) and the working process (`workflows/`) only; there is no application code yet. The scaffold and features will be added in subsequent commits following `workflows/start-project.md`.

## Local setup (once the scaffold exists)

You will likely need to create a `.env` file with real values for the application. For more advanced setups, consider environment-specific configurations so you can switch easily between development, testing, and production.

```bash
cp .env.example .env      # edit real values (includes LLM provider)
docker-compose up
docker-compose exec backend alembic upgrade head
```

- Frontend → http://localhost:3000
- API + docs → http://localhost:8000/docs
- Health check → `curl http://localhost:8000/health` → {"status": "healthy"}

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

