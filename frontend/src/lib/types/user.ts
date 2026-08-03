/* LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-52-frontend-and-design-system]] · [[adr-44-field-operational-roles]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

import type { ThemeConfig } from "$lib/theme";

/**
 * The single client a lot-owner portal session is bound to (adr-44 decision 4).
 * `null` for every staff/unbound session. The frontend scopes its UI off this;
 * the backend stays the security boundary.
 */
export interface ClientRef {
  id: number;
  name: string;
  kind: string;
}

export interface Me {
  sub: string;
  email: string;
  given_name: string;
  family_name: string;
  picture: string;
  groups: string[];
  nickname: string;
  avatar_visible: boolean;
  theme_config?: ThemeConfig;
  client: ClientRef | null;
}
