<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts">
  import { cn } from "$lib/utils";

  let {
    as = "h2",
    class: className = undefined,
    children,
    ...rest
  }: {
    /** Heading level to render; keeps the visual scale, varies the semantics. */
    as?: "h1" | "h2" | "h3";
    class?: string;
    children?: import("svelte").Snippet;
    [key: string]: unknown;
  } = $props();

  // Strong reading rhythm: h2/h3 carry generous space above (and a little
  // below) so sections separate clearly (dark-mode readability iteration).
  // h1 is a page title and stays flush; callers can still override via class.
  const sizeFor: Record<string, string> = {
    h1: "text-3xl font-bold tracking-tight text-primary leading-tight",
    h2: "text-xl font-semibold mt-10 mb-2",
    h3: "text-lg font-medium mt-6 mb-1",
  };
</script>

<svelte:element this={as} class={cn(sizeFor[as], className)} {...rest}>
  {@render children?.()}
</svelte:element>
