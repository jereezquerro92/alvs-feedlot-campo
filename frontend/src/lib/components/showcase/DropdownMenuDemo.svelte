<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of nav/DropdownMenu — realistic row-action sample
  data (Edit/Duplicate/Archive-disabled/Delete). `lastAction` renders the
  selected item's own already-translated label back to the page, proving the
  demo action fired (scenario 4) without a network call or the toaster
  singleton — no new literal string is introduced here.
-->
<script lang="ts">
  import { DropdownMenu, type DropdownMenuItem } from "$lib/components/nav";

  let {
    items,
    triggerLabel,
  }: {
    items: DropdownMenuItem[];
    triggerLabel: string;
  } = $props();

  let lastAction = $state("");

  function handleSelect(value: string) {
    lastAction = items.find((item) => item.value === value)?.label ?? value;
  }
</script>

<div class="flex flex-col gap-2">
  <DropdownMenu {items} {triggerLabel} onSelect={handleSelect} />
  {#if lastAction}
    <p class="text-sm text-muted-foreground">{lastAction}</p>
  {/if}
</div>
