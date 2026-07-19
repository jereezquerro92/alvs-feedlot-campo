import { describe, expect, test } from "bun:test";
import { Glob } from "bun";
import path from "node:path";
import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { compile, compileModule } from "svelte/compiler";

// The automated backstop for adr-22 rule 1 (issue #282): every component
// mounts with zero props and never throws. The suite discovers its own
// subjects — a new `.svelte` file under src/lib/components/ is covered the
// moment it lands, with no list to remember to update. That self-discovery
// is the point: an enumerated list would drift back into the manual,
// code-review-only enforcement this test exists to replace.
//
// This is the repo's first DOM-bearing test.

// `bun test` runs every file in one process, so registering a DOM here is
// unavoidably global. That is fine for the DOM itself, but happy-dom also
// substitutes the HTTP globals, and its CORS-enforcing versions break
// smoke.test.ts's SSR server and stub backend. No test wants a browser's
// HTTP stack, so Bun's native implementations are put back immediately —
// leaving only the DOM behind, which is all this file came for.
const nativeHttp = {
  fetch: globalThis.fetch,
  Request: globalThis.Request,
  Response: globalThis.Response,
  Headers: globalThis.Headers,
};
GlobalRegistrator.register();
Object.assign(globalThis, nativeHttp);

// `bun test` has no Svelte loader of its own — Vite supplies one in `dev`
// and `build`, but the test runner never goes through Vite. Without this,
// an imported `.svelte` file resolves to its own path string instead of a
// component. `generate: "client"` is what makes each mount below a real
// client-side render rather than the SSR string path smoke.test.ts covers.
Bun.plugin({
  name: "svelte",
  setup(build) {
    build.onLoad({ filter: /\.svelte$/ }, async ({ path: file }) => {
      const source = await Bun.file(file).text();
      const { js } = compile(source, { filename: file, generate: "client", css: "injected" });
      return { contents: js.code, loader: "js" };
    });

    build.onLoad({ filter: /\.svelte\.(ts|js)$/ }, async ({ path: file }) => {
      const source = await Bun.file(file).text();
      const { js } = compileModule(source, { filename: file, generate: "client" });
      return { contents: js.code, loader: "js" };
    });
  },
});

const { mount, unmount, flushSync } = await import("svelte");

const COMPONENTS_ROOT = path.join(import.meta.dir, "..", "src", "lib", "components");

// The named membership of adr-22 rule 1's context-bound exemption: each of
// these reads a Svelte context its parent sets, so a bare mount throws BY
// DESIGN — the throw states the parent requirement. Their parent is covered
// like any other component. Entries are exact paths relative to
// COMPONENTS_ROOT — never a directory-wide wildcard, so a new component can
// never be silently skipped into the exemption.
const CONTEXT_BOUND: string[] = [
  "ui/alert-dialog/alert-dialog-action.svelte",
  "ui/alert-dialog/alert-dialog-cancel.svelte",
  "ui/alert-dialog/alert-dialog-content.svelte",
  "ui/alert-dialog/alert-dialog-trigger.svelte",
];

function discover(): string[] {
  const glob = new Glob("**/*.svelte");
  return [...glob.scanSync(COMPONENTS_ROOT)].map((p) => p.replaceAll(path.sep, "/")).sort();
}

const all = discover();
const subjects = all.filter((rel) => !CONTEXT_BOUND.includes(rel));

describe("adr-22 rule 1 — zero-prop mount", () => {
  test("the suite discovers real subjects (a broken glob must fail, not silently pass)", () => {
    expect(all.length).toBeGreaterThan(50);
    expect(subjects.length).toBeGreaterThan(0);
  });

  test("every CONTEXT_BOUND exemption names a component that actually exists", () => {
    for (const rel of CONTEXT_BOUND) {
      expect(all).toContain(rel);
    }
  });

  for (const rel of subjects) {
    test(`${rel} mounts with zero props and does not throw`, async () => {
      const mod = await import(path.join(COMPONENTS_ROOT, rel));
      const Component = mod.default;
      expect(Component).toBeDefined();

      const target = document.createElement("div");
      document.body.appendChild(target);

      const instance = mount(Component, { target });
      unmount(instance);
      target.remove();
    });
  }
});

// The automated backstop for adr-22 rule 2, the rule-1 harness's equivalent:
// a zero-prop mount performs no mutating action. This covers the
// mount-and-effect vector — a
// POST/PATCH/DELETE wired into onMount or an $effect, which fires the moment
// a component renders with no caller wiring. It is the vector a mount can
// actually observe: install a fetch stub that records any non-GET method,
// mount, flush pending effects, and assert nothing mutating went out.
//
// It deliberately does NOT dispatch clicks. The click-fired mutation path
// (a Save/logout that PATCHes or POSTs only from a handler, its action prop
// caller-wireable — ProfileForm, ThemeCard, SessionBadge) stays a code-review
// gate: catching it by test would require routing those actions through
// no-op-defaulting props, a component change outside this test's scope.
// COMPONENTIZATION.md states this split coverage and its limit plainly.
//
// The stub is installed and RESTORED per test, never at module scope: `bun
// test` runs every file in one process and smoke.test.ts drives the real
// fetch against a live SSR server, so a leaked stub would break it.
function methodOf(input: unknown, init?: RequestInit): string {
  if (init?.method) return init.method.toUpperCase();
  if (input instanceof Request) return input.method.toUpperCase();
  return "GET";
}

