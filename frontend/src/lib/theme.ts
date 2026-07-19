/* LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-04-frontend-and-design-system]]
 * Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[MELT-UI]]
 * LIVE-DOC:END */

// Theme contract v1 — the SSOT for the `theme_config` blob shape, its
// sanitization rules, and the cookie mirror, matching docs/API.md's
// `PATCH /api/me/` `theme_config` validation exactly and
// docs/DESIGN-SYSTEM.md's user-configurable token subset. Kept DOM-free
// where possible (`computeThemeSSRAttrs`, `sanitizeColor`,
// `sanitizeRadius`, `parseThemeConfig`) so Base.astro's SSR render and
// bun:test can both use it without a browser.

export type ThemeMode = "light" | "dark";
export type ThemeBgPreset = "default" | "melt";

export interface ThemeColors {
  background?: string;
  primary?: string;
  secondary?: string;
  accent?: string;
}

export interface ThemeConfig {
  mode?: ThemeMode;
  bgPreset?: ThemeBgPreset;
  colors?: ThemeColors;
  radius?: string;
}

export const DEFAULTS: { mode: ThemeMode; bgPreset: ThemeBgPreset } = {
  mode: "dark",
  bgPreset: "melt",
};

export const COLOR_KEYS: readonly (keyof ThemeColors)[] = [
  "background",
  "primary",
  "secondary",
  "accent",
];

const COOKIE_NAME = "theme";

