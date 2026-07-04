# Workflow: Start a Project

## Step 1: Complete planning (Commit 1 — no code)

1. **`docs/REQUIREMENTS.md`** — problem interpretation, constraints, assumptions, risks, and chosen approach.
2. **`docs/PROJECT_SCOPE.md`** — Must/Should/Could/Won't Have, derived from `REQUIREMENTS.md`.
3. **`docs/ARCHITECTURE.md`** — explain why the project is organized this way (structure, stack, modular backend) before creating any folders.
4. **`docs/DECISIONS.md`, `docs/AI_RULES.md`** — remaining technical and process planning.
5. **`workflows/*.md`** — how the team will work going forward.

## Step 2: Create the structure (Commit 2 — code, no business logic)

Complete the architectural analysis for backend and frontend before creating the project structure.

## Step 3: Start services

Bring up the Docker services for local development.

## Step 4: Database

Design the database and run the required migrations.

## Step 5: Validate the structure

Verify that this initial layout matches the monolithic-modular vision of the project; if not, make necessary adjustments.

Initial recommended structure:
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
