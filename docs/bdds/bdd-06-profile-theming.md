---
title: bdd-06-profile-theming
type: bdd
status: draft
created: 2026-07-14
tags: [bdd, profile, theming, design-system]
---

# bdd-06 — profile theming

## Use case

As a **signed-in user**, when I open `/profile`, I can set my appearance —
`mode` (`light`/`dark`), a background `bgPreset` (`default` or the amber
dotted `melt` preset), and custom colors for background/primary/secondary/
accent plus a border radius — and see the change previewed live before I
save it. Saving writes the choice to my account (`PATCH /api/me/`,
`theme_config` — [[API]], [[GLOSSARY]]) and refreshes the `theme` cookie, so
the same appearance renders server-side, with no flash, on my next visit or
login. Everything the control panel touches is a CSS custom property —
never a hard-coded value ([[DESIGN-SYSTEM]]).

## Scenarios

### Happy path — customize and save

```gherkin
Given a signed-in user on `/profile`
When they choose a `mode`, a `bgPreset`, custom OKLCH colors for background,
  primary, secondary, and accent, and a radius
And they click Save
Then a `PATCH /api/me/` request is sent with `theme_config` set to
  `{mode, bgPreset, colors, radius}` ([[API]], [[GLOSSARY]]: `theme_config`)
And the response updates the same fields `GET /api/me/` would return
And the `theme` cookie is refreshed to mirror the saved `theme_config`
  ([[DESIGN-SYSTEM]])
```

### Live preview before save

```gherkin
Given a signed-in user on `/profile` with the theme controls open
When they change `mode`, `bgPreset`, a custom color, or the radius
Then the corresponding CSS custom property updates immediately on the
  rendered page ([[DESIGN-SYSTEM]] token layer) as a client-local preview
And no `PATCH /api/me/` request fires yet — the draft is unsaved
And clicking Save is what turns the current preview into a persisted write
```

### Persistence across login — no flash

```gherkin
Given a user who has previously saved a non-default `theme_config`
  (e.g. `mode: dark`, `bgPreset: melt`)
When they sign out and sign back in, or simply revisit any page
Then the `theme` cookie carries the saved values into the request
And Astro SSR applies `.dark` / `data-bg-preset` / the custom token
  overrides from the cookie before first paint ([[DESIGN-SYSTEM]])
And the page never renders the default theme first and then swaps —
  there is no flash of the wrong theme
```

### Invalid custom value is rejected

```gherkin
Given a signed-in user on `/profile`
When they submit a `theme_config` payload with a malformed value (an enum
  member outside `light`/`dark` or `default`/`melt`, a non-color string, or
  an out-of-range radius)
Then `PATCH /api/me/` returns `400` and the field is left unchanged
  server-side
And the `theme` cookie is NOT refreshed
And the offending control shows an inline error while the rest of the
  live preview keeps reflecting the user's still-unsaved draft
```

### Unauthenticated visitor

```gherkin
Given a visitor with no established Django session
When they request `/profile`
Then they are redirected to the Cognito-backed sign-in flow ([[AUTH]])
And no `theme_config` read or write is attempted
```

## Frontend half

**Theme controls — Svelte island, rung 3 of the interactivity ladder**
([[adr-04-frontend-and-design-system]] rule 3, [[FRONTEND]]). The panel
holds four continuously-varying, client-owned inputs (mode toggle, preset
choice, four color pickers, a radius control) whose every interaction must
repaint the page's CSS custom properties *before* any server round trip —
exactly the "optimistic UI, act before the server confirms" and "rich
widget with local component state" cases [[HTMX]]'s ladder criteria route to
a Svelte island, not HTMX: a fragment reload per color-picker drag would be
prohibitively chatty and there is no server-owned state to render until
Save, the same reasoning bdd-05's nickname draft used for a single control,
scaled to five. The draft values, the dirty flag, and the live-preview
token writes are transient client state that resolves into a `PATCH
/api/me/` write only on explicit Save — never per-keystroke.

