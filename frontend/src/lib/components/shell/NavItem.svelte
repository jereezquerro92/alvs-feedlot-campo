<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[COMPONENTIZATION]]
     LIVE-DOC:END -->

<!--
  Enterprise nav capsule: the icon disc is the left circular cap (tallest
  element); active/hover fill projects to the right as a pill that ends with
  the same radius (`rounded-full`, height = disc). Compact so long labels
  ("Usuarios y permisos", "Precios de hacienda") still truncate cleanly.
-->
<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import NavBadge from "./NavBadge.svelte";
  import NavGlyph from "./NavGlyph.svelte";
  import type { NavIconName } from "./nav";

  let {
    href = "#",
    label = "",
    active = false,
    count = 0,
    icon = "grid" as NavIconName,
    /** `inverse` = light glyphs on a primary/sidebar fill (docked FancyNav). */
    tone = "default",
    class: className = undefined,
    ...rest
  }: {
    href?: string;
    label?: string;
    active?: boolean;
    count?: number;
    icon?: NavIconName;
    tone?: "default" | "inverse";
    class?: string;
    [key: string]: unknown;
  } = $props();

  const inverse = $derived(tone === "inverse");
</script>

<Button
  {href}
  variant="bare"
  class={cn(
    "group flex h-7 w-full items-center gap-1.5 rounded-full py-0 pl-0 pr-2.5 text-left text-xs font-medium leading-tight transition-colors",
    "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
    inverse
      ? active
        ? "bg-primary-foreground/20 text-primary-foreground"
        : "text-primary-foreground/90 hover:bg-primary-foreground/12"
      : active
        ? "bg-accent/45 text-foreground"
        : "text-foreground hover:bg-accent/30",
    className,
  )}
  aria-current={active ? "page" : undefined}
  {...rest}
>
  <span
    class={cn(
      "grid size-7 shrink-0 place-items-center rounded-full transition-colors",
      inverse
        ? active
          ? "bg-primary-foreground text-primary"
          : "bg-primary-foreground/15 text-primary-foreground group-hover:bg-primary-foreground/25"
        : active
          ? "bg-primary text-primary-foreground"
          : "bg-muted text-muted-foreground group-hover:bg-background group-hover:text-foreground",
    )}
    aria-hidden="true"
  >
    <NavGlyph name={icon} class="size-3.5" />
  </span>
  <span class="min-w-0 flex-1 truncate">{label}</span>
  <NavBadge {count} />
</Button>
