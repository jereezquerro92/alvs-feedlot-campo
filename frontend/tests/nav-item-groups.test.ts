import { describe, expect, test } from "bun:test";
import { NAV_ITEM_GROUPS, canSeeNavItem } from "../src/lib/components/shell/nav";
import { GROUP } from "../src/lib/auth";

/**
 * Item trimming behaviour ([[adr-54-site-menu-lock-modes]] rule 9). Group names
 * are contract data — the values `/api/me/` returns in `groups` ([[API]]) — so
 * nothing here names or assumes anything about how the server decides
 * authorization ([[adr-53-api-membrane]] rule 2).
 *
 * Whether this table still agrees with the authority is checked from the server
 * side — the only side that may know both halves ([[adr-54-site-menu-lock-modes]]
 * rule 9).
 */

describe("canSeeNavItem", () => {
  test("no session supplied shows everything (zero-prop mount, gallery)", () => {
    for (const key of Object.keys(NAV_ITEM_GROUPS)) {
      expect(canSeeNavItem(key, null)).toBe(true);
    }
  });

  test("admins is the standing superset", () => {
    for (const key of Object.keys(NAV_ITEM_GROUPS)) {
      expect(canSeeNavItem(key, [GROUP.ADMINS])).toBe(true);
    }
  });

  test("a session with no groups sees only the ungated items", () => {
    expect(canSeeNavItem("dashboard", [])).toBe(true);
    expect(canSeeNavItem("users", [])).toBe(false);
    expect(canSeeNavItem("ledger", [])).toBe(false);
  });

  test("users & permissions is admins only", () => {
    expect(canSeeNavItem("users", ["field_managers"])).toBe(false);
    expect(canSeeNavItem("users", ["feedlot_owners"])).toBe(false);
    expect(canSeeNavItem("users", [GROUP.ADMINS])).toBe(true);
  });

  test("workshop sees gastos but not sanidad or cuenta", () => {
    expect(canSeeNavItem("gastos", ["workshop"])).toBe(true);
    expect(canSeeNavItem("sanitary", ["workshop"])).toBe(false);
    expect(canSeeNavItem("ledger", ["workshop"])).toBe(false);
  });

  test("feed_operators sees the mixer but not the ledger or the roster", () => {
    expect(canSeeNavItem("mixer", ["feed_operators"])).toBe(true);
    expect(canSeeNavItem("racion", ["feed_operators"])).toBe(true);
    expect(canSeeNavItem("ledger", ["feed_operators"])).toBe(false);
    expect(canSeeNavItem("clients", ["feed_operators"])).toBe(false);
  });

  test("a lot owner keeps the dashboard and loses the internal areas", () => {
    expect(canSeeNavItem("dashboard", ["lot_owners"])).toBe(true);
    expect(canSeeNavItem("clients", ["lot_owners"])).toBe(false);
    expect(canSeeNavItem("advisors", ["lot_owners"])).toBe(false);
    expect(canSeeNavItem("users", ["lot_owners"])).toBe(false);
  });

  test("more than one group unions their visibility", () => {
    expect(canSeeNavItem("gastos", ["workshop", "feed_operators"])).toBe(true);
    expect(canSeeNavItem("mixer", ["workshop", "feed_operators"])).toBe(true);
    expect(canSeeNavItem("users", ["workshop", "feed_operators"])).toBe(false);
  });

  test("an unclassified item key is never hidden", () => {
    // Trimming is convenience; an item nobody classified stays visible and the
    // server refuses it (adr-44 rule 8). Silent disappearance is the worse bug.
    expect(canSeeNavItem("not-a-real-item", ["workshop"])).toBe(true);
  });
});

describe("NAV_ITEM_GROUPS shape", () => {
  test("every entry is null or a non-empty list of group names", () => {
    for (const [key, groups] of Object.entries(NAV_ITEM_GROUPS)) {
      if (groups === null) continue;
      expect(groups.length, `${key} declares an empty group list`).toBeGreaterThan(0);
      for (const group of groups) {
        expect(group).toMatch(/^[a-z_]+$/);
      }
    }
  });
});
