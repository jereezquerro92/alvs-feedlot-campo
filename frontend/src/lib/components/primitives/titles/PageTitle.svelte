<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  The document `<title>` element, authored as a component so no `.astro`
  route or layout carries inline markup ([[COMPONENTIZATION]]: Astro is
  routes + layouts only). Base.astro imports this with NO client directive:
  Astro renders it server-side to pure static HTML, shipping zero JS for a
  static string.
-->
<script lang="ts">
  let { title }: { title: string } = $props();
</script>

<title>{title}</title>
