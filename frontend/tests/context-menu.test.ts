import { describe, expect, test } from "bun:test";
import path from "node:path";

const CONTEXT_MENU = path.join(
  import.meta.dir,
  "..",
  "src",
  "lib",
  "components",
  "nav",
  "ContextMenu.svelte",
);

async function read(): Promise<string> {
  return Bun.file(CONTEXT_MENU).text();
}

describe("ContextMenu — outside dismiss without Melt trigger", () => {
  test("does not spread popover.trigger (left-click toggle + Floating UI)", async () => {
    const source = await read();
    expect(source).not.toMatch(/\{\.\.\.popover\.trigger\}/);
  });

  test("closes on document pointerdown outside the content", async () => {
    const source = await read();
    expect(source).toContain('on(document, "pointerdown"');
    expect(source).toContain("popover.open = false");
    expect(source).toContain("contentEl.contains(target)");
  });
});
