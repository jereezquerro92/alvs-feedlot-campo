import { describe, expect, test } from "bun:test";
import {
  DEFAULTS,
  COLOR_VARS,
  computeThemeSSRAttrs,
  parseThemeConfig,
  sanitizeColor,
  sanitizeRadius,
  sanitizeThemeConfig,
} from "../src/lib/theme";
import {
  THEME_PACK_IDS,
  themeConfigFromPack,
  isThemePackId,
} from "../src/lib/theme-packs";

// Unit coverage for the theme contract's DOM-free helpers. Mirrors
// docs/API.md's PATCH /api/me/ theme_config validation — same rules Django
// enforces server-side, re-applied client-side for live-preview and SSR.

describe("sanitizeColor", () => {
  test("accepts hex, rgb(a), hsl, and oklch forms", () => {
    expect(sanitizeColor("#fff")).toBe("#fff");
    expect(sanitizeColor("rgb(0, 0, 0)")).toBe("rgb(0, 0, 0)");
    expect(sanitizeColor("rgba(0, 0, 0, 0.5)")).toBe("rgba(0, 0, 0, 0.5)");
    expect(sanitizeColor("hsl(210 40% 50%)")).toBe("hsl(210 40% 50%)");
    expect(sanitizeColor("oklch(0.7 0.1 250)")).toBe("oklch(0.7 0.1 250)");
  });

  test("rejects an out-of-family string", () => {
    expect(sanitizeColor("not-a-color")).toBeUndefined();
    expect(sanitizeColor(undefined)).toBeUndefined();
  });

  test("rejects an injection attempt regardless of matching the color shape", () => {
    expect(sanitizeColor("oklch(0.7 0.1 250); background: url(javascript:alert(1))")).toBeUndefined();
    expect(sanitizeColor("red;}<script>expression(alert(1))")).toBeUndefined();
    expect(sanitizeColor('oklch(0 0 0)" onmouseover="alert(1)')).toBeUndefined();
  });
});

describe("sanitizeRadius", () => {
  test("accepts a plain CSS length", () => {
    expect(sanitizeRadius("0.625rem")).toBe("0.625rem");
    expect(sanitizeRadius("8px")).toBe("8px");
  });

  test("rejects a malformed or injected value", () => {
    expect(sanitizeRadius("10rem; background: red")).toBeUndefined();
    expect(sanitizeRadius("not-a-length")).toBeUndefined();
    expect(sanitizeRadius(undefined)).toBeUndefined();
  });
});

describe("sanitizeThemeConfig", () => {
  test("keeps only the closed key set with valid per-mode values", () => {
    const blob = sanitizeThemeConfig({
      mode: "dark",
      bgPreset: "melt",
      sidebarSide: "right",
      colors: {
        dark: { canvas: "oklch(0.1 0 0)", primary: "not-a-color" },
        light: { primary: "oklch(0.6 0.1 45)" },
      },
      radius: "0.5rem",
      unknownKey: "danger",
    });
    expect(blob).toEqual({
      mode: "dark",
      bgPreset: "melt",
      sidebarSide: "right",
      colors: {
        dark: { canvas: "oklch(0.1 0 0)" },
        light: { primary: "oklch(0.6 0.1 45)" },
      },
      radius: "0.5rem",
    });
  });

  test("reads a legacy flat palette under the declared mode as surface", () => {
    const blob = sanitizeThemeConfig({
      mode: "light",
      colors: { background: "#ffffff", primary: "oklch(0.6 0.1 45)" },
    });
    expect(blob.colors?.light).toEqual({
      surface: "#ffffff",
      primary: "oklch(0.6 0.1 45)",
    });
    expect(blob.colors?.dark).toBeUndefined();
  });

  test("drops an out-of-enum mode/bgPreset/sidebarSide instead of defaulting silently", () => {
    const blob = sanitizeThemeConfig({
      mode: "purple",
      bgPreset: "wallpaper",
      sidebarSide: "top",
    });
    expect(blob.mode).toBeUndefined();
    expect(blob.bgPreset).toBeUndefined();
    expect(blob.sidebarSide).toBeUndefined();
  });

  test("returns {} for a non-object value", () => {
    expect(sanitizeThemeConfig(null)).toEqual({});
    expect(sanitizeThemeConfig("dark")).toEqual({});
    expect(sanitizeThemeConfig([1, 2, 3])).toEqual({});
  });
});

