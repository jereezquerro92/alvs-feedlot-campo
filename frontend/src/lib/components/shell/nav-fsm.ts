/* LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-52-frontend-and-design-system]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

/**
 * Site-menu FSM — preference, presentation, and active item. Two presentations
 * and no third state: there is always a menu ([[adr-54-site-menu-lock-modes]]
 * rule 3). DOM-free resolvers so Base.astro SSR and bun:test share one
 * contract with the island. Lock preference is a cookie (SSR-readable,
 * no-flash), not localStorage.
 *
 * The viewport band is NOT an FSM field: locked mode mounts rail and drawer
 * together and CSS at RAIL_MIN_WIDTH picks the visible one, so no measurement
 * is needed to decide what renders (rule 8).
 */

export type NavLockPreference = "locked" | "unlocked";

/** What the shell actually mounts / shows. Never absent — those are the two. */
export type NavPresentation = "rail" | "drawer";

export interface NavFsmState {
  preference: NavLockPreference;
  presentation: NavPresentation;
  active: string;
}

/** Cookie name — client-set chrome hint, same hygiene class as `theme`. */
export const NAV_LOCK_COOKIE = "nav_lock";

/** Locked rail minimum — tablet floor (~700px). Below it, CSS shows the drawer. */
export const RAIL_MIN_WIDTH = "43.75rem";

/** Legacy localStorage key — read once to migrate into the cookie. */
export const NAV_LOCK_LEGACY_KEY = "feedlot-nav-pinned";

export function parseNavLockCookie(raw: string | undefined | null): NavLockPreference {
  if (raw == null) return "unlocked";
  const v = raw.trim().toLowerCase();
  if (v === "1" || v === "locked" || v === "true") return "locked";
  return "unlocked";
}

export function encodeNavLockCookie(preference: NavLockPreference): string {
  return preference === "locked" ? "1" : "0";
}

/** Locked wants the rail, unlocked wants the drawer. There is no third answer. */
export function resolvePresentation(preference: NavLockPreference): NavPresentation {
  return preference === "locked" ? "rail" : "drawer";
}

export function resolveNavFsm(input: {
  preference: NavLockPreference;
  active: string;
}): NavFsmState {
  return {
    preference: input.preference,
    presentation: resolvePresentation(input.preference),
    active: input.active,
  };
}

/** Client-only: read preference from `document.cookie`. */
export function readNavLockCookie(): NavLockPreference {
  if (typeof document === "undefined") return "unlocked";
  const match = document.cookie.match(/(?:^|;\s*)nav_lock=([^;]+)/);
  return match ? parseNavLockCookie(decodeURIComponent(match[1] ?? "")) : "unlocked";
}

/** Client-only: persist preference for SSR on the next navigation. */
export function writeNavLockCookie(preference: NavLockPreference): void {
  if (typeof document === "undefined") return;
  const value = encodeURIComponent(encodeNavLockCookie(preference));
  document.cookie = `${NAV_LOCK_COOKIE}=${value}; Path=/; Max-Age=31536000; SameSite=Lax`;
}

/**
 * One-shot migration: if the cookie is absent but legacy localStorage says
 * pinned, write the cookie and return locked.
 */
export function migrateLegacyNavLock(): NavLockPreference | null {
  if (typeof document === "undefined" || typeof localStorage === "undefined") return null;
  const existing = document.cookie.match(/(?:^|;\s*)nav_lock=/);
  if (existing) return null;
  try {
    if (localStorage.getItem(NAV_LOCK_LEGACY_KEY) === "1") {
      writeNavLockCookie("locked");
      return "locked";
    }
  } catch {
    /* private mode / denied */
  }
  return null;
}
