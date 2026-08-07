import { describe, expect, test } from "bun:test";
import { Glob } from "bun";
import path from "node:path";
import { es } from "../src/i18n/messages/es";

// The automated backstop for the rendered catalog, and the counterpart to
// component-mount.test.ts: that suite proves a component does not THROW, this
// one proves that what it renders is real Spanish.
//
// Two failure modes were invisible to every other gate. A missing i18n key
// resolves to `undefined` and renders the literal word rather than raising, so
// typecheck, build and every mount test stay green while the screen reads
// "undefined". And a glyph baked into a catalog value breaches the design
// ruling that iconography is presentation, which no typechecker can see.
//
// Self-discovering, like its sibling: it walks the whole source tree and reads
// the catalog whole, so a component or a key that lands tomorrow is covered
// with no list to remember to update.
//
// Deliberately DOM-free. `bun test` runs every file in one process and
// happy-dom may be registered only once — component-mount.test.ts owns that
// registration. Checking key RESOLUTION statically is also strictly better
// diagnostics than checking rendered output: it names the offending file and
// key instead of showing the word "undefined" inside a wall of markup.

const SRC = path.join(import.meta.dir, "..", "src");
const CATALOG_KEYS = new Set(Object.keys(es));

/**
 * Every catalog key a source file references, by the two routes that exist:
 * a direct `t("key")` call, and a lookup table typed `Record<…, MessageKey>`
 * whose values are keys reached indirectly. The second route is the one that
 * hides from a naive grep — a key that never appears as a literal `t("…")`.
 */
function referencedKeys(source: string): Set<string> {
  const keys = new Set<string>();
  for (const m of source.matchAll(/\bt\(\s*"([a-z][a-z0-9_]*)"\s*\)/g)) keys.add(m[1]);
  for (const block of source.matchAll(/MessageKey>\s*=\s*\{([\s\S]*?)\n\s*\};/g)) {
    for (const v of block[1].matchAll(/:\s*"([a-z][a-z0-9_]*)"/g)) keys.add(v[1]);
  }
  return keys;
}

function sourceFiles(): string[] {
  const glob = new Glob("**/*.{svelte,ts}");
  return [...glob.scanSync(SRC)]
    .map((p) => p.replaceAll(path.sep, "/"))
    .filter((p) => !p.startsWith("i18n/messages/"))
    .sort();
}

const files = sourceFiles();

describe("catalog completeness — every referenced key exists", () => {
  test("the suite discovers real subjects (a broken glob must fail, not silently pass)", () => {
    expect(files.length).toBeGreaterThan(50);
    expect(CATALOG_KEYS.size).toBeGreaterThan(100);
  });

  test("the extractor sees both routes a key is reached by", () => {
    const probe = referencedKeys(
      'const M: Record<X, MessageKey> = {\n  a: "mapped_key",\n};\nt("direct_key")',
    );
    expect([...probe].sort()).toEqual(["direct_key", "mapped_key"]);
  });

  // One test per file: a failure names the file, so the owning worker is
  // obvious without reading a combined report.
  for (const rel of files) {
    const source = Bun.file(path.join(SRC, rel)).text();
    test(`${rel} references no key missing from the catalog`, async () => {
      const missing = [...referencedKeys(await source)]
        .filter((key) => !CATALOG_KEYS.has(key))
        .sort();
      expect(`${rel} missing: ${missing.join(", ")}`).toBe(`${rel} missing: `);
    });
  }
});

describe("catalog values — no glyph is baked into translatable copy", () => {
  // Owner ruling, delegated to the design system: an emoji or icon glyph is
  // PRESENTATION and belongs to a component prop or an icon slot, never to
  // translatable copy ([[DESIGN-SYSTEM]], adr-04 r5). Baking one in also puts
  // iconography outside theming control and renders inconsistently across
  // platforms.
  //
  // Punctuation is not iconography: the em dash carries the qualifier pattern
  // ("Cheques en Cartera — al cobro") and the `+` in "COMPROMISOS (vencidos +
  // hoy)" is text. Only pictographic and dingbat ranges fail.
  // `∀-⋿` (Mathematical Operators) is in the set because of `≈`, the
  // glyph the ruling actually had to strip — it is neither an emoji nor a
  // dingbat, and an emoji-only pattern would have let it through. The meta-test
  // below is what caught that omission.
  const PICTOGRAPHIC =
    /[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2190}-\u{21FF}\u{2200}-\u{22FF}\u{2300}-\u{23FF}\u{25A0}-\u{25FF}\u{2B00}-\u{2BFF}\u{FE0F}\u{203C}\u{2049}]/u;

  test("the pattern actually detects the glyphs the ruling names", () => {
    for (const glyph of ["✅", "⚠️", "≈", "✓", "🏦", "📋", "↩"]) {
      expect(`${glyph} sample`).toMatch(PICTOGRAPHIC);
    }
    // and leaves real copy alone
    for (const copy of ["Cheques en Cartera — al cobro", "COMPROMISOS (vencidos + hoy)", "Equiv. $"]) {
      expect(copy).not.toMatch(PICTOGRAPHIC);
    }
  });

  test("every value in es.ts is glyph-free", () => {
    const offenders = Object.entries(es)
      .filter(([, value]) => PICTOGRAPHIC.test(value as string))
      .map(([key, value]) => `${key} = ${value}`);
    expect(offenders).toEqual([]);
  });

  test("every value in es.ts is a non-empty string", () => {
    const offenders = Object.entries(es)
      .filter(([, value]) => typeof value !== "string" || (value as string).length === 0)
      .map(([key]) => key);
    expect(offenders).toEqual([]);
  });
});
