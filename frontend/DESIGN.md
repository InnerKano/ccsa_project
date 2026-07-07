# CCSA Frontend — Design System & UX/UI Guide

The single source of truth for **how the CCSA frontend looks and behaves**. Any new screen or component must follow this document so the product stays visually and behaviorally consistent as it scales. If a change here is intentional, update this file in the same commit — the guide must always reflect what is actually on screen (same discipline as `docs/DECISIONS.md`).

> Scope: frontend visual/interaction design only. Architecture and data flow live in [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) (§ Frontend layout); the build workflow is [`workflows/implement-feature.md`](../workflows/implement-feature.md) Step 5.

---

## 1. Design principles

CCSA is a **personal-finance (FinTech) tool**. The design serves trust and clarity, not decoration.

1. **Trust through restraint.** A calm, neutral canvas with a single confident accent. No gradients-for-the-sake-of-it, no visual noise around money figures. Financial data must read as credible.
2. **Clarity over cleverness.** The user uploads a statement to get *answers* (subscriptions, savings). Every screen states what it is and what to do next in plain language.
3. **Progressive disclosure.** Show the essential result first (totals, detected subscriptions); detail is one level deeper. Never dump raw data.
4. **Consistent, reusable primitives.** Screens compose from `components/ui/`. If a pattern appears twice, it becomes a component — screens never hand-roll one-off styles for shared patterns.
5. **Accessible by default.** Labeled inputs, visible focus rings, semantic roles, adequate contrast. Accessibility is part of "done", not a later pass.
6. **Graceful states.** Every async surface has a loading, empty, and error state. The product never shows a blank or a raw stack trace (mirrors the backend's graceful-degradation ethos, `REQUIREMENTS.md` §6).
7. **Privacy-aware copy.** Wording reinforces the data promise ("your raw file is never stored"). Never render sensitive detail where it isn't needed (`docs/DATA_MODEL.md`).

---

## 2. Foundation: design tokens

All visual constants live as **Tailwind v4 CSS-first tokens** in [`app/globals.css`](./app/globals.css) under `@theme`. Components consume them only through Tailwind utilities (`bg-brand-600`, `text-muted`, `border-border`) — never hard-coded hex values in components. This is what makes a future theme (e.g. dark mode) a token change, not a component rewrite.

### 2.1 Color

**Brand — emerald.** The accent color. Emerald reads as "savings / positive / money kept" — deliberate for this product. Used for primary actions, active nav, links, and positive emphasis. Not used as a large background fill.

| Token | Hex | Primary use |
|---|---|---|
| `brand-50` | `#ecfdf5` | Tinted backgrounds (active nav, success alert) |
| `brand-200` | `#a7f3d0` | Success alert border |
| `brand-500` | `#10b981` | Input focus border |
| `brand-600` | `#059669` | **Primary button**, focus ring |
| `brand-700` | `#047857` | Primary button hover, links, logo |
| `brand-800` | `#065f46` | Active nav text, success alert text |

**Neutral — slate.** The canvas and text. This is where 90% of the UI lives.

| Token | Hex | Use |
|---|---|---|
| `background` | `#f8fafc` | Page background |
| `surface` | `#ffffff` | Cards, header, inputs |
| `surface-muted` | `#f1f5f9` | Secondary button, subtle fills, info alert |
| `border` | `#e2e8f0` | All borders / dividers |
| `foreground` | `#0f172a` | Primary text |
| `muted` | `#64748b` | Secondary text, hints, placeholders |

**Status.** Reserved for meaning — never decorative.

| Token | Hex | Use |
|---|---|---|
| `danger` / `danger-bg` | `#dc2626` / `#fef2f2` | Errors, destructive actions |
| `warning` | `#d97706` | Cautions (e.g. essential recurring charges not flagged for cancellation) |
| `success` / `success-bg` | `#059669` / `#ecfdf5` | Confirmations |

**Color rules:**
- One accent. Do not introduce a second brand hue. Differentiate with neutrals + weight, not new colors.
- Money: render amounts in `foreground`. Reserve `success`/`danger` for *directional* meaning (e.g. estimated savings positive, an overspend), not for every number.
- Status colors require a non-color cue too (icon, label) — never rely on color alone (accessibility).

### 2.1.1 Dark theme

Dark mode is implemented via **`[data-theme="dark"]` on `<html>`** — semantic tokens in `globals.css` are overridden; components keep using the same Tailwind utilities (`bg-surface`, `text-foreground`, etc.).

| Mechanism | Location |
|---|---|
| Token overrides | `app/globals.css` → `[data-theme="dark"]` block |
| Preference storage | `lib/theme/session.ts` (`ccsa_theme` in `localStorage`) |
| React state | `lib/theme/context.tsx` (`ThemeProvider` in `app/providers.tsx`) |
| Anti-flash | Inline `beforeInteractive` script in `app/layout.tsx` (mirrors `resolve.ts`) |
| Toggle control | `components/ui/ThemeToggle.tsx` in `AppShell`, `AuthLayout`, landing |

**Preference values:** `light` · `dark` · `system` (default — follows `prefers-color-scheme`). The header toggle sets an explicit `light` or `dark` choice. Brand tints (`brand-50`, `brand-700`, …) are also overridden in dark so nav active states and ghost buttons stay legible.

### 2.2 Typography

- **Family:** system UI stack (`--font-sans`). No web-font network dependency → fast, robust in Docker/offline, native feel. `--font-mono` is available for figures/IDs if a monospace column ever helps scanning.
- **Scale (Tailwind):** `text-xs` hints · `text-sm` body/controls · `text-base` card titles · `text-lg` section/header brand · `text-2xl` page titles · `text-4xl`/`sm:text-5xl`/`lg:text-6xl` landing hero · `text-lg` landing description · `text-sm` trust note.
- **Landing hero (SaaS pattern):** centered block inside `max-w-3xl` (~672px). Hierarchy top → bottom:
  1. **Eyebrow** — product name, uppercase, `text-xs sm:text-sm font-medium tracking-[0.2em] text-muted` (brand present, low visual weight).
  2. **`h1`** — value proposition, `text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight`; **one** brand-accent word only (`text-brand-700` on “money”).
  3. **Description** — `text-lg text-muted max-w-xl` (~576px), `leading-relaxed`.
  4. **CTAs** — centered row, `gap-4` (16px), primary + secondary via `buttonClass`.
  5. **Trust note** — `text-sm text-muted`, `mt-10 sm:mt-12` (40–48px above).
- **Weight:** `font-medium` for labels/controls/nav/eyebrow, `font-semibold` for in-app page titles, `font-bold` for landing `h1` only. Body stays regular.
- **Color pairing:** titles/body in `foreground`; supporting text in `muted`.

### 2.3 Spacing, radius, elevation

- **Spacing:** Tailwind 4px scale. Vertical rhythm within a group via `space-y-4` (forms) / `space-y-6` (page sections). Card padding is standardized by `CardContent` (`px-6 py-5`).
- **Radius:** `rounded-lg` for controls (buttons, inputs, alerts); `--radius-card` (`0.875rem`) for cards. Consistent corner language.
- **Elevation:** `shadow-sm` only, on cards. The design is flat and border-driven; avoid heavy shadows.

### 2.4 Focus & motion

- **Focus:** global `:focus-visible` ring (2px `brand-600`, 2px offset) on all interactive elements — do not remove it.
- **Motion:** `transition-colors` on hover/focus state changes. Only spinners animate (`animate-spin`). No decorative motion.

---

## 3. Layout & responsiveness

- **Containers:** authenticated content is centered at `max-w-5xl`; auth screens at `max-w-md`; landing hero at `max-w-3xl` (centered, `text-center`). Description and trust note cap at `max-w-xl` (~576px). Horizontal page padding `px-4`.
- **Header height:** `h-14` in `AppShell`, `py-4` brand bar in `AuthLayout` and landing. Public headers (`/`, login, register) share the same bar: `border-b border-border bg-surface px-4 py-4`, inner row `flex items-center justify-between gap-4` — **full viewport width**, not capped to the hero container.
- **Mobile-first:** default styles target small screens; layer `sm:`/`lg:` up. Everything must be usable at 360px wide. Landing hero scales `text-4xl → sm:text-5xl → lg:text-6xl`; vertical padding `py-20 sm:py-28` for generous whitespace.
- **Full height:** page shells use `min-h-dvh` (dynamic viewport height — correct on mobile browsers).

---

## 4. Component catalog (`components/ui/`)

Import from the barrel: `import { Button, Field, Card, Alert, Spinner } from "@/components/ui";`

### Button
- **Variants:** `primary` (brand, main action — one per view), `secondary` (bordered, neutral), `ghost` (text-only, low emphasis — e.g. Sign out), `danger` (destructive).
- **Sizes:** `md` (default, `h-11`), `sm` (`h-9`, dense areas like the header).
- **Loading:** `loading` shows a spinner and disables the button — always use it for async submits so double-submit is impossible.
- **Links as buttons:** use `buttonClass(variant, size)` on a `next/link` when navigation should look like a button (landing CTAs). Don't nest a `<button>` in an `<a>`.

### Input / Field
- **`Field`** is the default form control: label + input + hint/error, wired `htmlFor`/`id` (auto-`useId`) and `aria-invalid`. Prefer it over raw `Input`.
- **`Input`** is the unstyled-logic primitive for rare custom cases.
- Error text uses `danger`; hint uses `muted` and hides when an error is shown (one message at a time).

### Card
- `Card` + `CardHeader` / `CardContent` / `CardTitle`. The standard surface for grouping content. Use `CardContent` for consistent padding; only add `CardHeader` when a titled divider is needed.

### Alert
- Inline feedback: `error` (`role="alert"`), `info`, `success` (`role="status"`). For form/API results shown in place. Not for global toasts (see §8 recommendations).

### ThemeToggle
- Ghost button with sun/moon SVG icons. Toggles between light and dark; persists via `useTheme()`. Placed in authenticated and public headers.

### Spinner
- Inline/standalone loading indicator; inherits `currentColor`. Used inside `Button` and for full-page auth/guard loading.

**Adding a component:** it belongs in `components/ui/` if it is presentation-only and reused; in `components/<feature>/` if it carries feature context. It must consume tokens (no hex), expose `className` passthrough via `cn()`, forward refs when it wraps a native control, and be exported from the relevant barrel.

---

## 5. Composition patterns (`components/layout/`, `components/auth/`, feature folders)

### App routes (Phase A)

| Route | Shell | Feature components |
|---|---|---|
| `/` | Landing header (logo + theme toggle) | centered SaaS hero (eyebrow → h1 → description → CTAs → trust note) |
| `/login`, `/register` | `AuthLayout` | forms with `Field` / `Button` / `Alert` |
| `/dashboard` | `AppShell` + `RequireAuth` | `StatementList`, `StatementCard` |
| `/upload` | `AppShell` + `RequireAuth` | `StatementUploadForm` |
| `/analysis/[id]` | `AppShell` + `RequireAuth` | `AnalysisDetailView` → `SubscriptionList`, `RecommendationList` |

### Layout & guards

- **`AuthLayout`** — centered card shell for `login`/`register`: brand bar, title/subtitle, `Card` body, optional footer link. Use for any unauthenticated, single-task screen.
- **`AppShell`** — authenticated chrome: brand, `NAV_ITEMS` nav with active state, Sign out. Add new authenticated destinations by extending `NAV_ITEMS` in one place — never re-implement the header per screen.
- **`RequireAuth` / `GuestOnly`** — client-side route guards (JWT lives in `localStorage`, so gating is client-side, not middleware). Protected pages wrap content in `RequireAuth`; `login`/`register` wrap in `GuestOnly`. Both render a full-page `Spinner` while the session hydrates, so there is no flash of the wrong state.

**Screen skeleton (authenticated):**
```tsx
export default function SomePage() {
  return (
    <RequireAuth>
      <AppShell>
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">Title</h1>
            <p className="mt-1 text-muted">One line of context.</p>
          </div>
          {/* Cards / content */}
        </div>
      </AppShell>
    </RequireAuth>
  );
}
```

---

## 6. Interaction & state conventions

Every data-driven surface handles four states explicitly:

| State | Convention |
|---|---|
| **Loading** | `Spinner` (inline in buttons; centered for full-page/guard). Prefer SWR `isLoading`. |
| **Empty** | A `Card` with a short explanation + the primary next action (e.g. "No statements yet — upload one"). Never a blank screen. |
| **Error** | `Alert variant="error"` with the backend `detail` message (already sanitized server-side — no sensitive content). Never show raw stack traces. |
| **Success** | Redirect to the meaningful next screen, or an inline `success` alert. |

- Async submit → set `loading`, clear previous error, `try/catch` around the API call, always reset `loading` in `finally`.
- Errors surfaced to users come from `ApiError.message` (from `{ "detail": ... }`) — do not invent client-side copy that could contradict the API.

---

## 7. Accessibility checklist (per screen)

- [ ] Every input has a visible `<label>` (use `Field`).
- [ ] Focus ring is present and not overridden.
- [ ] Color is never the only signal (pair with text/role/icon).
- [ ] Interactive elements are real `<button>`/`<a>` (keyboard + screen-reader friendly).
- [ ] Loading regions expose `role="status"`; errors use `role="alert"`.
- [ ] Text on `surface`/`background` meets WCAG AA (the token pairs above are chosen to pass).
- [ ] `autoComplete` set on auth fields (`email`, `current-password`, `new-password`).

---

## 8. Recommendations for future work (not yet built)

Add these only when a phase needs them — introduce the seam when the second use appears (same rule as backend abstractions, `implement-feature.md` Step 3). All should extend tokens/components, not fork the style:

- **Data table / list primitive** — the subscriptions list (A4.5) is the first real table; extract a `Table`/`DataList` into `components/ui/` when a second view needs it.
- **Money component** — a small `<Amount value currency />` wrapping `formatCurrency` so positive/negative styling and precision are centralized (uses `lib/format.ts`).
- **Toast/notification system** — for global, transient feedback (`Alert` stays for inline). Keep it token-driven and accessible (`aria-live`).
- **Empty-state & skeleton components** — standardize the loading/empty patterns in §6 as reusable pieces once repeated.
- **Icon set** — adopt one library (e.g. `lucide-react`) if icons are needed; never mix icon styles. Not required for the MVP.
- **Form/validation helper** — current forms use native validation + inline `Alert`. Introduce a schema helper only if forms grow beyond email/password.

Keep dependencies minimal (`REQUIREMENTS.md` Risk #3 — avoid over-engineering). Prefer a token or a small component over a new library.

---

## 9. Golden rules (quick reference)

**Do**
- Compose screens from `components/ui/` + layout shells.
- Use semantic tokens via Tailwind utilities.
- Give every async surface loading/empty/error states.
- Keep one primary action per view.

**Don't**
- Hard-code hex colors or px in components.
- Add a second accent color or a web font.
- Call `fetch` from a screen (go through `lib/api/*`).
- Remove focus rings or rely on color alone.
- Ship a screen without an empty/error state.
