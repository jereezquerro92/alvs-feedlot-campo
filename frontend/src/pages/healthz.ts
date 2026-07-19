/* LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-04-frontend-and-design-system]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

import type { APIRoute } from "astro";


export const GET: APIRoute = () =>
  new Response(JSON.stringify({ status: "ok" }), {
    status: 200,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
    },
  });
