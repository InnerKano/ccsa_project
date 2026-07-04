# Requirements — Credit Card Savings Analyzer (CCSA)

Pre-code thought document. If anything changes halfway through the project, record it in `DECISIONS.md`; do not rewrite the history here.

This document answers *why* and *what*. The *technical how* should be resolved in `ARCHITECTURE.md` and `DECISIONS.md` — it is not repeated here.

---

## 1. Problem interpretation

- **What is the real problem?** Most people do not know how much they spend each month on recurring charges and subscriptions. The card statement contains the information, but it is in a flat format (tens or hundreds of lines) that no one sits down to audit. Money is lost not because of lack of data, but because of lack of *actionable visibility* into that data.
- **Why is this a problem today?** Without a tool, detecting "I'm paying for 4 subscriptions I don't use" requires manually reading the statement, recognizing repeated merchant patterns, and calculating totals by hand. It is tedious, so it does not get done, and the leaks become permanent.
- **Who is it for?** An individual consumer (not a business) who wants to understand and reduce recurring spending. Not a bookkeeper or analyst: they expect to upload a file and receive clear conclusions, not another spreadsheet.

## 2. Constraints

- Time: 72 hours from project start.
- Team: one person.
- Stack: as defined in `ARCHITECTURE.md` (FastAPI + Next.js + PostgreSQL), unless a strong reason is documented in `DECISIONS.md`.
- Deliverable: repo + working deployment + video up to 10 minutes.

_Project-specific constraints:_

- **Sensitive data (FinTech):** financial transactions are handled. Even if test data is used, handling must demonstrate awareness of privacy/PII (direct evaluation criterion from the brief).
- **No access to real banking data:** there is no bank or aggregator integration in production within the timeframe. The input is a file that the user exports themselves.
- **The LLM cannot be the only path:** AI integration is subject to rate limits, inconsistent prompts, and provider changes. The product must deliver value even if the AI layer fails.

## 3. Assumptions

**Project assumptions**

- The user can export transactions to **CSV** from their bank (most banks allow this). A single format is not assumed: the system requests a minimal column mapping (date, description, amount).
- A monthly statement typically contains tens to a few hundred transactions — a volume that can be processed in memory without streaming or async jobs.
- Subscriptions are recognized by **recurrence** (same/similar merchant, stable amount, monthly cadence) plus a dictionary of known merchants (Netflix, Spotify, etc.).
- The user accepts that recommendations are indicative, not formal financial advice.

## 4. Risks

Ranked by probability × impact.

1. Inconsistent CSV formats across banks
   - Impact: parsing may fail or columns may map incorrectly, producing wrong data.
   - Mitigation: require explicit column mapping during upload, validate the CSV, and provide an example in the repo.

2. LLM layer fails or is delayed (rate limits, prompts)
   - Impact: lack of "intelligent" recommendations during the demo or use.
   - Mitigation: graceful degradation: a rules-based base layer that detects recurring charges and estimates savings without relying on AI.

3. Scope over-engineering (two layers, PDF, auto-cancellation)
   - Impact: the MVP may not be reached within the timeframe due to excessive features.
   - Mitigation: freeze scope in `PROJECT_SCOPE.md` and move extras to "Won't/Could Have".

4. Sensitive data leakage in logs/errors/repo
   - Impact: loss of trust and failure on security criteria.
   - Mitigation: do not persist the raw file, avoid logging transactions, keep `.env` out of version control, and isolate data per user.

5. LLM provider cost or latency in the demo
   - Impact: slow demo or quota failures.
   - Mitigation: design a provider-agnostic integration (Ollama local / OpenAI) configurable via `.env`, with timeouts and fallback to rules.

## 5. Open questions

_What I would ask the team if available, and what I assumed instead._

- Is multi-currency support expected? → **Assume a single currency per statement** (the currency in the CSV), without conversion.
- Should recommendations include the action to cancel? → **Assume no**: it recommends and explains; cancellation is performed by the user (see "Won't Have").
- Should analysis history be saved? → **Assume yes**, tied to the user's account, because the brief asks for "saved results" and it provides value for month-to-month tracking.

## 6. Chosen approach

_Summary_

- First build a **valuable base without AI** (upload CSV → detect recurring/subscriptions by rules → estimated savings in a dashboard).
- Then add an optional AI layer that enriches the results with finer categorization and natural-language recommendations.
- Prioritize a deliverable MVP with graceful degradation and a strong security story; if a real risk arises, consciously sacrifice PDF parsing, aggregator integration, and automatic cancellation.

---

**Next step:** complete `docs/PROJECT_SCOPE.md` → "Project Scope" section using this document as input. Only after both are ready create the code scaffold (see `workflows/start-project.md`).
