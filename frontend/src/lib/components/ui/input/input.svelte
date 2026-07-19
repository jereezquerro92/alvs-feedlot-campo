<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts">
  import { cn } from "$lib/utils";
  let { class: className = undefined, value = $bindable(undefined), ...rest }: {
    class?: string; value?: string; [key: string]: unknown;
  } = $props();
</script>

<input
  bind:value
  class={cn(
    "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-base shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
    className,
  )}
  {...rest}
/>
