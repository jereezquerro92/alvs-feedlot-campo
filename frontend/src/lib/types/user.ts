/* LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-04-frontend-and-design-system]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

import type { ThemeConfig } from "$lib/theme";

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
}
