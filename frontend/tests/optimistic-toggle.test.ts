import { describe, expect, test } from "bun:test";
import { optimisticToggle } from "../src/lib/optimistic-toggle";

// Unit coverage for ProfileForm's avatar-visibility toggle (bdd-05: "the
// toggle reverts to its prior state on avatar failure"). DOM-free, matching
// this template's bun:test conventions (no jsdom).

describe("optimisticToggle", () => {
  test("applies the flipped value immediately, then keeps it on success", async () => {
    let value = false;
    await optimisticToggle(
      value,
      (next) => {
        value = next;
      },
      async () => true,
    );
    expect(value).toBe(true);
  });

  test("reverts to the prior value when persist resolves false", async () => {
    let value = false;
    await optimisticToggle(
      value,
      (next) => {
        value = next;
      },
      async () => false,
    );
    expect(value).toBe(false);
  });

  test("reverts to the prior value when persist rejects", async () => {
    let value = true;
    await optimisticToggle(
      value,
      (next) => {
        value = next;
      },
      async () => {
        throw new Error("network error");
      },
    );
    expect(value).toBe(true);
  });
});
