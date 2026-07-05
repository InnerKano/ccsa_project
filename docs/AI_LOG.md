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

