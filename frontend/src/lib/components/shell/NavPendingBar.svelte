<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Visible during ClientRouter preparation (SSR fetch) — dim + top bar while
  HTML arrives. Driven by html[data-nav-pending] in app.css. Zero-prop,
  zero-hydration; Base.astro mounts it once.
-->
<div class="nav-pending-bar" aria-hidden="true"></div>
