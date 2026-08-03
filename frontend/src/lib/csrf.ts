/* LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-52-frontend-and-design-system]] · [[adr-10-auth]] · [[adr-05-htmx]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

export function readCsrfTokenFromCookie(): string {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}
