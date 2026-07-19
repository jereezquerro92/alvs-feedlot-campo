/* LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-04-frontend-and-design-system]] · [[adr-10-auth]] · [[adr-05-htmx]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

export function readCsrfTokenFromCookie(): string {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}
