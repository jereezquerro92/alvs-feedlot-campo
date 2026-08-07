import { describe, expect, test } from "bun:test";
import { cn } from "../src/lib/utils";

// Regression cover for issue #294: cn() must resolve same-property Tailwind
// conflicts caller-wins, not just concatenate — the #285 workaround this
// unblocks is reverted in SessionBadge.svelte in the same change.

describe("cn", () => {
  test("caller-wins on a same-property conflict regardless of stylesheet order", () => {
    expect(cn("rounded-md", "rounded-full")).toBe("rounded-full");
  });

  test("the later argument wins on a same-property conflict", () => {
    expect(cn("p-2", "p-4")).toBe("p-4");
  });

  test("non-conflicting classes are all preserved", () => {
    const result = cn("bg-primary", "rounded-full");
    expect(result).toContain("bg-primary");
    expect(result).toContain("rounded-full");
  });

  test("falsy values are filtered, matching the pre-existing join behavior", () => {
    expect(cn("a", false, null, undefined, "b")).toBe("a b");
  });

  test("the button composition case from #294: caller rounded-full beats chrome's rounded-md", () => {
    const result = cn("inline-flex rounded-md text-sm", "rounded-full");
    expect(result).toContain("inline-flex");
    expect(result).toContain("text-sm");
    expect(result).toContain("rounded-full");
    expect(result).not.toContain("rounded-md");
  });
});
