<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of nav/Menubar — a realistic File/Edit/View menu
  set. `lastAction` renders the selected menu and item labels back to the
  page, proving the demo action fired without a network call.
-->
<script lang="ts">
  import { Menubar, type MenubarMenu } from "$lib/components/nav";

  let {
    menus,
  }: {
    menus: MenubarMenu[];
  } = $props();

  let lastAction = $state("");

  function handleSelect(menuValue: string, itemValue: string) {
    const menu = menus.find((m) => m.value === menuValue);
    const item = menu?.items.find((i) => i.value === itemValue);
    lastAction = `${menu?.label ?? menuValue} → ${item?.label ?? itemValue}`;
  }
</script>

<div class="flex flex-col gap-2">
  <Menubar {menus} onSelect={handleSelect} />
  {#if lastAction}
    <p class="text-sm text-muted-foreground">{lastAction}</p>
  {/if}
</div>