// Mirrors docs/API.md's PATCH /api/me/ `theme_config` validation regex
// exactly: `^(#[0-9a-fA-F]{3,8}|rgb(a)?\(.*\)|hsl\(.*\)|oklch\(.*\))$`, plus
// the explicit forbidden-substring guard (`;`, `{`, `}`, `<`, `>`, `"`, `'`,
// `url`, `expression`) called out alongside it.
const COLOR_PATTERN = /^(#[0-9a-fA-F]{3,8}|rgb(a)?\(.*\)|hsl\(.*\)|oklch\(.*\))$/;
const RADIUS_PATTERN = /^[0-9]*\.?[0-9]+(px|rem|em|%|vh|vw|ch)$/;
const FORBIDDEN_SUBSTRINGS = [";", "{", "}", "<", ">", '"', "'", "url", "expression"];

function hasForbiddenSubstring(value: string): boolean {
  const lower = value.toLowerCase();
  return FORBIDDEN_SUBSTRINGS.some((needle) => lower.includes(needle));
}

/** Validates one color string against the shared contract. Returns
 * `undefined` for anything absent or invalid — never throws. */
export function sanitizeColor(value: string | undefined | null): string | undefined {
  if (!value) return undefined;
  const trimmed = value.trim();
  if (!trimmed || hasForbiddenSubstring(trimmed)) return undefined;
  return COLOR_PATTERN.test(trimmed) ? trimmed : undefined;
}

/** Validates a CSS length string for `--radius`. Same forbidden-substring
 * guard as colors, plus a plain-length shape check. */
export function sanitizeRadius(value: string | undefined | null): string | undefined {
  if (!value) return undefined;
  const trimmed = value.trim();
  if (!trimmed || hasForbiddenSubstring(trimmed)) return undefined;
  return RADIUS_PATTERN.test(trimmed) ? trimmed : undefined;
}

function isMode(value: unknown): value is ThemeMode {
  return value === "light" || value === "dark";
}

function isBgPreset(value: unknown): value is ThemeBgPreset {
  return value === "default" || value === "melt";
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Narrows an arbitrary parsed value (cookie or `me.theme_config`) down to
 * the closed `ThemeConfig` shape, dropping unknown keys and any
 * enum/color/radius value that fails sanitization. Never throws. */
export function sanitizeThemeConfig(value: unknown): ThemeConfig {
  if (!isPlainObject(value)) return {};

  const blob: ThemeConfig = {};
  if (isMode(value.mode)) blob.mode = value.mode;
  if (isBgPreset(value.bgPreset)) blob.bgPreset = value.bgPreset;

  if (isPlainObject(value.colors)) {
    const colors: ThemeColors = {};
    for (const key of COLOR_KEYS) {
      const safe = sanitizeColor(value.colors[key] as string | undefined);
      if (safe) colors[key] = safe;
    }
    if (Object.keys(colors).length > 0) blob.colors = colors;
  }

  const safeRadius = sanitizeRadius(value.radius as string | undefined);
  if (safeRadius) blob.radius = safeRadius;

  return blob;
}

/** Parses a raw `theme` cookie value — handling both a still-URI-encoded
 * string and an already-decoded one (frameworks differ on this) — and
 * defaults to `{}` on anything missing or malformed. */
export function parseThemeConfig(raw: string | null | undefined): ThemeConfig {
  if (!raw) return {};
  const candidates = [raw];
  try {
    candidates.push(decodeURIComponent(raw));
  } catch {
    // raw wasn't URI-encoded; fall through with the original candidate only
  }
  for (const candidate of candidates) {
    try {
      return sanitizeThemeConfig(JSON.parse(candidate));
    } catch {
      // try the next candidate
    }
  }
  return {};
}

export interface ThemeSSRAttrs {
  /** `"dark"` or `""` — spread into the `<html>` `class` attribute. */
  htmlClass: string;
  /** Always present — `data-bg-preset` on `<html>`. */
  dataBgPreset: ThemeBgPreset;
  /** Semicolon-joined `--token: value` declarations for only the present,
   * sanitized overrides — spread into the `<html>` inline `style`. */
  style: string;
}

/** Pure — no `document` access. Base.astro's SSR render calls this with the
 * cookie-derived blob to compute what to put on `<html>` before first
 * paint, with no flash ([[DESIGN-SYSTEM]]). */
export function computeThemeSSRAttrs(blob: ThemeConfig | null | undefined): ThemeSSRAttrs {
  const mode: ThemeMode = blob?.mode ?? DEFAULTS.mode;
  const bgPreset: ThemeBgPreset = blob?.bgPreset ?? DEFAULTS.bgPreset;

  const styleParts: string[] = [];
  for (const key of COLOR_KEYS) {
    const safe = sanitizeColor(blob?.colors?.[key]);
    if (safe) styleParts.push(`--${key}: ${safe}`);
  }
  const safeRadius = sanitizeRadius(blob?.radius);
  if (safeRadius) styleParts.push(`--radius: ${safeRadius}`);

  return {
    htmlClass: mode === "dark" ? "dark" : "",
    dataBgPreset: bgPreset,
    style: styleParts.join("; "),
  };
}

/** Client-only: applies a theme blob to `root` (default
 * `document.documentElement`) for the live-preview path — every control
 * change in ThemeCard calls this before any `PATCH /api/me/` fires. */
export function applyTheme(
  blob: ThemeConfig | null | undefined,
  root: HTMLElement = document.documentElement,
): void {
  const attrs = computeThemeSSRAttrs(blob);
  root.classList.toggle("dark", attrs.htmlClass === "dark");
  root.setAttribute("data-bg-preset", attrs.dataBgPreset);

  for (const key of COLOR_KEYS) {
    const safe = sanitizeColor(blob?.colors?.[key]);
    const varName = `--${key}`;
    if (safe) root.style.setProperty(varName, safe);
    else root.style.removeProperty(varName);
  }

  const safeRadius = sanitizeRadius(blob?.radius);
  if (safeRadius) root.style.setProperty("--radius", safeRadius);
  else root.style.removeProperty("--radius");
}

/** Client-only: reads and parses the `theme` cookie. Returns `{}` if
 * absent/malformed — callers fall back to `DEFAULTS`. */
export function readThemeCookie(): ThemeConfig {
  if (typeof document === "undefined") return {};
  const match = document.cookie.match(/(?:^|;\s*)theme=([^;]+)/);
  return match ? parseThemeConfig(match[1]) : {};
}

/** Client-only mirror of the cookie the backend refreshes on a successful
 * `PATCH /api/me/` ([[API]]). Per docs/bdds/bdd-06-profile-theming.md's
 * error-handling clause, this is called ONLY after a `200` save response —
 * never speculatively from the live-preview path, which uses `applyTheme`
 * alone. The browser's own `Set-Cookie` handling already does this; calling
 * it explicitly here keeps the client-side draft state in sync too. */
export function writeThemeCookie(blob: ThemeConfig): void {
  if (typeof document === "undefined") return;
  const value = encodeURIComponent(JSON.stringify(blob));
  document.cookie = `${COOKIE_NAME}=${value}; Path=/; Max-Age=31536000; SameSite=Lax`;
}
