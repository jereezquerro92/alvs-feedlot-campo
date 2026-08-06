import { describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { resolveShellNav } from "../src/lib/components/shell/nav";

/**
 * adr-54 rule 3 — the menu is NEVER invisible. The regression this guards is a
 * layout gate: `Base.astro` used to require a client in the URL before mounting
 * FancyNav, so `/feedlot/precios`, `/feedlot/usuarios`, `/profile/` and the
 * component gallery rendered no chrome at all.
 */
const BASE = readFileSync(new URL("../src/layouts/Base.astro", import.meta.url), "utf8");

/** Pages whose URL carries no client — every one of them must still get a menu. */
const CLIENTLESS_PATHS = [
  "/feedlot/precios",
  "/feedlot/usuarios",
  "/feedlot/",
  "/profile/",
  "/showcase/components",
];

describe("Base.astro site-menu gate", () => {
  test("does not gate the menu on a client being present in the URL", () => {
    const gate = BASE.split("\n").find((line) => line.includes("const showShellNav"));
    expect(gate).toBeDefined();
    expect(gate).not.toContain("navClientId");
  });

  test("gates only on the session having a role", () => {
    expect(BASE).toContain("const showShellNav = shellNav && hasRole(me);");
  });
});

describe("resolveShellNav", () => {
  test("a missing client is null data, never an error", () => {
    for (const path of CLIENTLESS_PATHS) {
      const resolved = resolveShellNav(path, new URLSearchParams());
      expect(resolved.clientId).toBeNull();
      expect(typeof resolved.active).toBe("string");
    }
  });

  test("still reads the client from a numeric path and from ?client=", () => {
    expect(resolveShellNav("/feedlot/42/", new URLSearchParams()).clientId).toBe("42");
    expect(resolveShellNav("/feedlot/precios", new URLSearchParams("client=42")).clientId).toBe(
      "42",
    );
  });

  test("highlights the module even with no client", () => {
    expect(resolveShellNav("/feedlot/precios", new URLSearchParams()).active).toBe("prices");
    expect(resolveShellNav("/feedlot/usuarios", new URLSearchParams()).active).toBe("users");
  });
});
