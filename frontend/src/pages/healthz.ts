/* LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-52-frontend-and-design-system]] · [[adr-09-docker-compose]]
 * Docs: [[FRONTEND]] · [[DOCKER]]
 * LIVE-DOC:END */

import type { APIRoute } from "astro";

// Liveness probe — issue #46. Unconditional 200 is the contract: this route
// proves Astro SSR is up and routing, nothing more. It MUST NOT check
// BACKEND_API_URL or any downstream dependency — doing so converts a liveness
// probe into an aggregate-health check and breaks the ALB TG contract.
// Semantics: [[FRONTEND]] § Health probe. Wiring (Compose, ALB TG, smoke
// suite): [[DOCKER]]. Required by [[adr-09-docker-compose]] rule 8.
export const GET: APIRoute = () =>
  new Response(JSON.stringify({ status: "ok" }), {
    status: 200,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
    },
  });
