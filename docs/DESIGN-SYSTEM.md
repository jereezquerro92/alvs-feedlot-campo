---
title: DESIGN-SYSTEM
type: reference
status: active
created: 2026-07-10
tags: [harness, frontend, design-system]
---

# DESIGN-SYSTEM

Owner of every visual and component decision ([[adr-04-frontend-and-design-system]] r5): where a decision here conflicts with any component's shipped default, this file wins. Stack context: [[FRONTEND]].

## The standing principle — variable-driven theming

> [!important] Supersedes "zero custom styling" (owner override, 2026-07-14)
> The prior standing principle — **zero custom styling, defaults win** — is superseded, in place, by kodex's explicit 2026-07-14 decision. It no longer holds and MUST NOT be read as current truth. The replacement is below.

**Everything visual is a CSS custom property (a token); nothing is hard-coded.** Color, radius, and background are never authored as literal values inside a component or a one-off utility class — they are always a reference to a token defined once, in `frontend/src/styles/app.css`. A shadcn-svelte component still ships styled by default ([[adr-04-frontend-and-design-system]] r4), but its default *is itself expressed through the token layer* — changing a token changes every consumer, with zero component edits.

This is not "more custom CSS than before" — it is the same amount of bespoke, component-level styling as the prior principle (still close to zero), redirected: instead of freezing the shadcn-svelte/theme defaults as immovable, the template makes every visual value swappable at one seam. The template still does not hand-author component CSS; it authors tokens.

## The token layer (SSOT)

`frontend/src/styles/app.css` is the single source of truth for every visual token. The set below is canonical — a visual value used anywhere in the frontend traces back to one of these, never to a literal:

`--background`, `--foreground`, `--primary`, `--secondary`, `--accent`, `--muted`, `--card`, `--popover`, `--destructive`, `--border`, `--input`, `--ring`, `--radius`, the `--spotlight-*` pair, `--canvas`, plus three financial-state pairs — `--success`, `--warning`, `--negative` — each with its own `--*-foreground`. Every color token — `--card`, `--popover`, `--primary`, `--secondary`, `--muted`, `--accent`, `--success`, `--warning`, `--negative` — ships a paired `--*-foreground` token for the text color drawn on that surface; the pair is listed once, under its base token, not enumerated twice.

