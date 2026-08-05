<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Big-control pick list: a titled card of large pressable rows with an optional
  trailing badge. Reusable default for "choose one and go" surfaces. Mounts with
  zero props and never throws ([[adr-22-showcase-ready-components]] rule 1); no
  write on mount (rule 2). Copy arrives from the caller ([[LOCALIZATION]]).
-->
<script lang="ts" module>
  import type { BadgeVariant } from "$lib/components/ui/badge/badge.svelte";

  export type ChoiceItem = {
    id: string | number;
    label: string;
    href?: string;
    badge?: string;
    badgeVariant?: BadgeVariant;
  };
</script>

<script lang="ts">
  import type { Snippet } from "svelte";
  import * as Card from "$lib/components/ui/card";
  import { Badge } from "$lib/components/ui/badge";
  import { SectionTitle } from "$lib/components/primitives/titles";
  import { cn } from "$lib/utils";

  let {
    title = "",
    subtitle = "",
    items = [],
    emptyLabel = "",
    class: className = undefined,
    footer,
  }: {
    title?: string;
    subtitle?: string;
    items?: ChoiceItem[];
    emptyLabel?: string;
    class?: string;
    footer?: Snippet;
  } = $props();
</script>

<Card.Root class={cn("gap-0 overflow-hidden py-0 shadow-sm", className)}>
  {#if title || subtitle}
    <Card.Header class="gap-1 border-b bg-muted/40 px-5 py-5 text-center">
      {#if title}
        <SectionTitle as="h1" class="mt-0 mb-0 text-2xl sm:text-3xl">{title}</SectionTitle>
      {/if}
      {#if subtitle}
        <p class="text-sm text-muted-foreground">{subtitle}</p>
      {/if}
    </Card.Header>
  {/if}

  {#if items.length === 0}
    <Card.Content class="px-5 py-8 text-center text-sm text-muted-foreground">
      {emptyLabel}
    </Card.Content>
  {:else}
    <ul class="flex flex-col">
      {#each items as item, i (item.id)}
        <li class={cn(i > 0 && "border-t border-border")}>
          <svelte:element
            this={item.href ? "a" : "div"}
            href={item.href}
            data-pressable={item.href ? "" : undefined}
            class={cn(
              "flex items-center justify-between gap-3 px-5 py-4 text-left transition-colors",
              item.href && "hover:bg-accent/60 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
            )}
          >
            <span class="min-w-0 text-base font-medium text-foreground">{item.label}</span>
            <span class="flex shrink-0 items-center gap-2">
              {#if item.badge}
                <Badge variant={item.badgeVariant ?? "success"}>{item.badge}</Badge>
              {/if}
              {#if item.href}
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  class="size-4 text-muted-foreground"
                  aria-hidden="true"
                >
                  <path d="m9 18 6-6-6-6" />
                </svg>
              {/if}
            </span>
          </svelte:element>
        </li>
      {/each}
    </ul>
  {/if}

  {#if footer}
    <Card.Footer class="border-t px-5 py-3">
      {@render footer()}
    </Card.Footer>
  {/if}
</Card.Root>
