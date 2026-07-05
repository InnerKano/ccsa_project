# Deployment Guide — CCSA

## Overview

Deploy the Credit Card Savings Analyzer to a production environment suitable. Target: Vercel (frontend) + Railway or Render (backend + PostgreSQL).

## Pre-deployment checklist

- [ ] All tests passing on the happy path (upload → analyze → view results)
- [ ] Environment variables configured (including LLM provider if Layer 2 is enabled)
- [ ] Database migrations tested against a remote PostgreSQL instance
- [ ] `docs/API.md` matches the live endpoints
- [ ] Frontend builds successfully (`npm run build`)
- [ ] No secrets or sample CSVs with real PII in the repository
- [ ] Git history is clean and readable

## Frontend (Vercel)

### Prerequisites

- Vercel account
- GitHub repository connected

### Steps

1. **Push code to GitHub**
   ```bash
   git push origin main
   ```

2. **Connect to Vercel**
   - Import the repository at vercel.com
   - Root directory: `frontend/`
   - Build command: `npm run build`
   - Output directory: `.next`

3. **Environment variables**
   - `NEXT_PUBLIC_API_URL` → production backend URL (e.g. `https://ccsa-api.onrender.com`)

4. **Deploy**
   - Vercel auto-deploys on push to `main`

Production URL: `your-project.vercel.app`

## Backend (Railway or Render)

### Railway

1. Create a new project and connect the GitHub repository
2. Add a **PostgreSQL** plugin
3. Set the service root to `backend/`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Copy environment variables from `.env.example` (see below)

### Render

1. Create a **Web Service** connected to GitHub
2. Root directory: `backend/`
3. Build: `pip install -r requirements.txt`
4. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add a managed PostgreSQL instance and wire `DATABASE_URL`

## Database

1. Use the managed PostgreSQL from Railway/Render
2. Run migrations before the first deploy or as a release step:
   ```bash
   alembic upgrade head
   ```
3. Verify: `GET /health` returns `{"status": "healthy"}`

## Environment configuration

### Backend (production)

```
DATABASE_URL=postgresql://user:pass@host:5432/ccsa
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<strong-random-key>
CORS_ORIGINS=https://your-project.vercel.app

# LLM — Layer 2 (optional; Layer 1 works without these)
LLM_PROVIDER=openai          # or ollama
LLM_API_KEY=<key-if-openai>
LLM_BASE_URL=http://localhost:11434   # only if using Ollama remotely
LLM_ENABLED=true             # set false to ship rules-only analysis
```

### Frontend (production)

```
NEXT_PUBLIC_API_URL=https://your-backend-url
```

## Post-deploy verification

```bash
curl https://your-backend-url/health
# → {"status": "healthy"}
```

Manual smoke test on the deployed URL:

1. Register / log in
2. Upload a sample CSV (use synthetic data, not real statements)
3. Run analysis and confirm results render
4. Confirm error responses do not leak transaction content

## Rollback

```bash
git revert <commit-hash>
git push origin main
```

Both Vercel and Railway/Render redeploy automatically on push.

## Common issues

**Backend connection refused**
Wrong `DATABASE_URL` or DB not provisioned.

**Frontend API errors**
`NEXT_PUBLIC_API_URL` mismatch or CORS not set to Vercel domain.

**Analysis returns `ai_enabled: false` only**
LLM env vars missing or provider unreachable — expected fallback; verify Layer 1 still works.

**Migration failures**
Run `alembic upgrade head` manually; check logs.

## Security checklist (non-negotiable for financial data)

- [ ] HTTPS on both frontend and backend
- [ ] Secrets only in platform env vars, never in code
- [ ] CORS restricted to the Vercel origin (not `*`)
- [ ] JWT auth enforced on `/api/statements` and `/api/analysis`
- [ ] Raw CSV files are not persisted (only normalized transactions)
- [ ] Error responses do not expose stack traces or statement content in production