- **`--primary`'s hue is orange** (`H ≈ 45` in OKLCH), and every neutral surface token (`--background`/`--card`/`--popover`/`--secondary`/`--muted`/`--accent`/`--border`/`--input`) carries a faint matching warm tint (low chroma, `H ≈ 50–60`) so the UI reads as orange-native, not "gray UI with an orange button." Alternate `--primary` hues (burnt terracotta, golden amber, coral-red-orange) ship as commented swap options directly in `app.css`, alongside the shipped value, for a project cloning this template.
- **The financial-state tokens are named distinctly from `--destructive`** even where a value is shared (`--negative` currently equals `--destructive`'s OKLCH value) — a financial "danger" state and a form-validation error are the same red today, by name they are two separate tokens, so diverging them later touches one value, not every consumer's markup. These are state-color tokens, not domain-scoped components: a business-agnostic component like `NumericValue` or `StatusBadge` ([[COMPONENTIZATION]]) reads `--negative` for a bad number regardless of what kind of app renders it.
- **Color space is OKLCH**, for every token above — perceptually uniform lightness makes light/dark pairs and user-tunable presets predictable to derive.
- **Dark mode is the `.dark` class**, switched via Tailwind 4's `@custom-variant dark (&:is(.dark *))`. This is not optional infrastructure: **every color surface token above ships a light value AND a `.dark` value, always** — a color token defined in `:root` without its `.dark` counterpart is a defect, not an oversight. One named exception, as shipped: `--radius` is a length, not a color, so it has no `.dark` variant to speak of. The `--spotlight-*` pair's prior light-mode-only gap is closed — it now ships its own `.dark` pair like every other color token.
- Tokens are exposed to Tailwind utilities through `@theme inline` (`--color-background: var(--background)`, etc.) — utilities consume the token, never the raw OKLCH literal, so a token change propagates without touching a single class.
- **A bare `border` follows `--border`, never `currentColor`** — an `@layer base` rule in `app.css` resets `border-color` to `var(--color-border)` on every element, because Tailwind 4 otherwise paints an unset border in the near-white foreground (the "white border" defect). Explicit border-color utilities (`border-primary`, `border-primary/40`, `border-input`) still win; the reset only governs borders that name no color.
- This layer already exists in the codebase; this doc is its governing record, not a proposal.

## Palette ratification (owner decision, 2026-07-16)

> [!success] Rationed-orange palette approved, both themes — orange-canvas-light dropped
> kodex evaluated the running app at `localhost:4321` and approved the current palette as-is, in both light and dark. This closes the palette question opened in epic #178: the proposal there to give the light theme an **orange background canvas** is dropped; the shipped **rationed-orange** approach — orange confined to `--primary`, every surface token neutral — is the accepted, standing direction. See #169 for the prior no-pure-white / warm-neutrals thread this ratifies.

Both themes stay fully token-driven CSS custom properties in `frontend/src/styles/app.css` (the SSOT — this section states the decision, not new values; read the file for exact figures if they drift). As ratified:

- **Light (`:root`):** a warm off-white / very-light-warm-grey field — `--background`, `--canvas` (the slightly deeper page canvas), `--card`/`--popover`, `--muted`, `--border` — all low-chroma, warm-hued neutrals; `--primary` carries the orange accent. `color-scheme: light`.
- **Dark (`.dark`):** a near-black field on the same neutral tokens, `--primary` the same orange accent at a lightness/chroma tuned for dark surfaces. `color-scheme: dark`.
- **The invariant this ratifies:** orange lives ONLY in `--primary` (and tokens that intentionally echo it, e.g. `--ring`) in both themes — never as `--background` or `--canvas`. No pure white in either mode (#169).

This is a standing ratification, not a snapshot pinned to today's OKLCH numbers — a future token retune stays governed by "Tokens, not literals" and "Light + dark, always" below; it does not reopen the orange-canvas-light question, which is closed.

## User-configurable subset (`/profile`)

A subset of the token layer is exposed to the end user, not just to the developer. This is deliberately narrow — most tokens stay developer-only:

| Control | Values | Backs which token(s) |
|---|---|---|
| mode | `light` \| `dark` (default: `dark`) | toggles the `.dark` class |
| bgPreset | `default` \| `melt` (default: `melt`) | `[data-bg-preset]` attribute → the `--melt-dots-*`/`--melt-fade-color` set below, with distinct light/dark pairs |
| custom background | OKLCH color | `--background` |
| custom primary | OKLCH color | `--primary` |
| custom secondary | OKLCH color | `--secondary` |
| custom accent | OKLCH color | `--accent` |
| radius | length | `--radius` (the three derived `--radius-*` follow via `@theme inline`) |

- **Persistence is per-user**: the chosen values live on `User.theme_config`, read and written through `PATCH /api/me/` ([[API]]). A profile visual preference is user data, not session state — it survives logout/login on the same account.
- **Mirrored to a `theme` cookie for no-flash SSR.** The cookie is a client-side rendering hint, not a secret and not a session credential: it carries no auth data and needs no `HttpOnly`/`Secure` treatment beyond ordinary hygiene. Mechanism: below.
- **This is not a cached response.** The theme cookie changes what the server renders per request, but the response it produces for an authenticated user is still `no-store` by default ([[adr-06-cache]], [[CACHE]]) — personalizing via a cookie and caching the personalized output are different questions, and this doc answers only the first. A future opt-in to cache a themed fragment is a row-level decision in [[API]], not implied by this section.

## Theme application mechanism

One shared pair of pure functions in `frontend/src/lib/theme.ts` — `computeThemeSSRAttrs` and its client wrapper `applyTheme` — is the single place that turns a `ThemeConfig` blob into `.dark` / `data-bg-preset` / inline token overrides. Every rendering path below calls one of the two; neither Base.astro nor ThemeCard hand-rolls its own version:

- **SSR, no-flash.** `Base.astro` reads the `theme` cookie (`Astro.cookies.get("theme")`), decodes and sanitizes it with `parseThemeConfig` (which delegates to `sanitizeThemeConfig`/`sanitizeColor`/`sanitizeRadius`), then calls `computeThemeSSRAttrs(blob)` for `{ htmlClass, dataBgPreset, style }` — spread straight onto `<html>` before the first byte renders. This is why an authenticated user never sees a flash of the default theme on navigation or after login (the `theme` cookie is set by the backend on login and on a successful `PATCH /api/me/`, [[API]]).
- **Client live preview.** `ThemeCard.svelte` runs an `$effect` that calls `applyTheme(draftBlob)` on every control change — the mode toggle, the `bgPreset` radio, a color input, the radius field. `applyTheme` reuses `computeThemeSSRAttrs` internally, then writes the class, the `data-bg-preset` attribute, and the custom-property overrides directly onto `document.documentElement`. This is a pure client-local repaint: no `PATCH /api/me/` request fires per keystroke or click.
- **Cookie mirror only on a confirmed Save.** `writeThemeCookie` runs exactly once per Save click, and only after `PATCH /api/me/` returns `200` — never from the live-preview effect. It mirrors the server's own echoed, re-sanitized response, not the client's draft, so the cookie always matches what actually persisted. A `400` or network failure leaves the `theme` cookie and the last-confirmed snapshot (what Reset reverts to) untouched; the draft stays live-previewed but unpersisted.
- **Sanitize on both sides, one shared contract.** `sanitizeColor`/`sanitizeRadius`/`sanitizeThemeConfig` (`theme.ts`) run client-side at every hop that touches untrusted input — building the live-preview draft blob, narrowing the confirmed `PATCH` response before it is mirrored to the cookie, and inside `computeThemeSSRAttrs`/`applyTheme` themselves — and Django re-validates the identical shape server-side before persisting ([[API]]). Neither side treats the other's input as pre-sanitized.

## The Melt preset — dotted background

`bgPreset: "melt"` is now the **default** preset ([[bdd-07-melt-theme-sitewide]]) — every route without a `theme` cookie renders it — activated by `[data-bg-preset="melt"]` on the `<html>` element (set by `computeThemeSSRAttrs`/`applyTheme` — see "Theme application mechanism" above). It reproduces melt-ui.com's **actual** construction, matched to its own scraped CSS: a **neutral field** (the existing `--canvas` token — NOT a separate amber-tinted background), a **dot-grid layer**, and a **top-fade highlight** layered above the dots, on a **2rem grid**. It is fully variable-driven; the rule itself — selectors, gradients, both mode pairs — lives once, as the SSOT, in `frontend/src/styles/app.css` (`[data-bg-preset="melt"]` / `.dark[data-bg-preset="melt"]`), and is not repeated here:

| Token | Tunes |
|---|---|
| `--melt-dots-size` | dot-grid density (2rem grid) |
| `--melt-dots-color` | dot color/opacity — its own light and dark value |
| `--melt-fade-color` | top-fade highlight color/opacity — its own light and dark value |

- **Explicit light AND dark token pairs, always** — `[data-bg-preset="melt"]` carries the light-mode values; `.dark[data-bg-preset="melt"]` overrides both `--melt-dots-color` and `--melt-fade-color` with their own tuning, never the light-mode value reused unchanged (a token without its `.dark` pair is a defect, per the rule below). This closed two real prior gaps — a flat `--melt-dots-color` and an opaque `--melt-fade-color` both reused unchanged under `.dark`, the second painting a solid band over the top of a dark-mode viewport instead of a faint highlight. Exact current values are read from `app.css`, never mirrored here.
- The base field is the **neutral** `--canvas` token, shared with the `default` preset's spotlight background — `melt` is a dot-grid + fade layered on top of the same neutral field, not a separate amber-tinted field.
- The token declarations sit on `[data-bg-preset="melt"]`/`.dark[data-bg-preset="melt"]` (the `<html>` element); the painted `background` is scoped to `[data-bg-preset="melt"] body`, overriding the plain `body { background: ... }` rule above by specificity.
- Tuned to match melt-ui.com's own `.dotted-bg`/`.dotted-bg:after` rule pair (scraped ground truth: a dot-grid radial gradient plus a top-fade), widened to a `2rem` grid for this template, so a project drawing its interactive primitives from Melt ([[MELT-UI]]) gets a background that reads as the same family, not an approximation.
- **One-line adjustable, in `app.css`**: dot density is `--melt-dots-size`, dot color/opacity is `--melt-dots-color` (per mode), the fade highlight is `--melt-fade-color` — changing the preset never means touching the gradient rules themselves, only their tokens.
- `default` (no `data-bg-preset`, or `data-bg-preset="default"`) is now the **non-default, alternate** preset — the existing `--canvas` + spotlight background already in `app.css`, unchanged by this section. A visitor with no saved preference sees `melt`, in dark mode, by default ([[bdd-07-melt-theme-sitewide]]); `default` is reached only by an explicit user choice on `/profile`.

## Component layering — Melt UI first, shadcn-svelte second, custom last (Bits UI is upstream lineage, not installed)

Three layers in this repo, in priority order ([[adr-04-frontend-and-design-system]] r8):

1. **Melt UI (pkg `melt`) is the default builder layer for a new component.** Headless builders with no shipped markup or CSS at all, wired directly onto your own markup — reached for first, before considering a vendored default. Choosing-Melt criteria and vendored examples are owned by [[MELT-UI]].
2. **shadcn-svelte is the second choice.** Vendored components ([[adr-04-frontend-and-design-system]] r4) already speak the token layer above and need no bespoke styling to fit the theme; reach for one when a Melt builder doesn't already cover the shape needed, or a shadcn-svelte primitive is genuinely the better fit. shadcn-svelte's own components are historically and architecturally derived from Bits UI, itself built on Melt — but that lineage is upstream of this repo: the vendored components here hand-roll their state via `getContext`/`setContext`, not Bits UI primitives.
3. **A fully hand-rolled custom component is the last resort** — only when neither a Melt builder nor a vendored shadcn-svelte component produces the behavior or visual shape a feature needs.

**Bits UI is not a dependency of this repo** — no row in [[REQUIREMENTS]], zero usage. It is upstream lineage context for how shadcn-svelte itself is built, not a rung of this stack; adopting it as an active layer would require its own [[REQUIREMENTS]] row first ([[adr-02-initial-stack]] r1).

How-to and the concrete choose-Melt-vs-shadcn criteria are owned by [[MELT-UI]], not restated here. The `.astro`-routes-only discipline that decides which files these layered components may live inside is owned by [[COMPONENTIZATION]].

## What this means in practice

- **Tokens, not literals.** A color, radius, or background value written directly into a component (a hex code, an inline `oklch(...)`, a magic pixel radius) is a defect — it belongs in `app.css` as a token, referenced from there.
- **rem over px, everywhere.** Every length in `app.css` — radii, the melt-preset grid, gradient offsets — is `rem`, never `px`; a length that must stay outside the token layer (a one-off gradient offset, not itself a swappable design decision) is still authored in `rem` so it scales with the root font size.
- **Hex for a literal, OKLCH for a token.** A one-off, genuinely non-token color value (a code comment showing a swap option, a third-party asset color) is written as hex, so it reads unambiguously as "not a token, don't reach for `var(--...)`"; anything that IS a token — everything a component actually consumes — stays OKLCH. "Literal" is this doc's canonical term for such a value; do not introduce "fixed value" or similar as a synonym.
- **Light + dark, always.** Adding a token without its `.dark` pair is incomplete work, not a follow-up.
- **User-facing theming is additive, not a redesign.** The `/profile` controls narrow a pre-existing token set; they never introduce a token that only the user-configurable path uses.
- **This file still owns every visual decision** ([[adr-04-frontend-and-design-system]] r5): a future preset, a new user-configurable token, or a fourth component layer is recorded here before it ships, exactly as this rewrite was.
