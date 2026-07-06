# UI components

Reusable, presentation-only building blocks. Feature screens in `app/` compose these — they do not embed one-off styles for patterns that repeat.

## Layout

```text
components/ui/
├── Alert.tsx       # inline status (error / info / success)
├── Button.tsx      # variants + loading state; export buttonClass for Link-as-button
├── Card.tsx        # Card, CardHeader, CardContent, CardTitle
├── Input.tsx       # Input + Field (label, hint, error)
├── Spinner.tsx
└── index.ts        # barrel export
```

## Rules

- Primitives use Tailwind utility classes backed by semantic tokens in `app/globals.css` (`@theme`).
- No business logic or API calls here — only props in, JSX out.
- New shared patterns (e.g. a data table for subscriptions) land here or in `components/<feature>/` once a second screen needs them.

See `docs/ARCHITECTURE.md` § Frontend layout.
