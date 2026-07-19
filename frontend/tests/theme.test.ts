import { describe, expect, test } from "bun:test";
import {
  DEFAULTS,
  computeThemeSSRAttrs,
  parseThemeConfig,
  sanitizeColor,
  sanitizeRadius,
  sanitizeThemeConfig,
} from "../src/lib/theme";

// Unit coverage for the theme contract's DOM-free helpers (bdd-06:
// "Persistence across login — no flash", "Invalid custom value is
// rejected"). Mirrors docs/API.md's PATCH /api/me/ `theme_config`
// validation exactly — these are the same rules Django enforces
// server-side, re-applied client-side for the live-preview path and the
// SSR no-flash render. No jsdom, matching this template's bun:test
// conventions (optimistic-toggle.test.ts).

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
  test("keeps only the closed key set with valid values", () => {
    const blob = sanitizeThemeConfig({
      mode: "dark",
      bgPreset: "melt",
      colors: { background: "oklch(0.1 0 0)", primary: "not-a-color" },
      radius: "0.5rem",
      unknownKey: "danger",
    });
    expect(blob).toEqual({
      mode: "dark",
      bgPreset: "melt",
      colors: { background: "oklch(0.1 0 0)" },
      radius: "0.5rem",
    });
  });

  test("drops an out-of-enum mode/bgPreset instead of defaulting silently", () => {
    const blob = sanitizeThemeConfig({ mode: "purple", bgPreset: "wallpaper" });
    expect(blob.mode).toBeUndefined();
    expect(blob.bgPreset).toBeUndefined();
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

  test("an explicit non-default value is preserved, never forced back to DEFAULTS (regression: presence, not equality)", () => {
    // A saved theme_config of mode:"light" / bgPreset:"default" must survive
    // even though DEFAULTS is now dark/melt — resolving by `=== "dark"` /
    // `=== "melt"` equality instead of by presence (`??`) would silently
    // discard an explicitly-saved light/default choice back to the new
    // DEFAULTS, regressing bdd-06's user-configurable-theme guarantee.
    expect(computeThemeSSRAttrs({ mode: "light" }).htmlClass).toBe("");
    expect(computeThemeSSRAttrs({ bgPreset: "default" }).dataBgPreset).toBe("default");
  });

  test("only sanitized, present color/radius overrides reach the inline style", () => {
    const attrs = computeThemeSSRAttrs({
      colors: { background: "oklch(0.2 0 0)", primary: "javascript:alert(1)" },
      radius: "1rem",
    });
    expect(attrs.style).toContain("--background: oklch(0.2 0 0)");
    expect(attrs.style).toContain("--radius: 1rem");
    expect(attrs.style).not.toContain("--primary");
  });
});
