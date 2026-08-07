import { describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";

/**
 * Regression: ClientRouter view transitions paint named snapshots above the
 * live DOM. A prior fix put view-transition-name on the same node as the
 * drawer transform — capture failed and page-main still covered the menu.
 * Contract now: (1) no named page-main snapshot, (2) VT name on an
 * untransformed outer aside, (3) shell old/new images forced opaque.
 */
const APP_CSS = readFileSync(new URL("../src/styles/app.css", import.meta.url), "utf8");
const FANCY = readFileSync(
  new URL("../src/lib/components/overlay/FancyDrawer.svelte", import.meta.url),
  "utf8",
);
const DRAWER = readFileSync(
  new URL("../src/lib/components/overlay/Drawer.svelte", import.meta.url),
  "utf8",
);
const FANCY_NAV = readFileSync(
  new URL("../src/lib/components/feedlot/FeedlotFancyNav.svelte", import.meta.url),
  "utf8",
);
const CHAT_DRAWER = readFileSync(
  new URL("../src/lib/components/shell/ChatDrawer.svelte", import.meta.url),
  "utf8",
);
const BASE = readFileSync(new URL("../src/layouts/Base.astro", import.meta.url), "utf8");

describe("shell drawer view-transition stacking", () => {
  test("Base does not name page-main (no full-bleed covering snapshot)", () => {
    expect(BASE).toContain('data-page-main');
    expect(BASE).not.toContain('transition:name="page-main"');
    expect(BASE).not.toMatch(/PAGE_FADE/);
  });

  test("FancyDrawer and Drawer put VT name on an untransformed outer shell", () => {
    expect(FANCY).toContain("view-transition-name:");
    expect(FANCY).toContain("outerStyle");
    expect(FANCY).toMatch(/transform:\s*translateX/);
    // Outer style builder must not bake transform into the named node.
    const outerBlock = FANCY.slice(
      FANCY.indexOf("const outerStyle"),
      FANCY.indexOf("let rootEl"),
    );
    expect(outerBlock).not.toMatch(/transform/);

    expect(DRAWER).toContain("view-transition-name:");
    expect(DRAWER).toContain("outerStyle");
    const drawerOuter = DRAWER.slice(
      DRAWER.indexOf("const outerStyle"),
      DRAWER.indexOf("const isLeft"),
    );
    expect(drawerOuter).not.toMatch(/transform/);
  });

  test("site FancyNav and ChatDrawer pass unique shell VT names", () => {
    expect(FANCY_NAV).toContain('viewTransitionName="shell-nav"');
    expect(CHAT_DRAWER).toContain('viewTransitionName="shell-chat"');
  });

  test("app.css keeps shell VT images opaque and stacked", () => {
    expect(APP_CSS).toMatch(
      /::view-transition-group\(shell-nav\),\s*\n\s*::view-transition-group\(shell-chat\)\s*\{[^}]*z-index:\s*50/s,
    );
    expect(APP_CSS).toMatch(/::view-transition-old\(shell-nav\)/);
    expect(APP_CSS).toMatch(/opacity:\s*1\s*!important/);
    expect(APP_CSS).not.toMatch(/::view-transition-group\(page-main\)/);
  });

  test("Base keeps shell islands persisted without animate morph", () => {
    expect(BASE).toContain('transition:persist="shell-nav-island"');
    expect(BASE).toContain('transition:persist="shell-chat-island"');
  });
});
