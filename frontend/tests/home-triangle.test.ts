import { describe, expect, test } from "bun:test";
import { resolveAccessibleLabel, resolveHomeTarget } from "../src/lib/home-triangle";

// Unit coverage for HomeTriangle's action resolver (issue #255, adr-22
// rules 1-2). DOM-free, matching this template's bun:test conventions (no
// jsdom / svelte component-render harness in the repo).

describe("resolveHomeTarget", () => {
  test("zero props resolves to inert — no navigation, no callback (adr-22 rule 1/2 default)", () => {
    const target = resolveHomeTarget();
    expect(target).toEqual({ kind: "inert" });
  });

  test("an explicit href resolves to a link target (rung-1 plain anchor)", () => {
    const target = resolveHomeTarget("/");
    expect(target).toEqual({ kind: "link", href: "/" });
  });

  test("an explicit onHome resolves to an action target and is not invoked implicitly", () => {
    let called = false;
    const onHome = () => {
      called = true;
    };
    const target = resolveHomeTarget(undefined, onHome);
    expect(target.kind).toBe("action");
    expect(called).toBe(false);
    if (target.kind === "action") target.onHome();
    expect(called).toBe(true);
  });

  test("href takes precedence when both are supplied", () => {
    const target = resolveHomeTarget("/", () => {});
    expect(target.kind).toBe("link");
  });
});

// Coverage for the accessible-name resolver (issue #283, WCAG 4.1.2): an
// interactive branch (link/action) must never resolve to an empty or
// undefined name, with or without a caller-supplied `ariaLabel`.
describe("resolveAccessibleLabel", () => {
  test("inert target needs no accessible name", () => {
    const target = resolveHomeTarget();
    expect(resolveAccessibleLabel(target, undefined, "fallback")).toBeUndefined();
    expect(resolveAccessibleLabel(target, "", "fallback")).toBeUndefined();
  });

  test("link target with no ariaLabel falls back to the non-empty default", () => {
    const target = resolveHomeTarget("/");
    expect(resolveAccessibleLabel(target, undefined, "fallback")).toBe("fallback");
  });

  test("link target with an empty-string ariaLabel still falls back (never an empty name)", () => {
    const target = resolveHomeTarget("/");
    expect(resolveAccessibleLabel(target, "", "fallback")).toBe("fallback");
  });

  test("link target with a caller-supplied ariaLabel uses it verbatim", () => {
    const target = resolveHomeTarget("/");
    expect(resolveAccessibleLabel(target, "Go home", "fallback")).toBe("Go home");
  });

  test("action target with no ariaLabel falls back to the non-empty default", () => {
    const target = resolveHomeTarget(undefined, () => {});
    expect(resolveAccessibleLabel(target, undefined, "fallback")).toBe("fallback");
  });
});

const source = await Bun.file(
  new URL("../src/lib/components/primitives/HomeTriangle.svelte", import.meta.url),
).text();

describe("HomeTriangle.svelte source (static contract checks)", () => {
  test("uses design-system tokens only — no hardcoded hex or raw oklch literal", () => {
    // Strip issue references ("#255") before scanning for CSS hex literals —
    // they are not color codes.
    const withoutIssueRefs = source.replace(/#\d+/g, "");
    expect(withoutIssueRefs).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(source).not.toMatch(/oklch\(/);
    expect(source).toContain("bg-primary");
    expect(source).toContain("text-primary-foreground");
  });

  test("holds an inline SVG home icon, no icon-package import", () => {
    expect(source).toContain("<svg");
    expect(source).not.toMatch(/from ["'](lucide|@lucide|iconify)/);
  });

  test("href and onHome both default to undefined — no implicit navigation on zero-prop invocation", () => {
    expect(source).toMatch(/href\s*=\s*undefined/);
    expect(source).toMatch(/onHome\s*=\s*undefined/);
    expect(source).not.toMatch(/window\.location/);
  });

  test("interactive branches never render aria-label directly from the raw ariaLabel prop (issue #283)", () => {
    // Both <a> and <button> must read the resolved (never-empty) label, not
    // the raw caller prop, which may be omitted or empty.
    expect(source).not.toMatch(/aria-label=\{ariaLabel\}/);
    expect(source).toMatch(/aria-label=\{resolvedAriaLabel\}/g);
    expect(source).toContain("resolveAccessibleLabel");
    // No hardcoded English fallback string baked into the component — the
    // fallback comes from resolving an existing i18n key.
    expect(source).toContain('t("home_triangle_aria_label")');
  });
});
