/* LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-04-frontend-and-design-system]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

export const defaultLocale = "es";

export const locales = [defaultLocale] as const;

export type Locale = (typeof locales)[number];
