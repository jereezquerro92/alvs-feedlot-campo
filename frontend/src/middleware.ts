/* LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-10-auth]]
 * Docs: [[INFRASTRUCTURE]]
 * LIVE-DOC:END */

import { defineMiddleware } from "astro:middleware";

// Cache-Control backstop (docs/CACHE.md, adr-06 rule 3; issue #52 — the
// frontend-container counterpart of the backend's #42/#46). Pages set their
// own explicit header on the success path (index.astro, showcase.astro,
// healthz.ts), but framework-generated responses — most visibly the default
// 404 — never run any page's code, so a per-page pattern cannot cover them.
// This runs for every request and only fills in the default when a response
// ships with no header at all; it never overrides a page's own choice.
export const onRequest = defineMiddleware(async (_context, next) => {
  const response = await next();
  if (!response.headers.has("Cache-Control")) {
    response.headers.set("Cache-Control", "no-store");
  }
  return response;
});
