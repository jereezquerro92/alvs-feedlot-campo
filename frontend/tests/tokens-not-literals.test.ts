import { describe, expect, test } from "bun:test";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

// Guards [[DESIGN-SYSTEM]] "Tokens, not literals": paint colors authored in
// components are a defect — they belong in the token SSOTs
// (`styles/app.css` developer tokens, `lib/theme-packs.ts` curated packs).
//
// Safe: text-search only, no DOM, no network. Mirrors the i18n orphan-key
// harness (issue #53 style). Shrink the MECHANICAL_ALLOWLIST when a literal
// moves into a token; do not widen it for convenience.

const SRC = fileURLToPath(new URL("../src/", import.meta.url));
const SOURCE_EXTENSIONS = [".ts", ".svelte", ".astro"];

/** Files allowed to author color values (the template / pack SSOTs). */
const TOKEN_SSOT_SUFFIXES = [
  "styles/app.css",
  "lib/theme-packs.ts",
];

/**
 * Files that may mention color syntax without painting UI chrome.
 * Keep this list tiny — prefer moving paint into app.css / theme-packs.ts.
 */
const MECHANICAL_FILES: ReadonlyArray<{ path: string; why: string }> = [
  {
    path: "lib/theme.ts",
    why: "sanitize regex + toHexColor rasterization sentinels (not paint)",
  },
  {
    path: "lib/components/theme/PaletteFields.svelte",
    why: "native color-input fallback reads --swatch-fallback; placeholder copy only",
  },
];

/** Tailwind / utility paint that bypasses the token layer. */
const TAILWIND_LITERALS =
  /\b(?:text-white|bg-white|bg-black|border-white|border-black|backdrop:bg-black)\b/;

/** CSS color functions / hex that paint UI.
 *  Hex is 6 or 8 digits only — 3-digit forms collide with issue refs (`#283`). */
const COLOR_LITERAL =
  /(?:oklch|oklab|lab|lch|hwb)\s*\(|(?:rgba?|hsla?)\s*\(|#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?\b/;

function sourceFiles(dir: string, acc: string[] = []): string[] {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      sourceFiles(full, acc);
    } else if (SOURCE_EXTENSIONS.some((ext) => entry.endsWith(ext))) {
      acc.push(full);
    }
  }
  return acc;
}

function rel(path: string): string {
  return relative(SRC, path).replaceAll("\\", "/");
}

function isTokenSsot(path: string): boolean {
  const r = rel(path);
  return TOKEN_SSOT_SUFFIXES.some((suffix) => r === suffix || r.endsWith(`/${suffix}`));
}

function isMechanical(path: string): boolean {
  const r = rel(path);
  return MECHANICAL_FILES.some((entry) => entry.path === r);
}

/** Strip block/line/HTML comments so issue refs and prose cannot trip the scan. */
function stripComments(source: string): string {
  return source
    .replace(/<!--[\s\S]*?-->/g, "")
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/(^|[^:])\/\/.*$/gm, "$1");
}

function findOffenders(
  files: string[],
  pattern: RegExp,
): Array<{ file: string; line: number; snippet: string }> {
  const hits: Array<{ file: string; line: number; snippet: string }> = [];
  for (const file of files) {
    if (isTokenSsot(file) || isMechanical(file)) continue;
    const cleaned = stripComments(readFileSync(file, "utf-8"));
    const lines = cleaned.split("\n");
    lines.forEach((line, idx) => {
      if (pattern.test(line)) {
        hits.push({
          file: rel(file),
          line: idx + 1,
          snippet: line.trim().slice(0, 120),
        });
      }
    });
  }
  return hits;
}

const consumers = sourceFiles(SRC);

describe("tokens, not literals ([[DESIGN-SYSTEM]])", () => {
  test("component source does not paint with hex/oklch/rgb/hsl literals", () => {
    const hits = findOffenders(consumers, COLOR_LITERAL);
    expect(
      hits,
      hits
        .map((h) => `${h.file}:${h.line}: ${h.snippet}`)
        .join("\n") || "clean",
    ).toEqual([]);
  });

  test("component source does not use Tailwind white/black paint utilities", () => {
    const hits = findOffenders(consumers, TAILWIND_LITERALS);
    expect(
      hits,
      hits
        .map((h) => `${h.file}:${h.line}: ${h.snippet}`)
        .join("\n") || "clean",
    ).toEqual([]);
  });

  test("every MECHANICAL_FILES path still exists (no silent dead entries)", () => {
    for (const entry of MECHANICAL_FILES) {
      const full = join(SRC, entry.path);
      expect(statSync(full).isFile(), `missing mechanical file ${entry.path} (${entry.why})`).toBe(
        true,
      );
    }
  });
});

describe("theme packs stay synced with the app.css template", () => {
  const css = readFileSync(join(SRC, "styles/app.css"), "utf-8");
  const packs = readFileSync(join(SRC, "lib/theme-packs.ts"), "utf-8");

  function cssToken(selector: string, name: string): string {
    // Prefer the declaration that sits inside the named rule; when several
    // `:root` blocks exist, take the one that actually defines this token.
    const re = new RegExp(
      `${selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s*\\{[^}]*?${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s*:\\s*([^;]+);`,
      "s",
    );
    const m = css.match(re);
    expect(m, `missing ${name} under ${selector}`).toBeTruthy();
    return m![1].trim();
  }

  test("kodexArg pack primary matches :root / .dark --primary", () => {
    const light = cssToken(":root", "--primary");
    const dark = cssToken(".dark", "--primary");
    expect(packs).toContain(`primary: "${light}"`);
    expect(packs).toContain(`primary: "${dark}"`);
  });

  test("Jeremías pack primary matches .feedlot-app / .dark .feedlot-app --primary", () => {
    const light = cssToken(".feedlot-app", "--primary");
    const dark = cssToken(".dark .feedlot-app", "--primary");
    expect(light).toBe("oklch(0.52 0.12 152)");
    expect(dark).toBe("oklch(0.68 0.13 152)");
    expect(packs).toContain(`primary: "${light}"`);
    expect(packs).toContain(`primary: "${dark}"`);
  });

  test("kodexArg pack canvas matches :root / .dark --canvas", () => {
    const light = cssToken(":root", "--canvas");
    const dark = cssToken(".dark", "--canvas");
    expect(packs).toContain(`canvas: "${light}"`);
    expect(packs).toContain(`canvas: "${dark}"`);
  });

  test("app.css still ships --swatch-fallback and --scrim-bg tokens", () => {
    expect(css).toMatch(/--swatch-fallback:\s*#[0-9a-fA-F]{6}/);
    expect(css).toMatch(/--scrim-bg:/);
    expect(css).toMatch(/--destructive-foreground:/);
    expect(css).toMatch(/--corner-nav-shadow:/);
    expect(css).toMatch(/--corner-nav-edge:/);
  });
});
