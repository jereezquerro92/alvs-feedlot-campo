/* LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-04-frontend-and-design-system]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

import { defaultLocale, locales } from "./config";
import type { Locale } from "./config";
import { messages } from "./messages";
import type { MessageKey } from "./messages";

export { defaultLocale, locales };
export type { Locale, MessageKey };

export function t(key: MessageKey, locale: Locale = defaultLocale): string {
  return messages[locale][key];
}
