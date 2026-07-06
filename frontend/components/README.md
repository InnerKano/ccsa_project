# UI components

Reusable, presentation-only building blocks. Feature screens in `app/` compose these — they do not embed one-off styles for patterns that repeat.

## Layout

```text
components/
├── auth/
│   ├── RequireAuth.tsx   # redirect to /login when unauthenticated
│   └── GuestOnly.tsx     # redirect to /dashboard when already signed in
├── layout/
│   ├── AppShell.tsx      # authenticated header + nav + main
│   └── AuthLayout.tsx    # centered card shell for login/register
└── ui/                   # primitives (Button, Field, Card, …)
```

## Rules

- Primitives use Tailwind utility classes backed by semantic tokens in `app/globals.css` (`@theme`).
- No business logic or API calls here — only props in, JSX out.
- New shared patterns (e.g. a data table for subscriptions) land here or in `components/<feature>/` once a second screen needs them.

See `docs/ARCHITECTURE.md` § Frontend layout.
