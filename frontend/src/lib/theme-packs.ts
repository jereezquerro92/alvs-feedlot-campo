/* LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-52-frontend-and-design-system]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

// Closed theme-pack presets — curated ThemeConfig blobs that fill
// AppearanceCard. Packs are client-side composition over the closed
// theme_config contract; they do not add a persisted pack id ([[API]],
// [[DESIGN-SYSTEM]]). Applying a pack live-previews; Save PATCHes colors.

import {
  DEFAULTS,
  sanitizeThemeConfig,
  type ThemeColors,
  type ThemeConfig,
  type ThemeMode,
} from "$lib/theme";
import type { MessageKey } from "../i18n";

export type ThemePackId = "kodexarg" | "jeremias" | "militar" | "amber";

export const THEME_PACK_IDS: readonly ThemePackId[] = [
  "kodexarg",
  "jeremias",
  "militar",
  "amber",
];

export const THEME_PACK_LABELS: Record<ThemePackId, MessageKey> = {
  kodexarg: "appearance_pack_kodexarg",
  jeremias: "appearance_pack_jeremias",
  militar: "appearance_pack_militar",
  amber: "appearance_pack_amber",
};

/** Rationed-orange from app.css `:root` / `.dark` — the /profile default. */
const KODEXARG: Record<ThemeMode, ThemeColors> = {
  light: {
    canvas: "oklch(0.94 0.006 55)",
    dots: "oklch(0.90 0.05 75)",
    surface: "oklch(0.985 0.004 60)",
    foreground: "oklch(0.18 0.015 50)",
    primary: "oklch(0.64 0.19 45)",
    secondary: "oklch(0.96 0.010 55)",
    accent: "oklch(0.93 0.030 55)",
  },
  dark: {
    canvas: "oklch(0.12 0.008 50)",
    dots: "oklch(0.48 0.13 45 / 0.25)",
    surface: "oklch(0.16 0.010 50)",
    foreground: "oklch(0.91 0.008 60)",
    primary: "oklch(0.72 0.16 45)",
    secondary: "oklch(0.28 0.015 50)",
    accent: "oklch(0.30 0.030 55)",
  },
};

/**
 * Jeremías emerald — exact `.feedlot-app` primary/ring hues from commit
 * f4af45f (Jeremias Ezquerro, 2026-07-28), with warm neutrals shifted toward
 * forest so the pack reads as the operational green brand on /profile too.
 * Sidebar/chart tokens stay developer-owned under `.feedlot-app` in app.css.
 */
const JEREMIAS: Record<ThemeMode, ThemeColors> = {
  light: {
    canvas: "oklch(0.94 0.012 150)",
    dots: "oklch(0.82 0.04 152)",
    surface: "oklch(0.985 0.008 150)",
    foreground: "oklch(0.18 0.03 150)",
    primary: "oklch(0.52 0.12 152)",
    secondary: "oklch(0.94 0.02 150)",
    accent: "oklch(0.90 0.04 152)",
  },
  dark: {
    canvas: "oklch(0.12 0.015 155)",
    dots: "oklch(0.45 0.08 152 / 0.35)",
    surface: "oklch(0.16 0.02 155)",
    foreground: "oklch(0.95 0.015 150)",
    primary: "oklch(0.68 0.13 152)",
    secondary: "oklch(0.26 0.03 155)",
    accent: "oklch(0.30 0.05 152)",
  },
};

/** Olive Militar — syv-theme `#7B8A4E` family (H≈120), distinct from Jeremías. */
const MILITAR: Record<ThemeMode, ThemeColors> = {
  light: {
    canvas: "oklch(0.94 0.01 120)",
    dots: "oklch(0.80 0.04 120)",
    surface: "oklch(0.98 0.006 120)",
    foreground: "oklch(0.18 0.02 120)",
    primary: "oklch(0.607 0.085 120.5)",
    secondary: "oklch(0.94 0.02 120)",
    accent: "oklch(0.88 0.05 120)",
  },
  dark: {
    canvas: "oklch(0.12 0.012 130)",
    dots: "oklch(0.45 0.06 120 / 0.35)",
    surface: "oklch(0.15 0.015 130)",
    foreground: "oklch(0.95 0.01 90)",
    primary: "oklch(0.65 0.09 120)",
    secondary: "oklch(0.24 0.02 130)",
    accent: "oklch(0.30 0.04 120)",
  },
};

/** Golden amber — Alt 2 commented in app.css. */
const AMBER: Record<ThemeMode, ThemeColors> = {
  light: {
    canvas: "oklch(0.94 0.01 70)",
    dots: "oklch(0.88 0.05 70)",
    surface: "oklch(0.985 0.006 70)",
    foreground: "oklch(0.18 0.02 60)",
    primary: "oklch(0.70 0.16 60)",
    secondary: "oklch(0.95 0.02 70)",
    accent: "oklch(0.92 0.04 65)",
  },
  dark: {
    canvas: "oklch(0.12 0.012 60)",
    dots: "oklch(0.48 0.10 60 / 0.30)",
    surface: "oklch(0.16 0.015 55)",
    foreground: "oklch(0.92 0.01 70)",
    primary: "oklch(0.76 0.14 60)",
    secondary: "oklch(0.28 0.02 55)",
    accent: "oklch(0.32 0.04 60)",
  },
};

const PACK_PALETTES: Record<ThemePackId, Record<ThemeMode, ThemeColors>> = {
  kodexarg: KODEXARG,
  jeremias: JEREMIAS,
  militar: MILITAR,
  amber: AMBER,
};

/** Builds a sanitized ThemeConfig that applies the named pack's dual palettes
 * onto the current mode/bgPreset/sidebarSide/radius (or defaults). */
export function themeConfigFromPack(
  id: ThemePackId,
  base?: ThemeConfig | null,
): ThemeConfig {
  const palettes = PACK_PALETTES[id];
  return sanitizeThemeConfig({
    mode: base?.mode ?? DEFAULTS.mode,
    bgPreset: base?.bgPreset ?? DEFAULTS.bgPreset,
    sidebarSide: base?.sidebarSide ?? DEFAULTS.sidebarSide,
    radius: base?.radius,
    colors: {
      light: { ...palettes.light },
      dark: { ...palettes.dark },
    },
  });
}

export function isThemePackId(value: unknown): value is ThemePackId {
  return typeof value === "string" && (THEME_PACK_IDS as readonly string[]).includes(value);
}
