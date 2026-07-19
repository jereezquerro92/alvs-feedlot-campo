/* LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-04-frontend-and-design-system]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

import type { Me } from "$lib/types/user";

export type NameSource = Partial<Pick<Me, "nickname" | "given_name" | "family_name" | "email">> | null | undefined;

/** A nickname the user typed for themselves outranks every derived form, so
 * it is consulted first wherever a name is shown. The email local part is the
 * last resort before an empty string: the full address is an identity anchor
 * (the popover shows it verbatim), not a display name. */
export function resolveDisplayName(me: NameSource): string {
  return (
    me?.nickname?.trim() ||
    `${me?.given_name ?? ""} ${me?.family_name ?? ""}`.trim() ||
    me?.email?.split("@")[0] ||
    ""
  );
}

export function resolveInitials(me: NameSource): string {
  const nickname = me?.nickname?.trim();
  if (nickname) return nickname.slice(0, 2).toUpperCase();

  const fromNames = `${me?.given_name?.[0] ?? ""}${me?.family_name?.[0] ?? ""}`.trim();
  if (fromNames) return fromNames.toUpperCase();

  return me?.email?.[0]?.toUpperCase() || "?";
}
