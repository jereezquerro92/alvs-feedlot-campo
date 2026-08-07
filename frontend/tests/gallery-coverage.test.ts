import { describe, expect, test } from "bun:test";
import { Glob } from "bun";
import path from "node:path";
import { GALLERY_REGISTRY } from "../src/lib/components/showcase/galleryRegistry";

// The automated backstop for the showcase gallery's own decay, adapted from
// the alvs-financial-gateway suite of the same name: docs/COMPONENTIZATION.md
// names exactly this shape — "an enumerated list of subjects decays back into
// the code-review-only enforcement the harness replaces" — of
// component-mount.test.ts's own `discover()`/`CONTEXT_BOUND` pair, one layer
// up. This suite does not re-render anything (that stays
// component-mount.test.ts's job); it only asks whether every `.svelte` file
// under the tracked categories has a documented fate: a `GALLERY_REGISTRY`
// row (it IS exhibited) or a `GALLERY_EXCLUDED` entry (it is deliberately
// not, for a stated, named reason). A file in neither bucket is silent
// drift — exactly what decayed the gateway's gallery to ~26% coverage before
// this test existed there.
const COMPONENTS_ROOT = path.join(import.meta.dir, "..", "src", "lib", "components");

// The twelve categories the template's galleryRegistry.ts covers in full.
// Deliberately narrower than component-mount.test.ts's whole-tree Glob:
// - ui/ is the vendored shadcn layer — most of its atoms are composition
//   material, not gallery subjects; the registry's six ui/ rows are still
//   validated for existence below ("ui rows").
// - views/ is page bodies, never gallery tiles, per COMPONENTIZATION.md's
//   rung split.
// - header/ (LayoutHeader/NavBar) is one-instance layout chrome exhibited by
//   every page through Base.astro, like PageCanvas — not a gallery tile.
// Widening this list is a deliberate, separate decision.
const TRACKED_CATEGORIES = [
  "primitives",
  "data",
  "dashboard",
  "form",
  "nav",
  "chat",
  "overlay",
  "feedback",
  "auth",
  "theme",
  "shell",
  "showcase",
] as const;

// Named, exact, justified exclusions — never a directory-wide wildcard, for
// the same reason CONTEXT_BOUND never is: a wildcard would silently swallow
// the next new file dropped into an excluded folder, exactly the drift this
// test exists to catch.
//
// Today the list is EMPTY on purpose: the ported registry covers every
// `.svelte` file under the twelve tracked categories. The mechanism stays so
// the first genuinely non-exhibitable component (a mutation-owning island
// wrapper, a domain-propped control) has a sanctioned, reviewable place to
// land — with its justification written next to its name.
const GALLERY_EXCLUDED: string[] = [];

function discoverTracked(): string[] {
  const found: string[] = [];
  for (const category of TRACKED_CATEGORIES) {
    const glob = new Glob("**/*.svelte");
    for (const rel of glob.scanSync(path.join(COMPONENTS_ROOT, category))) {
      found.push(`${category}/${rel.replaceAll(path.sep, "/")}`);
    }
  }
  return found.sort();
}

function discoverAll(): string[] {
  const glob = new Glob("**/*.svelte");
  return [...glob.scanSync(COMPONENTS_ROOT)].map((p) => p.replaceAll(path.sep, "/")).sort();
}

const trackedSubjects = discoverTracked();
const allComponents = discoverAll();
const registryPaths = new Set(GALLERY_REGISTRY.map((entry) => entry.path));
const excludedPaths = new Set(GALLERY_EXCLUDED);

describe("gallery coverage — every tracked-category component has a documented fate", () => {
  test("the suite discovers real subjects (a broken glob must fail, not silently pass)", () => {
    expect(trackedSubjects.length).toBeGreaterThan(50);
  });

  test("TRACKED_CATEGORIES matches the registry's non-ui categories exactly", () => {
    const registryCategories = [
      ...new Set(
        GALLERY_REGISTRY.map((entry) => entry.category).filter((category) => category !== "ui"),
      ),
    ].sort();
    expect(registryCategories).toEqual([...TRACKED_CATEGORIES].sort());
  });

  test("every GALLERY_EXCLUDED entry names a component that actually exists", () => {
    for (const rel of GALLERY_EXCLUDED) {
      expect(allComponents).toContain(rel);
    }
  });

  test("every GALLERY_REGISTRY entry names a component that actually exists", () => {
    for (const entry of GALLERY_REGISTRY) {
      expect(allComponents).toContain(entry.path);
    }
  });

  test("GALLERY_REGISTRY and GALLERY_EXCLUDED never claim the same path", () => {
    const overlap = GALLERY_REGISTRY.map((entry) => entry.path).filter((p) => excludedPaths.has(p));
    expect(overlap).toEqual([]);
  });

  for (const rel of trackedSubjects) {
    test(`${rel} is in GALLERY_REGISTRY or a named, justified GALLERY_EXCLUDED entry`, () => {
      const covered = registryPaths.has(rel) || excludedPaths.has(rel);
      expect(covered).toBe(true);
    });
  }
});
