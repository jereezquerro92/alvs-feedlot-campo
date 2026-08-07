import { describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";

/**
 * Regression: ClientRouter view transitions paint named snapshots in a layer
 * above the live DOM. Fixed FancyDrawer/Drawer chrome that only relies on
 * document z-40 gets covered by `page-main` during navigation unless the
 * fixed <aside> itself carries a view-transition-name stacked above it.
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
  test("FancyDrawer and Drawer accept an optional viewTransitionName prop", () => {
    expect(FANCY).toContain("viewTransitionName");
    expect(FANCY).toContain("view-transition-name:");
    expect(DRAWER).toContain("viewTransitionName");
    expect(DRAWER).toContain("view-transition-name:");
  });

  test("site FancyNav and ChatDrawer pass unique shell VT names on the fixed roots", () => {
    expect(FANCY_NAV).toContain('viewTransitionName="shell-nav"');
    expect(CHAT_DRAWER).toContain('viewTransitionName="shell-chat"');
  });

  test("app.css stacks shell VT groups above page-main", () => {
    expect(APP_CSS).toMatch(/::view-transition-group\(page-main\)\s*\{[^}]*z-index:\s*1/s);
    expect(APP_CSS).toMatch(
      /::view-transition-group\(shell-nav\),\s*\n\s*::view-transition-group\(shell-chat\)\s*\{[^}]*z-index:\s*40/s,
    );
  });

  test("Base keeps shell islands out of the page-main fade", () => {
    expect(BASE).toContain('transition:persist="shell-nav-island"');
    expect(BASE).toContain('transition:persist="shell-chat-island"');
    expect(BASE).toContain('transition:name="page-main"');
  });
});
