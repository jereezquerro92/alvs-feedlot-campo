/* LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-54-site-menu-lock-modes]] · [[adr-52-frontend-and-design-system]]
 * Docs: [[DESIGN-SYSTEM]] · [[COMPONENTIZATION]]
 * LIVE-DOC:END */

/**
 * Site-menu FSM — preference, viewport band, presentation, and active item.
 * DOM-free resolvers so Base.astro SSR and bun:test share one contract with
 * the island. Lock preference is a cookie (SSR-readable, no-flash), not
 * localStorage ([[adr-54-site-menu-lock-modes]]).
 */

export type NavLockPreference = "locked" | "unlocked";

/** Viewport bands in rem ([[DESIGN-SYSTEM]] rail floor + Tailwind `lg`). */
export type NavViewport = "mobile" | "tablet" | "desk";

/** What the shell actually mounts / shows. */
export type NavPresentation = "rail" | "drawer";

export interface NavFsmState {
  preference: NavLockPreference;
  viewport: NavViewport;
  presentation: NavPresentation;
  active: string;
}

/** Cookie name — client-set chrome hint, same hygiene class as `theme`. */
export const NAV_LOCK_COOKIE = "nav_lock";

/** Locked rail minimum — tablet floor (~700px). Below → force drawer. */
export const RAIL_MIN_WIDTH = "43.75rem";

/** Desk floor — Tailwind `lg`. */
export const DESK_MIN_WIDTH = "64rem";

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

/**
 * Viewport from matchMedia results (root rem), not a hard-coded px/16 split.
 * `railFits` = min-width RAIL_MIN_WIDTH; `deskFits` = min-width DESK_MIN_WIDTH.
 */
export function resolveViewport(railFits: boolean, deskFits: boolean): NavViewport {
  if (!railFits) return "mobile";
  if (!deskFits) return "tablet";
  return "desk";
}

export function resolvePresentation(
  preference: NavLockPreference,
  viewport: NavViewport,
): NavPresentation {
  if (preference === "unlocked") return "drawer";
  if (viewport === "mobile") return "drawer";
  return "rail";
}

export function resolveNavFsm(input: {
  preference: NavLockPreference;
  viewport: NavViewport;
  active: string;
}): NavFsmState {
  const preference = input.preference;
  const viewport = input.viewport;
  return {
    preference,
    viewport,
    presentation: resolvePresentation(preference, viewport),
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
