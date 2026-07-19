<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of feedback/Toast — pushes a toast onto the shared
  `toaster` singleton on click. Mount feedback/Toast once elsewhere on the
  page (the region that actually renders the notification); this is only
  the trigger.
-->
<script lang="ts">
  import { toaster } from "$lib/components/feedback";
  import { Button } from "$lib/components/ui/button";

  let {
    triggerLabel,
    title,
    description,
  }: {
    triggerLabel: string;
    title: string;
    description: string;
  } = $props();
</script>

<Button
  type="button"
  variant="outline"
  onclick={() => toaster.addToast({ data: { title, description, variant: "success" } })}
>
  {triggerLabel}
</Button>
