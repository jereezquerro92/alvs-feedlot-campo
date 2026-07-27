/* LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-04-frontend-and-design-system]] · [[adr-44-field-operational-roles]] · [[adr-20-authorization-lobby]] · [[adr-10-auth]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

import type { Me } from "$lib/types/user";
import { hasRole, isPortalSession } from "$lib/auth";

/** Query flag `/` reads to surface the role-less bounce reason ([[adr-20-authorization-lobby]]). */
export const DENIED_QUERY = "denied";

/** Where a role-less session is bounced — the lobby, carrying the denied flag. */
export const DENIED_REDIRECT = `/?${DENIED_QUERY}=1`;

/**
 * The shared role gate for every authenticated page ([[adr-20-authorization-lobby]]
 * rule 1). Returns the redirect path a role-less session must be bounced to, or
 * `null` when the session holds at least one Django Group. Pages call it as:
 *
 *   const redirect = requireRole(me);
 *   if (redirect) return Astro.redirect(redirect);
 *
 * so the bounce carries a reason `/` can render, instead of a silent redirect.
 */
export function requireRole(me: Me | null): string | null {
  return hasRole(me) ? null : DENIED_REDIRECT;
}

/**
 * The one feedlot route a client-portal (`lot_owners`) session may land on — its
 * own client dashboard (adr-44 decision 3) — or `DENIED_REDIRECT` when no client
 * is bound, failing closed to the lobby (adr-44 decision 4). Returns `null` for a
 * staff session, which is unscoped and reaches the roster normally.
 *
 * The backend (`ClientScopedReadPermission`) is the real boundary; this only
 * spares a portal user the roster fetch it would be 403'd on and lands it where
 * it belongs.
 */
export function portalLanding(me: Me | null): string | null {
  if (!isPortalSession(me)) return null;
  const clientId = me?.client?.id;
  return clientId == null ? DENIED_REDIRECT : `/feedlot/${clientId}`;
}

/**
 * Guard a client-scoped feedlot page: a portal session may view ONLY its own
 * client id. Returns a redirect path (its own dashboard, or `DENIED_REDIRECT`
 * when unbound) or `null` when the requested id is allowed. Staff → always `null`.
 * UX only — the backend already 403s a portal session on any other client's data.
 */
export function requireClientScope(me: Me | null, routeId: string | undefined): string | null {
  if (!isPortalSession(me)) return null;
  const clientId = me?.client?.id;
  if (clientId == null) return DENIED_REDIRECT;
  return String(clientId) === String(routeId) ? null : `/feedlot/${clientId}`;
}

/**
 * Guard an operational/write feedlot page (data entry, scheduling): a portal
 * session is read-only (adr-44) and never belongs there — it is sent to its own
 * dashboard, or the lobby when unbound. Returns `null` for a staff session.
 */
export function denyPortalSession(me: Me | null): string | null {
  return isPortalSession(me) ? portalLanding(me) : null;
}
