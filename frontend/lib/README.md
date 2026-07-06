# Frontend lib

Shared utilities and API layer. Feature screens import from here — not the other way around.

## Layout

```text
lib/
├── api/
│   ├── client.ts      # apiFetch + ApiError — all HTTP goes through this
│   ├── auth.ts        # register / login
│   ├── statements.ts  # upload + list
│   └── analysis.ts    # run + list + get
├── auth/
│   ├── session.ts     # token read/write (localStorage — single persistence seam)
│   └── context.tsx    # AuthProvider / useAuth
├── cn.ts              # className helper (clsx)
└── format.ts          # formatCurrency / formatDate (Decimal strings from API)
```

## Rules

- **One `lib/api/<feature>.ts` per backend module** — typed functions built on `apiFetch`.
- **Never pass the JWT manually** — `apiFetch` reads it from `session.ts` when `auth: true` (default).
- **Money:** API returns decimal strings; use `format.ts` at the display edge only.
- **Reads:** prefer SWR with the default fetcher wired in `app/providers.tsx`.

See `workflows/implement-feature.md` Step 5 and `docs/ARCHITECTURE.md` § Frontend layout.
