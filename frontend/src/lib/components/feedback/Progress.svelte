<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Progress bar on the melt/builders Progress ([[MELT-UI]]) — display-only, no
  trigger and no user interaction, so it carries no `onValueChange`: a
  zero-prop call falls back to the builder's own `value=0` default and
  renders an empty bar, never throwing ([[adr-22-showcase-ready-components]]).
-->
<script lang="ts">
  import { Progress as ProgressBuilder } from "melt/builders";
  import { cn } from "$lib/utils";

  let {
    value = undefined,
    max = 100,
    label = undefined,
    class: className = undefined,
  }: {
    value?: number;
    max?: number;
    label?: string;
    class?: string;
  } = $props();

  const progress = new ProgressBuilder({
    value: () => value,
    max: () => max,
  });
</script>

<div class={cn("flex flex-col gap-1", className)}>
  {#if label}<span class="text-sm text-muted-foreground">{label}</span>{/if}
  <div
    {...progress.root}
    class="relative h-2 w-full overflow-hidden rounded-full border border-border bg-muted"
  >
    <div
      {...progress.progress}
      class="h-full w-full flex-1 bg-primary transition-transform translate-x-[calc(var(--progress)*-1)]"
    ></div>
  </div>
</div>
