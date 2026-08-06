import { describe, expect, test } from "bun:test";
import {
  encodeNavLockCookie,
  parseNavLockCookie,
  resolveNavFsm,
  resolvePresentation,
  type NavLockPreference,
} from "../src/lib/components/shell/nav-fsm";

const PREFERENCES: NavLockPreference[] = ["locked", "unlocked"];

describe("parseNavLockCookie", () => {
  test("treats 1/locked/true as locked", () => {
    expect(parseNavLockCookie("1")).toBe("locked");
    expect(parseNavLockCookie("locked")).toBe("locked");
    expect(parseNavLockCookie("TRUE")).toBe("locked");
  });

  test("everything else is unlocked", () => {
    expect(parseNavLockCookie(undefined)).toBe("unlocked");
    expect(parseNavLockCookie(null)).toBe("unlocked");
    expect(parseNavLockCookie("0")).toBe("unlocked");
    expect(parseNavLockCookie("unlocked")).toBe("unlocked");
    expect(parseNavLockCookie("")).toBe("unlocked");
  });
});

describe("encodeNavLockCookie", () => {
  test("round-trips through parse", () => {
    expect(parseNavLockCookie(encodeNavLockCookie("locked"))).toBe("locked");
    expect(parseNavLockCookie(encodeNavLockCookie("unlocked"))).toBe("unlocked");
  });
});

describe("resolvePresentation", () => {
  test("locked is the rail, unlocked is the drawer", () => {
    expect(resolvePresentation("locked")).toBe("rail");
    expect(resolvePresentation("unlocked")).toBe("drawer");
  });

  // adr-54 rule 3: the menu is NEVER invisible. There is no third presentation
  // and no input that yields one, so no viewport measurement can hide the menu.
  test("every preference resolves to a real presentation", () => {
    for (const preference of PREFERENCES) {
      expect(["rail", "drawer"]).toContain(resolvePresentation(preference));
    }
  });
});

describe("resolveNavFsm", () => {
  test("packages preference, presentation, and active", () => {
    expect(resolveNavFsm({ preference: "locked", active: "feeding" })).toEqual({
      preference: "locked",
      presentation: "rail",
      active: "feeding",
    });
  });

  test("never yields a state without a menu", () => {
    for (const preference of PREFERENCES) {
      const fsm = resolveNavFsm({ preference, active: "" });
      expect(fsm.presentation).toBeTruthy();
      expect(["rail", "drawer"]).toContain(fsm.presentation);
    }
  });
});
