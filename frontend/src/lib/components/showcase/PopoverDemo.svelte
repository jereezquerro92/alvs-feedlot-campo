<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of overlay/Popover — Popover's `content` prop is a
  Snippet, which Astro's slot mechanism cannot pass through, so the #snippet
  lives here (same reason showcase/TooltipDemo.svelte exists), supplying a
  realistic quote-box body instead of the component's empty-state fallback.
-->
<script lang="ts">
  import { Popover } from "$lib/components/overlay";

  let {
    triggerLabel,
    quote,
    author,
  }: {
    triggerLabel: string;
    quote: string;
    author: string;
  } = $props();
</script>

<Popover {triggerLabel}>
  {#snippet content()}
    <blockquote class="text-sm italic">&ldquo;{quote}&rdquo;</blockquote>
    <p class="mt-2 text-xs text-muted-foreground">— {author}</p>
  {/snippet}
</Popover>