describe("parseThemeConfig", () => {
  test("parses a URI-encoded JSON cookie value", () => {
    const raw = encodeURIComponent(JSON.stringify({ mode: "dark", bgPreset: "melt" }));
    expect(parseThemeConfig(raw)).toEqual({ mode: "dark", bgPreset: "melt" });
  });

  test("parses an already-decoded JSON string too", () => {
    const raw = JSON.stringify({ mode: "light" });
    expect(parseThemeConfig(raw)).toEqual({ mode: "light" });
  });

  test("defaults to {} on missing or malformed input", () => {
    expect(parseThemeConfig(undefined)).toEqual({});
    expect(parseThemeConfig("{not json")).toEqual({});
  });
});

describe("computeThemeSSRAttrs", () => {
  test("defaults to DEFAULTS.mode/DEFAULTS.bgPreset, no inline overrides", () => {
    const attrs = computeThemeSSRAttrs(null);
    expect(attrs.htmlClass).toBe(DEFAULTS.mode === "dark" ? "dark" : "");
    expect(attrs.dataBgPreset).toBe(DEFAULTS.bgPreset);
    expect(attrs.style).toBe("");
  });

  test("dark mode sets the html class; melt preset sets data-bg-preset", () => {
    const attrs = computeThemeSSRAttrs({ mode: "dark", bgPreset: "melt" });
    expect(attrs.htmlClass).toBe("dark");
    expect(attrs.dataBgPreset).toBe("melt");
  });

  test("an explicit non-default value is preserved, never forced back to DEFAULTS", () => {
    expect(computeThemeSSRAttrs({ mode: "light" }).htmlClass).toBe("");
    expect(computeThemeSSRAttrs({ bgPreset: "default" }).dataBgPreset).toBe("default");
  });

  test("only the active mode's sanitized overrides reach the inline style", () => {
    const attrs = computeThemeSSRAttrs({
      mode: "dark",
      colors: {
        dark: { canvas: "oklch(0.2 0 0)", primary: "javascript:alert(1)" },
        light: { canvas: "oklch(0.9 0 0)" },
      },
      radius: "1rem",
    });
    expect(attrs.style).toContain(`${COLOR_VARS.canvas}: oklch(0.2 0 0)`);
    expect(attrs.style).toContain("--radius: 1rem");
    expect(attrs.style).not.toContain("--primary");
    expect(attrs.style).not.toContain("oklch(0.9 0 0)");
  });
});

describe("theme packs", () => {
  test("every pack id is recognized and yields a valid dual-mode ThemeConfig", () => {
    for (const id of THEME_PACK_IDS) {
      expect(isThemePackId(id)).toBe(true);
      const blob = themeConfigFromPack(id);
      expect(blob.colors?.light?.primary).toBeTruthy();
      expect(blob.colors?.dark?.primary).toBeTruthy();
      expect(blob.colors?.light?.canvas).toBeTruthy();
      expect(blob.colors?.dark?.dots).toBeTruthy();
      // Round-trip through sanitize must keep the pack intact
      expect(sanitizeThemeConfig(blob)).toEqual(blob);
    }
  });

  test("kodexArg primary is orange-ish (hue near 45)", () => {
    const blob = themeConfigFromPack("kodexarg");
    expect(blob.colors?.dark?.primary).toContain("45");
    expect(blob.colors?.light?.primary).toContain("45");
  });

  test("Jeremías primary is emerald (hue near 152) from .feedlot-app", () => {
    const blob = themeConfigFromPack("jeremias");
    expect(blob.colors?.light?.primary).toBe("oklch(0.52 0.12 152)");
    expect(blob.colors?.dark?.primary).toBe("oklch(0.68 0.13 152)");
  });

  test("Militar primary is olive (hue near 120), distinct from Jeremías", () => {
    const blob = themeConfigFromPack("militar");
    expect(blob.colors?.light?.primary).toContain("120");
    expect(blob.colors?.light?.primary).not.toContain("152");
  });

  test("applying a pack preserves mode/bgPreset/sidebarSide from the base blob", () => {
    const blob = themeConfigFromPack("amber", {
      mode: "light",
      bgPreset: "default",
      sidebarSide: "right",
      radius: "1rem",
    });
    expect(blob.mode).toBe("light");
    expect(blob.bgPreset).toBe("default");
    expect(blob.sidebarSide).toBe("right");
    expect(blob.radius).toBe("1rem");
    expect(blob.colors?.light?.primary).toContain("60");
  });
});
