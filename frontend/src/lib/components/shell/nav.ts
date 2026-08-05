/* LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-52-frontend-and-design-system]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

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
