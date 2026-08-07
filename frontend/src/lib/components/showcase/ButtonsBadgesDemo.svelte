<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Gallery tile for vendored ui/button + ui/badge + data/StatusBadge — keeps
  ShowcaseGalleryView free of authored button/badge markup (adr-52 r9).
-->
<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import { StatusBadge } from "$lib/components/data";
</script>

<div class="flex flex-wrap gap-3">
  <Button>Default</Button>
  <Button variant="secondary">Secondary</Button>
  <Button variant="destructive">Destructive</Button>
  <Button variant="outline">Outline</Button>
  <Button variant="ghost">Ghost</Button>
  <Button variant="link" href="/showcase/components/">Link</Button>
</div>
<div class="flex flex-wrap gap-3">
  <Badge>Default</Badge>
  <Badge variant="secondary">Secondary</Badge>
  <Badge variant="destructive">Destructive</Badge>
  <Badge variant="outline">Outline</Badge>
</div>
<div class="flex flex-wrap gap-3">
  <StatusBadge status="approved" />
  <StatusBadge status="pending" />
  <StatusBadge status="rejected" />
</div>
