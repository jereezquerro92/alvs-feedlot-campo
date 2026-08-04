/* LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-52-frontend-and-design-system]]
 * Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[MELT-UI]]
 * LIVE-DOC:END */

// Theme contract — SSOT for the `theme_config` blob shape, sanitization, and
// cookie mirror, matching docs/API.md's PATCH /api/me/ validation and
// docs/DESIGN-SYSTEM.md's user-configurable subset. DOM-free helpers
// (`computeThemeSSRAttrs`, sanitize*, `parseThemeConfig`) so Base.astro SSR
// and bun:test share one contract with the live-preview path.

export type ThemeMode = "light" | "dark";
export type ThemeBgPreset = "default" | "melt";
export type SidebarSide = "left" | "right";

export interface ThemeColors {
  /** Page field — the `melt` preset's base, the large dark/light expanse. */
  canvas?: string;
  /** The dots drawn over the field. */
  dots?: string;
  /** Control and card fill — what `bg-background` resolves to. */
  surface?: string;
  /** Text over the surface. */
  foreground?: string;
  primary?: string;
  secondary?: string;
  accent?: string;
}

/** One palette per mode. A mode absent from the blob simply has no
 * overrides — `app.css` answers for it. */
export type ThemePalettes = Partial<Record<ThemeMode, ThemeColors>>;

export interface ThemeConfig {
  mode?: ThemeMode;
  bgPreset?: ThemeBgPreset;
  sidebarSide?: SidebarSide;
  colors?: ThemePalettes;
  radius?: string;
}

export const DEFAULTS: { mode: ThemeMode; bgPreset: ThemeBgPreset; sidebarSide: SidebarSide } = {
  mode: "dark",
  bgPreset: "melt",
  sidebarSide: "left",
};

export const SIDEBAR_SIDES: readonly SidebarSide[] = ["left", "right"];

export const COLOR_KEYS: readonly (keyof ThemeColors)[] = [
  "canvas",
  "dots",
  "surface",
  "foreground",
  "primary",
  "secondary",
  "accent",
];

export const MODES: readonly ThemeMode[] = ["light", "dark"];

/** Which CSS custom property each editable color drives. `canvas` and `dots`
 * are the two the page actually shows; `surface` is the control fill the
 * retired `background` key used to write. */
export const COLOR_VARS: Record<keyof ThemeColors, string> = {
  canvas: "--canvas",
  dots: "--melt-dots-color",
  surface: "--background",
  foreground: "--foreground",
  primary: "--primary",
  secondary: "--secondary",
  accent: "--accent",
};

const COOKIE_NAME = "theme";

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

