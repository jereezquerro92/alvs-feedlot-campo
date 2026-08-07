/* LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-52-frontend-and-design-system]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

import { twMerge } from "tailwind-merge";

export type ClassValue = string | false | null | undefined;

export function cn(...classes: ClassValue[]): string {
  return twMerge(classes.filter(Boolean).join(" "));
}
