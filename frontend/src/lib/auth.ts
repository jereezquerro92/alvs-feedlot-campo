/* LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-52-frontend-and-design-system]] · [[adr-44-field-operational-roles]] · [[adr-20-authorization-lobby]] · [[adr-10-auth]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

import type { Me } from "./types/user";

export function hasRole(me: Me | null): me is Me {
  return me !== null && me.groups.length > 0;
}

/**
 * The six field role names (adr-44), as returned in the `groups` field of
 * `/api/me/` ([[API]]) — contract data, not a server internal
 * ([[adr-53-api-membrane]] rule 2). Held here for UI gating ONLY: these strings
 * drive navigation and portal routing and never an authorization decision. The
 * gate is convenience, never the barrier (adr-44 rule 8).
 */
export const GROUP = {
  ADMINS: "admins",
  FIELD_MANAGERS: "field_managers",
  FEED_OPERATORS: "feed_operators",
  LOT_OWNERS: "lot_owners",
  FIELD_ADMINS: "field_admins",
  FEEDLOT_OWNERS: "feedlot_owners",
  WORKSHOP: "workshop",
} as const;

/** Every internal/staff group — anyone NOT confined to a single-client portal. */
const STAFF_GROUPS: readonly string[] = [
  GROUP.ADMINS,
  GROUP.FIELD_MANAGERS,
  GROUP.FEED_OPERATORS,
  GROUP.FIELD_ADMINS,
  GROUP.FEEDLOT_OWNERS,
  GROUP.WORKSHOP,
];

/** True when the session belongs to at least one of `names`. */
export function inAnyGroup(me: Me | null, names: readonly string[]): boolean {
  return me !== null && me.groups.some((g) => names.includes(g));
}

/**
 * A client-portal session: in `lot_owners` and in NO staff group. Such a session
 * sees exactly one client and never the roster (adr-44 decision 3). A user who is
 * both a lot owner and staff is treated as staff — the wider view wins, matching
 * the backend, where any staff group already grants the cross-client read.
 */
export function isPortalSession(me: Me | null): boolean {
  return inAnyGroup(me, [GROUP.LOT_OWNERS]) && !inAnyGroup(me, STAFF_GROUPS);
}
