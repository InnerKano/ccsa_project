# Frontend lib

Shared utilities and API layer. Feature screens import from here — not the other way around.

## Layout

```text
lib/
├── api/
│   ├── client.ts      # apiFetch + ApiError — all HTTP goes through this
│   ├── auth.ts        # register / login / forgot-password / reset-password
│   ├── statements.ts  # upload, list, get
│   └── analysis.ts    # run + list + get
│   └── exportAnalysisCsv.ts # export analysis as CSV
├── auth/
│   ├── session.ts        # token read/write (localStorage — single persistence seam)
│   ├── passwordPolicy.ts # NIST strength rules (D24) — mirror of backend password_policy.py
│   └── context.tsx       # AuthProvider / useAuth
├── theme/
│   ├── session.ts     # theme preference read/write (localStorage)
│   ├── resolve.ts     # light / dark / system → resolved theme + DOM apply
│   └── context.tsx    # ThemeProvider / useTheme
├── cn.ts              # className helper (clsx)
├── format.ts          # formatCurrency / formatDate (Decimal strings from API)
└── analysis/
    └── chartColors.ts # stable chart-1…8 mapping per category (spending comparison)
```

## Rules

- **One `lib/api/<feature>.ts` per backend module** — typed functions built on `apiFetch`.
- **Never pass the JWT manually** — `apiFetch` reads it from `session.ts` when `auth: true` (default).
- **Money:** API returns decimal strings; use `format.ts` at the display edge only.
- **Reads:** prefer SWR with named keys and typed fetchers from `lib/api/` (e.g. `useSWR("statements", listStatements)`). Invalidate with `mutate("statements")` after writes. See `implement-feature.md` Step 5.

See `workflows/implement-feature.md` Step 5, `docs/ARCHITECTURE.md` § Frontend layout, and [`frontend/README.md`](../README.md).
