<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Plain anchor-link nav to in-page headings — Melt 0.44 ships no Table of
  Contents builder and none is needed: this is a hand-rolled fallback exactly
  like nav/Pagination or overlay/ScrollArea ([[MELT-UI]], adr-04 r8 last
  resort). It is deliberately NOT a menu: no roving tabindex, no arrow-key
  cycling, no typeahead — every link stays natively tab-focusable in document
  order, the correct behavior for a page-scroll nav. The one piece of runtime
  behavior is active-section highlighting via `IntersectionObserver` against
  the headings the `items` prop names, torn down on unmount.
-->
<script lang="ts" module>
  export type TableOfContentsItem = {
    href: string;
    label: string;
    depth?: 2 | 3;
  };
</script>

<script lang="ts">
  import { onMount } from "svelte";
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";

  // adr-22 r1: a zero-prop invocation renders three sample section links
  // rather than throwing.
  let {
    items = [
      { href: "#overview", label: t("demo_toc_overview") },
      { href: "#details", label: t("demo_toc_details"), depth: 3 },
      { href: "#summary", label: t("demo_toc_summary") },
    ],
    label = t("demo_toc_label"),
    class: className = undefined,
  }: {
    items?: TableOfContentsItem[];
    label?: string;
    class?: string;
  } = $props();

  let activeHref = $state<string | null>(null);

  onMount(() => {
    // Sample/demo headings and headings absent from the current page both
    // resolve to zero targets — the observer simply has nothing to watch,
    // never a throw.
    const targets = items
      .map((item) => document.querySelector(item.href))
      .filter((el): el is Element => el !== null);
    if (targets.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.find((entry) => entry.isIntersecting);
        if (visible) activeHref = `#${visible.target.id}`;
      },
      { rootMargin: "-10% 0px -80% 0px" },
    );
    targets.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  });
</script>

<nav aria-label={label} class={cn("flex flex-col gap-1 text-sm", className)}>
  {#each items as item (item.href)}
    <a
      href={item.href}
      aria-current={activeHref === item.href ? "location" : undefined}
      class={cn(
        "rounded-sm px-2 py-1 text-muted-foreground outline-none transition-colors",
        "hover:text-foreground focus-visible:ring-1 focus-visible:ring-ring",
        item.depth === 3 && "pl-5",
        activeHref === item.href && "font-medium text-foreground",
      )}
    >
      {item.label}
    </a>
  {/each}
</nav>