function isSidebarSide(value: unknown): value is SidebarSide {
  return value === "left" || value === "right";
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function sanitizePalette(value: Record<string, unknown>): ThemeColors {
  const palette: ThemeColors = {};
  for (const key of COLOR_KEYS) {
    const safe = sanitizeColor(value[key] as string | undefined);
    if (safe) palette[key] = safe;
  }
  return palette;
}

/** Narrows an arbitrary parsed value (cookie or `me.theme_config`) down to
 * the closed `ThemeConfig` shape, dropping unknown keys and any
 * enum/color/radius value that fails sanitization. Never throws. */
export function sanitizeThemeConfig(value: unknown): ThemeConfig {
  if (!isPlainObject(value)) return {};

  const blob: ThemeConfig = {};
  if (isMode(value.mode)) blob.mode = value.mode;
  if (isBgPreset(value.bgPreset)) blob.bgPreset = value.bgPreset;
  if (isSidebarSide(value.sidebarSide)) blob.sidebarSide = value.sidebarSide;

  if (isPlainObject(value.colors)) {
    const palettes: ThemePalettes = {};

    // Pre-per-mode shape was one flat palette shared by both modes, with
    // `background` where `surface` now is. Read as the palette of the mode
    // the same blob declares; the other mode stays unset.
    const legacy = sanitizePalette({
      ...value.colors,
      surface: value.colors.surface ?? value.colors.background,
    });
    if (Object.keys(legacy).length > 0) palettes[blob.mode ?? DEFAULTS.mode] = legacy;

    for (const mode of MODES) {
      if (!isPlainObject(value.colors[mode])) continue;
      const palette = sanitizePalette(value.colors[mode]);
      if (Object.keys(palette).length > 0) palettes[mode] = palette;
    }

    if (Object.keys(palettes).length > 0) blob.colors = palettes;
  }

  const safeRadius = sanitizeRadius(value.radius as string | undefined);
  if (safeRadius) blob.radius = safeRadius;

  return blob;
}

/** Parses a raw `theme` cookie value — handling both a still-URI-encoded
 * string and an already-decoded one — and defaults to `{}` on anything
 * missing or malformed. */
export function parseThemeConfig(raw: string | null | undefined): ThemeConfig {
  if (!raw) return {};
  const candidates = [raw];
  try {
    candidates.push(decodeURIComponent(raw));
  } catch {
    // raw wasn't URI-encoded
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

  const palette = blob?.colors?.[mode] ?? {};
  const styleParts: string[] = [];
  for (const key of COLOR_KEYS) {
    const safe = sanitizeColor(palette[key]);
    if (safe) styleParts.push(`${COLOR_VARS[key]}: ${safe}`);
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
 * change in AppearanceCard calls this before any `PATCH /api/me/` fires. */
export function applyTheme(
  blob: ThemeConfig | null | undefined,
  root: HTMLElement = document.documentElement,
): void {
  const attrs = computeThemeSSRAttrs(blob);
  root.classList.toggle("dark", attrs.htmlClass === "dark");
  root.setAttribute("data-bg-preset", attrs.dataBgPreset);

  const palette = blob?.colors?.[blob?.mode ?? DEFAULTS.mode] ?? {};
  for (const key of COLOR_KEYS) {
    const safe = sanitizeColor(palette[key]);
    const varName = COLOR_VARS[key];
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
 * `PATCH /api/me/` ([[API]]). Called ONLY after a `200` save response —
 * never from the live-preview path. */
export function writeThemeCookie(blob: ThemeConfig): void {
  if (typeof document === "undefined") return;
  const value = encodeURIComponent(JSON.stringify(blob));
  document.cookie = `${COOKIE_NAME}=${value}; Path=/; Max-Age=31536000; SameSite=Lax`;
}

/** Normalizes any CSS color the token set may hold — `oklch()`, `hsl()`,
 * `rgb()` — into hex: `#rrggbb`, or `#rrggbbaa` when the color is
 * translucent. Returns `undefined` for a value the browser cannot parse.
 *
 * Rasterizing is the only reliable conversion: paint one pixel and read
 * bytes (clamps wide-gamut tokens to sRGB — correct for a swatch). */
export function toHexColor(value: string): string | undefined {
  if (typeof document === "undefined") return undefined;
  const trimmed = value.trim();
  if (!trimmed) return undefined;

  const probe = document.createElement("span");
  probe.style.color = "#000000";
  probe.style.color = trimmed;
  if (probe.style.color === "") {
    probe.style.color = "#ffffff";
    probe.style.color = trimmed;
    if (probe.style.color === "") return undefined;
  }

  const canvas = document.createElement("canvas");
  canvas.width = 1;
  canvas.height = 1;
  const ctx = canvas.getContext("2d");
  if (!ctx) return undefined;
  ctx.fillStyle = "#000000";
  ctx.fillStyle = trimmed;
  if (ctx.fillStyle === "#000000" && !/^#?0+$/i.test(trimmed.replace(/\s/g, ""))) {
    // Ambiguous — try a second sentinel
    ctx.fillStyle = "#ffffff";
    ctx.fillStyle = trimmed;
    if (ctx.fillStyle === "#ffffff") return undefined;
  }
  ctx.fillRect(0, 0, 1, 1);
  const [r, g, b, a] = ctx.getImageData(0, 0, 1, 1).data;
  const hex = (n: number) => n.toString(16).padStart(2, "0");
  if (a < 255) return `#${hex(r)}${hex(g)}${hex(b)}${hex(a)}`;
  return `#${hex(r)}${hex(g)}${hex(b)}`;
}

/** Seeds unset palette keys from the live computed stylesheet so a control
 * the user has never set opens on the color that token actually paints. */
export function resolvePalette(
  existing: ThemeColors | undefined,
  root: HTMLElement = document.documentElement,
): ThemeColors {
  const resolved: ThemeColors = { ...(existing ?? {}) };
  const styles = getComputedStyle(root);
  for (const key of COLOR_KEYS) {
    if (resolved[key]) continue;
    const raw = styles.getPropertyValue(COLOR_VARS[key]).trim();
    if (!raw) continue;
    const hex = toHexColor(raw);
    if (hex) resolved[key] = hex;
  }
  return resolved;
}
