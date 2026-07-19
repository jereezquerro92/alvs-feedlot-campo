<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Single expand/collapse disclosure on the melt/builders Collapsible
  ([[MELT-UI]]) — the builder owns open state and aria-expanded/aria-controls
  wiring; this component is the styled shell. `data/` because it generalizes
  the single-row expand data/DataTable.svelte already does per-row: one
  reusable disclosure, not tied to a table row.
-->
<script lang="ts">
  import { Collapsible } from "melt/builders";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";
  import type { Snippet } from "svelte";

  let {
    triggerLabel = t("demo_collapsible_trigger"),
    content,
    open = $bindable(false),
    class: className = undefined,
  }: {
    triggerLabel?: string;
    content?: Snippet;
    open?: boolean;
    class?: string;
  } = $props();

  const collapsible = new Collapsible({
    open: () => open,
    onOpenChange: (v) => (open = v),
  });
</script>

<div class={cn("flex flex-col gap-2", className)}>
  <h3 class="flex">
    <Button
      type="button"
      variant="bare"
      {...collapsible.trigger}
      class="flex items-center gap-2 text-sm font-medium hover:text-primary"
    >
      <span
        aria-hidden="true"
        class={cn("shrink-0 transition-transform duration-200", collapsible.open && "rotate-180")}
      >⌄</span>
      {triggerLabel}
    </Button>
  </h3>
  {#if collapsible.open}
    <div {...collapsible.content} class="rounded-md border bg-background px-4 py-3 text-sm text-muted-foreground">
      {#if content}
        {@render content()}
      {:else}
        {t("demo_collapsible_empty")}
      {/if}
    </div>
  {/if}
</div>