**Mode/`bgPreset` control — built on a Melt UI builder** ([[MELT-UI]], pkg
`melt`), not a shadcn-svelte or Bits UI toggle-group recipe. Per
[[DESIGN-SYSTEM]]'s component-layering order (shadcn-svelte → Bits UI →
Melt UI as the escape hatch), Melt is reached only when a shadcn-svelte/
Bits UI recipe doesn't already cover the needed pattern; here the control
must drive the live-preview token application directly — toggling the
`.dark` class and the `[data-bg-preset]` attribute on the document root as
part of its own state changes, not through a shipped, styled toggle
component — which is the fully-custom-behavior case [[MELT-UI]] reserves
Melt for. Exact builder choice and markup are [[MELT-UI]]'s to specify, not
restated here ([[DESIGN-SYSTEM]] rule).

The four color pickers and the radius control render through shadcn-svelte
form primitives (rung 1 of the component layering, [[DESIGN-SYSTEM]]) —
only the mode/preset segmented control needs Melt. Design compliance:
every value the panel writes is one of the canonical tokens
(`--background`, `--primary`, `--secondary`, `--accent`, `--radius`) —
never a literal ([[DESIGN-SYSTEM]]). Variables consumed: none beyond the
existing session-scoped fetch of `GET /api/me/` to prefill current values —
no `PUBLIC_*` addition ([[VARIABLES]]).

## Backend half

Reuses the existing `PATCH /api/me/` / `GET /api/me/` row ([[API]]),
**widened** to read and write a fourth field, `theme_config` — the JSON
blob `{mode, bgPreset, colors: {background, primary, secondary, accent},
radius}` ([[GLOSSARY]]: `theme_config`, `mode`, `bgPreset`;
[[DESIGN-SYSTEM]]: user-configurable subset). As of this entry, [[API]]'s
`PATCH /api/me/` contract lists only `nickname` and `avatar_visible` as
write fields — widening it to `theme_config` is a prerequisite, its own
reviewable [[API]] row change ([[adr-03-api-and-backend]] rule 3) before any
[[TDD]] entry for this write path is drafted, per the
[[adr-07-development-flow]] rule 4 checkpoint: does [[API]] solve the need
today? No — the row must be added first, then the checkpoint reruns.
`GET /api/me/`'s `UserSerializer` output needs the same widening so the
island can prefill saved values on page load.

Feeds the [[TDD]] entry(ies) owed once that row lands: `theme_config` shape
validation (enum checks on `mode`/`bgPreset`, color-string and radius
range/format checks), partial-update semantics consistent with the existing
`nickname`/`avatar_visible` fields, `no-store` header, `403` without
session. Mirroring the saved value into the `theme` cookie on a successful
write, and Astro SSR reading that cookie to render `.dark` /
`data-bg-preset` / inline token overrides before first paint, is
[[DESIGN-SYSTEM]]-owned frontend/SSR behavior reading a plain cookie — it
needs no additional [[API]] row.

## Error handling

A `400` from `PATCH /api/me/` (malformed `theme_config` shape or an
out-of-enum value) surfaces inline next to the offending control; the rest
of the panel keeps the user's unsaved draft and its live preview — nothing
reverts to the last-saved theme except the field that failed. The `theme`
cookie is refreshed only on a `200` from `PATCH /api/me/`, never
speculatively from the client-side preview. `403` (session expired
mid-edit) redirects to `/accounts/login/`, matching bdd-05's pattern. All
authenticated responses are `no-store` ([[CACHE]], [[adr-06-cache]] rule 4).

## Shadow-test spec

- Open `/profile` → toggle `mode` to dark → page repaints dark immediately,
  no request fires → choose `bgPreset: melt` → amber dotted background
  renders → adjust a custom color and the radius → click Save →
  `PATCH /api/me/` fires with the full `theme_config` → reload the page →
  the same theme renders from the `theme` cookie, no flash of the default
  theme first.
- Sign out and sign back in → the previously saved theme applies
  server-side before first paint (cookie-driven SSR, no flash).
- Submit an invalid custom color or out-of-range radius → inline error
  shown on that control → `theme` cookie unchanged → other draft controls
  keep their live preview.
- Visit `/profile` signed out → redirected to sign-in, no `theme_config`
  read/write attempted.
- Until a project's shadow-test runner exists, this entry may reach
  `building`, never `shipped` ([[BDD]]).
