import { describe, expect, test } from "bun:test";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { messages } from "../src/i18n/messages";

// Guards `src/i18n/messages/es.ts` against dead copy (issue #53): 32 keys had
// accumulated that nothing rendered, three of them left behind when
// LobbyView.svelte was deleted in #43. Nothing was watching, so they stayed.
//
// The check is a text search for each key across `src/`, which is only sound
// because this codebase never builds a key at run time. That is not an
// assumption — `assert no key is assembled dynamically` below is what makes the
// orphan search trustworthy, and it fails the moment someone writes
// `` t(`prefix_${x}`) ``. If that day comes, this test is the place to add an
// explicit allowlist of dynamically-reached keys; silently loosening the
// orphan check instead would turn it into decoration.
//
// `t(key: MessageKey)` is typed against `keyof typeof es`, so `astro check`
// already catches the opposite error — a reference to a key that does not
// exist. This test covers the direction the typechecker cannot see.

const SRC = fileURLToPath(new URL("../src/", import.meta.url));
const MESSAGES_DIR = "i18n/messages";
const SOURCE_EXTENSIONS = [".ts", ".svelte", ".astro"];

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

/** Every source file except the message catalogues themselves — a key
 *  appearing only in `es.ts` is precisely what counts as an orphan. */
const consumers = sourceFiles(SRC).filter(
  (f) => !f.replaceAll("\\", "/").includes(MESSAGES_DIR),
);
const haystack = consumers.map((f) => readFileSync(f, "utf-8")).join("\n");

describe("i18n message catalogue", () => {
  test("no key is assembled dynamically, so a text search can find every reference", () => {
    // The two genuinely dynamic call sites — AsesorChat's `MessageKey[]`
    // groups and router-client's OUTCOME_COPY map — both spell their keys out
    // as literals, so they are found. What must not exist is a key built from
    // a template literal or widened by a cast, either of which would leave a
    // live key with no literal anywhere and make it read as an orphan.
    const evasions = [
      { pattern: /\bt\(`/, what: "a template-literal t() call" },
      { pattern: /as\s+MessageKey\b/, what: "an `as MessageKey` cast" },
    ];

    for (const { pattern, what } of evasions) {
      const offenders = consumers.filter((f) => pattern.test(readFileSync(f, "utf-8")));
      expect(
        offenders,
        `${what} defeats the orphan search below; add an explicit allowlist ` +
          `for the keys it reaches instead of weakening the check`,
      ).toEqual([]);
    }
  });

  test("every message key is referenced by something that renders it", () => {
    const keys = Object.keys(messages.es);
    expect(keys.length).toBeGreaterThan(0);

    const orphans = keys.filter(
      (key) => !new RegExp(`\\b${key}\\b`).test(haystack),
    );

    expect(
      orphans,
      `${orphans.length} message key(s) are rendered by nothing. Remove them, ` +
        `or wire up the copy they were written for — copy for a feature that ` +
        `does not exist yet is added with that feature, not ahead of it`,
    ).toEqual([]);
  });
});
