<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of nav/ContextMenu — a labeled right-click region
  wrapping realistic row-action sample data. `lastAction` renders the
  selected item's own already-translated label back to the page, proving the
  demo action fired without a network call or the toaster singleton.
-->
<script lang="ts">
  import { ContextMenu, type ContextMenuItem } from "$lib/components/nav";
  import { t } from "../../../i18n";

  let {
    items,
    regionLabel,
  }: {
    items: ContextMenuItem[];
    regionLabel: string;
  } = $props();

  let lastAction = $state("");

  function handleSelect(value: string) {
    lastAction = items.find((item) => item.value === value)?.label ?? value;
  }
</script>

<div class="flex flex-col gap-2">
  <ContextMenu {items} onSelect={handleSelect}>
    <div class="flex h-24 w-full items-center justify-center rounded-md border border-dashed text-sm text-muted-foreground">
      {regionLabel}
    </div>
  </ContextMenu>
  {#if lastAction}
    <p class="text-sm text-muted-foreground">{lastAction}</p>
  {:else}
    <p class="text-sm text-muted-foreground">{t("demo_context_menu_hint")}</p>
  {/if}
</div>
