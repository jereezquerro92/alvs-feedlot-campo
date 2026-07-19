/* LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-04-frontend-and-design-system]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

import type { Me } from "$lib/types/user";
import { hasRole } from "$lib/auth";

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
