<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!-- Stroke glyphs for the enterprise NavDrawer. Presentation only — names are
     closed in nav.ts; copy stays in i18n. -->
<script lang="ts">
  import { cn } from "$lib/utils";
  import type { NavIconName } from "./nav";

  let {
    name = "grid",
    class: className = undefined,
  }: {
    name?: NavIconName;
    class?: string;
  } = $props();
</script>

<svg
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="1.75"
  stroke-linecap="round"
  stroke-linejoin="round"
  class={cn("size-4", className)}
  aria-hidden="true"
>
  {#if name === "grid"}
    <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
  {:else if name === "users"}
    <circle cx="9" cy="8" r="3" /><path d="M3 20c0-3 3-5 6-5s6 2 6 5" /><path d="M16 6a3 3 0 0 1 0 6M21 20c0-2-1-3.5-3-4.3" />
  {:else if name === "cow"}
    <path d="M5 8c-1.5 0-2-1.5-2-2.5S4 4 5 5" /><path d="M19 8c1.5 0 2-1.5 2-2.5S20 4 19 5" /><path d="M5 8v3a7 7 0 0 0 14 0V8" /><path d="M9 15h6" /><circle cx="9.5" cy="11" r=".6" fill="currentColor" /><circle cx="14.5" cy="11" r=".6" fill="currentColor" />
  {:else if name === "wheat"}
    <path d="M12 22V8" /><path d="M12 8c0-2 1.5-3 3-3 0 2-1.5 3-3 3Z" /><path d="M12 8c0-2-1.5-3-3-3 0 2 1.5 3 3 3Z" /><path d="M12 13c0-2 1.5-3 3-3 0 2-1.5 3-3 3Z" /><path d="M12 13c0-2-1.5-3-3-3 0 2 1.5 3 3 3Z" />
  {:else if name === "shield"}
    <path d="M12 3 5 6v5c0 4 3 7 7 8 4-1 7-4 7-8V6Z" /><path d="m9 12 2 2 4-4" />
  {:else if name === "scale"}
    <path d="M12 3v18" /><path d="M7 21h10" /><path d="M5 7h14" /><path d="M5 7 2 13a3 3 0 0 0 6 0Z" /><path d="M19 7l-3 6a3 3 0 0 0 6 0Z" />
  {:else if name === "truck"}
    <path d="M3 6h11v9H3Z" /><path d="M14 9h4l3 3v3h-7Z" /><circle cx="7" cy="17.5" r="1.6" /><circle cx="17" cy="17.5" r="1.6" />
  {:else if name === "blend"}
    <circle cx="9" cy="9" r="6" /><circle cx="15" cy="15" r="6" />
  {:else if name === "box"}
    <path d="M3 8 12 3l9 5v8l-9 5-9-5Z" /><path d="M3 8l9 5 9-5" /><path d="M12 13v8" />
  {:else if name === "receipt"}
    <path d="M5 3v18l2-1 2 1 2-1 2 1 2-1 2 1V3l-2 1-2-1-2 1-2-1-2 1Z" /><path d="M9 8h6M9 12h6" />
  {:else if name === "coins"}
    <ellipse cx="8" cy="6" rx="5" ry="2.5" /><path d="M3 6v5c0 1.4 2.2 2.5 5 2.5s5-1.1 5-2.5V6" /><path d="M11 15.5c0 1.4 2.2 2.5 5 2.5s5-1.1 5-2.5v-5c0-1.4-2.2-2.5-5-2.5" />
  {:else if name === "spark"}
    <path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2 2M16 16l2 2M18 6l-2 2M8 16l-2 2" /><circle cx="12" cy="12" r="2.4" />
  {:else if name === "key"}
    <circle cx="8" cy="15" r="3.5" /><path d="m10.5 12.5 8-8M15 5l2 2M18 8l2-2" />
  {:else if name === "tag"}
    <path d="M3 12V4h8l9 9-8 8Z" /><circle cx="7.5" cy="7.5" r="1.3" />
  {:else if name === "chat"}
    <path d="M4 5h16v11H8l-4 4Z" />
  {:else if name === "user"}
    <circle cx="12" cy="8" r="3.5" /><path d="M5 20c0-3.5 3-6 7-6s7 2.5 7 6" />
  {:else if name === "sun"}
    <circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
  {:else if name === "moon"}
    <path d="M21 14.5A8.5 8.5 0 0 1 9.5 3 7 7 0 1 0 21 14.5Z" />
  {:else if name === "layers"}
    <path d="m12 3 9 5-9 5-9-5Z" /><path d="m3 12 9 5 9-5" /><path d="m3 17 9 5 9-5" />
  {/if}
</svg>
