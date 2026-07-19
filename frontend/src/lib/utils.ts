/* LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-04-frontend-and-design-system]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

export type ClassValue = string | false | null | undefined;


export function cn(...classes: ClassValue[]): string {
  return classes.filter(Boolean).join(" ");
}
