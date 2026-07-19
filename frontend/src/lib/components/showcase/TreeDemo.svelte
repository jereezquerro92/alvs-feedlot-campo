<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of data/Tree — Tree needs no snippet, so this
  composition exists only for a visible client:load island in the gallery
  (same shape as showcase/PinInputDemo.svelte): its zero-prop default sample
  hierarchy already exercises the component fully.
-->
<script lang="ts">
  import { Tree } from "$lib/components/data";
</script>

<Tree />
