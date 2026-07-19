<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Collapsible sections on the melt/builders Accordion ([[MELT-UI]]) — the
  builder owns roving focus, aria-expanded, and single/multiple selection;
  this component is the styled shell.
-->
<script lang="ts" module>
  export type AccordionItemData = {
    id: string;
    title: string;
    content?: string;
    disabled?: boolean;
  };
</script>

<script lang="ts">
  import { Accordion } from "melt/builders";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import type { Snippet } from "svelte";

  let {
    items,
    multiple = false,
    value = $bindable(undefined),
    content = undefined,
    class: className = undefined,
  }: {
    items: AccordionItemData[];
    multiple?: boolean;
    value?: string | string[] | undefined;
    /** Rich body per item; falls back to the item's `content` string. */
    content?: Snippet<[AccordionItemData]>;
    class?: string;
  } = $props();

  const accordion = new Accordion<boolean>({
    multiple: () => multiple,
    value: () => value,
    onValueChange: (v) => (value = v),
  });
</script>

<div {...accordion.root} class={cn("divide-y rounded-lg border bg-background", className)}>
  {#each items as data (data.id)}
    {@const item = accordion.getItem({ id: data.id, disabled: data.disabled })}
    <div class={cn("px-4 transition-colors", item.isExpanded && "bg-muted/50")}>
      <h3 {...item.heading} class="flex">
        <Button
          variant="bare"
          {...item.trigger}
          class="flex flex-1 items-center justify-between gap-4 py-4 text-left text-sm font-medium hover:text-primary"
        >
          {data.title}
          <span
            aria-hidden="true"
            class={cn("shrink-0 transition-transform duration-200", item.isExpanded && "rotate-180")}
          >⌄</span>
        </Button>
      </h3>
      {#if item.isExpanded}
        <div {...item.content} class="pb-4 text-sm text-muted-foreground">
          {#if content}
            {@render content(data)}
          {:else}
            {data.content ?? ""}
          {/if}
        </div>
      {/if}
    </div>
  {/each}
</div>