describe("adr-22 rule 2 — zero-prop mount issues no mutating request", () => {
  for (const rel of subjects) {
    test(`${rel} issues no mutating (non-GET) request on a zero-prop mount`, async () => {
      const mod = await import(path.join(COMPONENTS_ROOT, rel));
      const Component = mod.default;
      expect(Component).toBeDefined();

      const mutating: string[] = [];
      const target = document.createElement("div");
      document.body.appendChild(target);
      let instance: ReturnType<typeof mount> | undefined;

      try {
        globalThis.fetch = ((input: unknown, init?: RequestInit) => {
          const method = methodOf(input, init);
          if (method !== "GET" && method !== "HEAD") mutating.push(method);
          return Promise.resolve(new nativeHttp.Response(null, { status: 204 }));
        }) as typeof fetch;

        instance = mount(Component, { target });
        flushSync();

        expect(mutating).toEqual([]);
      } finally {
        if (instance) unmount(instance);
        target.remove();
        globalThis.fetch = nativeHttp.fetch;
      }
    });
  }
});

// Regression anchor for issue #373 (itself a regression of #189, surviving
// #277's structural fix and #275/#299's re-verifications): the SessionBadge
// hamburger menu's Melt Popover content rendered open/mispositioned on first
// load. Root cause: the popover-content <div> carried Tailwind's
// unconditional `flex` utility class alongside Melt's `popover="manual"`
// attribute. `.flex { display: flex }` is an ordinary author-stylesheet
// rule — same-or-higher cascade priority than the UA's built-in
// `[popover]:not(:popover-open) { display: none }` default — so `flex` won
// the cascade and permanently defeated the native hidden-by-default state,
// regardless of `popover`/`inert` being structurally correct. This is why
// #277's `popover="manual"` fix alone never held: it never touched the CSS
// that was overriding it.
//
// happy-dom does not implement the Popover API's UA default styling (that
// is a browser-engine behavior, not something exposed to a DOM emulator),
// so a getComputedStyle(...).display assertion here would not exercise the
// actual mechanism and could pass even with the regression reintroduced.
// The faithful, durable anchor is structural: the popover-content element's
// class list must NEVER carry a bare, unconditional `flex` (or any other
// `display` utility) token — every `display` utility on that element must
// be gated behind a `:popover-open`-scoped variant, so the UA default
// governs the closed state unopposed. A future edit that reintroduces a
// bare `flex` on this element fails this test immediately, without needing
// a real browser.
describe("issue #373 regression — SessionBadge popover never carries an unconditional display utility", () => {
  test("the authenticated popover-content div gates `flex` behind `:popover-open`, never bare", async () => {
    const mod = await import(path.join(COMPONENTS_ROOT, "auth/SessionBadge.svelte"));
    const Component = mod.default;

    const target = document.createElement("div");
    document.body.appendChild(target);

    const instance = mount(Component, {
      target,
      props: {
        me: {
          sub: "test-sub",
          email: "dev@example.com",
          given_name: "",
          family_name: "",
          picture: "",
          groups: [],
          nickname: "",
          avatar_visible: true,
        },
      },
    });
    flushSync();

    try {
      const popoverContent = target.querySelector("[data-melt-popover-content]");
      expect(popoverContent).not.toBeNull();

      const classList = popoverContent!.getAttribute("class") ?? "";
      const bareDisplayUtility = /(^|\s)(flex|grid|block|inline|inline-flex|inline-grid|inline-block)(\s|$)/;
      expect(classList).not.toMatch(bareDisplayUtility);

      // The popover attribute itself must stay "manual" (native hidden-by-
      // default) — a regression could also come from losing this attribute.
      expect(popoverContent!.getAttribute("popover")).toBe("manual");

      unmount(instance);
    } finally {
      target.remove();
    }
  });

  test("the logged-out popover-content div gates `flex` behind `:popover-open`, never bare", async () => {
    const mod = await import(path.join(COMPONENTS_ROOT, "auth/SessionBadge.svelte"));
    const Component = mod.default;

    const target = document.createElement("div");
    document.body.appendChild(target);

    const instance = mount(Component, { target, props: { me: null } });
    flushSync();

    try {
      const popoverContent = target.querySelector("[data-melt-popover-content]");
      expect(popoverContent).not.toBeNull();

      const classList = popoverContent!.getAttribute("class") ?? "";
      const bareDisplayUtility = /(^|\s)(flex|grid|block|inline|inline-flex|inline-grid|inline-block)(\s|$)/;
      expect(classList).not.toMatch(bareDisplayUtility);
      expect(popoverContent!.getAttribute("popover")).toBe("manual");

      unmount(instance);
    } finally {
      target.remove();
    }
  });
});
