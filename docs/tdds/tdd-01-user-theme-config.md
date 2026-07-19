---
title: tdd-01-user-theme-config
type: tdd
status: done
created: 2026-07-14
api: ["GET /api/me/", "PATCH /api/me/"]
tags: [tdd, users, theme, design-system]
---

# tdd-01 — user theme_config

## Context

Backend half of [[bdd-06-profile-theming]]. [[API]]'s `PATCH /api/me/` row was
widened to accept a fourth write field, `theme_config` — the per-user
appearance blob `{mode, bgPreset, colors, radius}` — and `GET /api/me/` was
widened to return it ([[GLOSSARY]]: `theme_config`, `theme`, `mode`,
`bgPreset`). This entry is the [[TDD]] flow that widening owes, plus the
`theme` cookie mirror on `MeView` PATCH and both login views
(`CallbackView`, `DevLoginView`) so Astro SSR can render the saved theme with
no flash ([[DESIGN-SYSTEM]]).

## Design

- `User.theme_config` — `models.JSONField(default=dict, blank=True)`
  ([[BACKEND]]); `default=dict` keeps every existing/new row at `{}` with no
  data migration needed. Migration `0005_user_theme_config.py`.
- `UserSerializer` gains `theme_config` as a normal writable field (not in
  `read_only_fields`); a `validate_theme_config` field validator enforces the
  closed contract from [[API]]: top-level keys limited to
  `mode`/`bgPreset`/`colors`/`radius`; `mode` ∈ `{light, dark}`; `bgPreset` ∈
  `{default, melt}`; `colors` keys limited to
  `background`/`primary`/`secondary`/`accent`, each value matching
  `^(#[0-9a-fA-F]{3,8}|rgb(a)?\(.*\)|hsl\(.*\)|oklch\(.*\))$` and containing
  none of `; { } < >` nor the substrings `url`/`expression` (case-insensitive)
  — the injection guard [[DESIGN-SYSTEM]] requires for a value that lands in
  a CSS custom property; `radius` must be a string, stored as-is. An unknown
  key or an out-of-contract value is a `400`, matching the existing
  read-only-field rejection style already in `UserSerializer.validate`.
  Because DRF's default `ModelSerializer.update()` assigns the validated
  value directly to the JSONField, a `theme_config` present in a PATCH
  **replaces the stored blob wholesale** with no extra code — the same
  mechanism `nickname`/`avatar_visible` already use, just applied to a dict
  field. Absent from the request body → untouched, per DRF's `partial=True`
  semantics.
- `views.set_theme_cookie(response, blob)` — one shared helper (no cache
  layer involved, no server exists beyond the `theme` cookie itself,
  [[CACHE]] unaffected): URL-encodes `json.dumps(blob)` with
  `urllib.parse.quote(..., safe="")` so it round-trips with the frontend's
  `decodeURIComponent`, and sets it `Path=/`, `SameSite=Lax`,
  `Max-Age=31536000`, `HttpOnly=False` (the frontend must read it),
  `Secure=settings.CSRF_COOKIE_SECURE` (mirrors the existing cookie-security
  policy rather than introducing a new variable — no [[VARIABLES]] row
  needed). Wired into three call sites: `MeView.patch` (only when
  `theme_config` was a key in the request body — a 400 or a PATCH that never
  touched the theme must never refresh the cookie), `CallbackView.get` and
  `DevLoginView.get` (always, right after `login()`, from `user.theme_config`
  — including the `{}` default for a brand-new user, so SSR always has a
  cookie to read).
- No new settings/env variable; `CSRF_COOKIE_SECURE` is reused as-is.

## Tests (`backend/apps/users/test_theme.py`)

Failing-first, then made green:

- `test_me_get_includes_theme_config_default_empty` / `..._returns_persisted_theme_config`
- `test_me_patch_valid_theme_config_persists_and_returns_it`
- `test_me_patch_valid_theme_config_sets_theme_cookie_roundtrip` (decodes the
  `Set-Cookie` value and asserts it matches the saved blob)
- `test_me_patch_theme_config_cookie_attributes` (`Path`, `SameSite`,
  `Max-Age`, `HttpOnly` off, `Secure` mirrors `CSRF_COOKIE_SECURE`)
- `test_me_patch_theme_config_replaces_wholesale`
- `test_me_patch_without_theme_config_key_leaves_existing_unchanged` /
  `..._does_not_set_cookie`
- `test_me_patch_theme_config_unknown_top_level_key_rejected` /
  `..._unknown_color_key_rejected` (400, blob unchanged, cookie not set)
- `test_me_patch_theme_config_bad_mode_enum_rejected` /
  `..._bad_bgpreset_enum_rejected` (parametrized)
- `test_me_patch_theme_config_injection_color_rejected` (parametrized:
  non-color strings, `;`, `url(...)`, `expression(...)`, `<script>`)
- `test_me_patch_theme_config_accepts_all_color_forms` (hex, `rgb`, `rgba`,
  `hsl`, `oklch` — parametrized)
- `test_me_patch_theme_config_bad_radius_type_rejected` /
  `..._not_object_rejected`
- `test_me_patch_theme_config_no_store`
- `test_callback_sets_theme_cookie_from_existing_user` /
  `..._default_empty_for_new_user`
- `test_dev_login_sets_theme_cookie` / `..._default_empty_theme_cookie_for_new_user`
- Regression: `test_rbac.py::test_me_patch_updates_nickname`,
  `test_me_patch_updates_avatar_visible` and the `GET /api/me/` exact-shape
  assertion (widened to include `theme_config: {}`) stay green.

## Status

`done`. Tests written first against the pre-widening model/serializer/views
(confirmed red — `theme_config` absent from the model), then
`theme_config` (model field, migration `0005`, serializer validation, the
`set_theme_cookie` helper and its three call sites) were implemented until
green. `python manage.py makemigrations --check --dry-run` reports "No
changes detected"; the full `backend/apps/users` suite (112 tests) and the
full backend suite (196 tests) pass.
