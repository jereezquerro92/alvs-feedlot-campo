/* LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-52-frontend-and-design-system]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

import { GROUP } from "$lib/auth";

/** Closed icon names for shell/NavGlyph + NavItem. */

export type NavIconName =
  | "grid"
  | "users"
  | "cow"
  | "wheat"
  | "shield"
  | "scale"
  | "truck"
  | "blend"
  | "box"
  | "receipt"
  | "coins"
  | "spark"
  | "key"
  | "tag"
  | "chat"
  | "user"
  | "sun"
  | "moon"
  | "layers";

/**
 * Which role groups may SEE each menu item.
 *
 * The only thing named here is a group name — the same value `/api/me/` returns
 * in its `groups` field ([[API]]), so this table holds contract data and no
 * knowledge of how the server decides anything ([[adr-53-api-membrane]] rule 2).
 *
 * It is not a second RBAC matrix either ([[adr-44-field-operational-roles]] rule
 * 1 owns the one matrix). The binding is enforced from the server side, which is
 * the only side allowed to know both halves: a backend test reads this table and
 * fails if it disagrees with the authority. Drift cannot pass silently, and the
 * membrane is crossed in the one direction that is permitted.
 *
 * This is UI trimming only. The barrier is the server (adr-44 rule 8): hiding an
 * item removes a dead end, it does not protect the route.
 *
 * `null` = visible to every role.
 */
export const NAV_ITEM_GROUPS: Readonly<Record<string, readonly string[] | null>> = {
  // Per-client metrics — every role reaches its own scope, lot owners included.
  dashboard: null,
  intake: [GROUP.FIELD_MANAGERS, GROUP.FEED_OPERATORS, GROUP.FIELD_ADMINS, GROUP.FEEDLOT_OWNERS],
  pesajes: [GROUP.FIELD_MANAGERS, GROUP.FEED_OPERATORS, GROUP.FIELD_ADMINS, GROUP.FEEDLOT_OWNERS],
  feeding: [GROUP.FIELD_MANAGERS, GROUP.FEED_OPERATORS, GROUP.FIELD_ADMINS, GROUP.FEEDLOT_OWNERS],
  sanitary: [GROUP.FIELD_MANAGERS, GROUP.FEED_OPERATORS, GROUP.FEEDLOT_OWNERS],
  mixer: [GROUP.FIELD_MANAGERS, GROUP.FEED_OPERATORS, GROUP.FEEDLOT_OWNERS],
  racion: [GROUP.FIELD_MANAGERS, GROUP.FEED_OPERATORS, GROUP.FEEDLOT_OWNERS],
  stocks: [GROUP.FIELD_MANAGERS, GROUP.FIELD_ADMINS, GROUP.FEEDLOT_OWNERS],
  ledger: [GROUP.FIELD_MANAGERS, GROUP.FEEDLOT_OWNERS],
  gastos: [GROUP.FIELD_MANAGERS, GROUP.WORKSHOP, GROUP.FEEDLOT_OWNERS],
  clients: [GROUP.FIELD_MANAGERS, GROUP.FIELD_ADMINS, GROUP.FEEDLOT_OWNERS],
  advisors: [GROUP.FIELD_MANAGERS, GROUP.FEEDLOT_OWNERS],
  prices: [GROUP.FIELD_MANAGERS, GROUP.FEED_OPERATORS, GROUP.FIELD_ADMINS, GROUP.FEEDLOT_OWNERS],
  users: [GROUP.ADMINS],
};

/**
 * May this session see this item?
 *
 * `sessionGroups == null` means the caller supplied no session — show
 * everything, so a zero-prop mount and the component gallery render the whole
 * menu ([[adr-22-showcase-ready-components]] rules 1-3). `admins` is the
 * standing superset and always passes ([[adr-10-auth]]). An item absent from
 * the table stays visible: trimming is convenience, and a silent disappearance
 * is worse than a request the server refuses.
 */
export function canSeeNavItem(key: string, sessionGroups: readonly string[] | null): boolean {
  if (sessionGroups == null) return true;
  if (sessionGroups.includes(GROUP.ADMINS)) return true;
  const allowed = NAV_ITEM_GROUPS[key];
  if (allowed == null) return true;
  return allowed.some((group) => sessionGroups.includes(group));
}

/** Module slug → FancyNav `active` key (site menu highlight). */
const MODULE_ACTIVE: Record<string, string> = {
  hacienda: "intake",
  alimentacion: "feeding",
  sanidad: "sanitary",
  pesajes: "pesajes",
  mixer: "mixer",
  racion: "racion",
  stocks: "stocks",
  cuenta: "ledger",
  gastos: "gastos",
  asesor: "advisors",
  usuarios: "users",
  precios: "prices",
};

/** Per-client subpath → FancyNav `active` key. */
const CLIENT_SUB_ACTIVE: Record<string, string> = {
  ledger: "ledger",
  outstanding: "ledger",
  schedule: "sanitary",
  load: "intake",
};

/**
 * Resolve FancyNav highlight + client context from the request URL so
 * `Base.astro` can mount the site menu once without every page re-passing it.
 * `clientId` is data, not a gate: a null one scopes no link and never
 * suppresses the menu ([[adr-54-site-menu-lock-modes]] rule 3).
 */
export function resolveShellNav(
  pathname: string,
  searchParams?: URLSearchParams | null,
): { active: string; clientId: string | null } {
  const path = pathname.replace(/\/+$/, "") || "/";
  const qClient = searchParams?.get("client")?.trim() || null;

  if (path === "/feedlot") {
    return { active: "clients", clientId: qClient };
  }

  const clientMatch = path.match(/^\/feedlot\/(\d+)(?:\/([^/]+))?$/);
  if (clientMatch) {
    const clientId = clientMatch[1] ?? null;
    const sub = clientMatch[2];
    if (!sub) return { active: "dashboard", clientId };
    return { active: CLIENT_SUB_ACTIVE[sub] ?? "dashboard", clientId };
  }

  const moduleMatch = path.match(/^\/feedlot\/([^/]+)$/);
  if (moduleMatch) {
    const slug = moduleMatch[1] ?? "";
    return { active: MODULE_ACTIVE[slug] ?? "", clientId: qClient };
  }

  return { active: "", clientId: qClient };
}
