/* LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-04-frontend-and-design-system]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

import type { Locale } from "../config";
import { es } from "./es";

export const messages = { es } satisfies Record<Locale, Record<string, string>>;

export type MessageKey = keyof typeof es;
