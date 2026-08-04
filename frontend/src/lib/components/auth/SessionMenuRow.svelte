<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Fixed session-menu row: glyph on the left, label on the right. Same chrome
  for theme toggle, profile link, and admin showcase link inside SessionBadge.
  Zero-prop safe (adr-22 r1) — renders a blank ghost row when label is empty.
-->
<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import NavGlyph from "$lib/components/shell/NavGlyph.svelte";
  import type { NavIconName } from "$lib/components/shell/nav";
  import { cn } from "$lib/utils";

  let {
    label = "",
    icon = "user" as NavIconName,
    href = undefined,
    type = "button",
    onclick = undefined,
    ariaLabel = undefined,
    class: className = undefined,
    ...rest
  }: {
    label?: string;
    icon?: NavIconName;
    href?: string;
    type?: "button" | "submit";
    onclick?: (event: MouseEvent) => void;
    ariaLabel?: string;
    class?: string;
    [key: string]: unknown;
  } = $props();
</script>

<Button
  {href}
  {type}
  {onclick}
  variant="ghost"
  size="sm"
  aria-label={ariaLabel ?? (label || undefined)}
  class={cn(
    "inline-flex h-9 w-full items-center justify-start gap-2.5 px-2 font-medium",
    className,
  )}
  {...rest}
>
  <span
    class="grid size-7 shrink-0 place-items-center rounded-md bg-muted text-muted-foreground"
    aria-hidden="true"
  >
    <NavGlyph name={icon} class="size-3.5" />
  </span>
  <span class="min-w-0 flex-1 truncate text-left">{label}</span>
</Button>
