<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Prev/next + numbered page controls for pairing with data/DataTable. Melt
  0.44 ships no Pagination builder ([[MELT-UI]] — same absence recorded for
  DropdownMenu's menu semantics), so the page window is hand-rolled here
  rather than delegated; page/onPageChange default to a safe single-page,
  no-op state so a zero-prop invocation renders without throwing and fires
  no mutating call (adr-22 r1/r2).
-->
<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";

  let {
    page = 1,
    pageCount = 1,
    onPageChange = () => {},
    class: className = undefined,
  }: {
    page?: number;
    pageCount?: number;
    onPageChange?: (page: number) => void;
    class?: string;
  } = $props();

  const pages = $derived(Array.from({ length: Math.max(1, pageCount) }, (_, i) => i + 1));

  function go(target: number): void {
    if (target < 1 || target > pageCount || target === page) return;
    onPageChange(target);
  }
</script>

<nav aria-label={t("demo_pagination_nav")} class={cn("flex items-center gap-1", className)}>
  <Button
    type="button"
    variant="outline"
    size="icon"
    disabled={page <= 1}
    onclick={() => go(page - 1)}
    aria-label={t("demo_pagination_prev")}
  >
    <span aria-hidden="true">‹</span>
  </Button>
  {#each pages as p (p)}
    <Button
      type="button"
      variant={p === page ? "default" : "ghost"}
      size="icon"
      aria-current={p === page ? "page" : undefined}
      onclick={() => go(p)}
    >
      {p}
    </Button>
  {/each}
  <Button
    type="button"
    variant="outline"
    size="icon"
    disabled={page >= pageCount}
    onclick={() => go(page + 1)}
    aria-label={t("demo_pagination_next")}
  >
    <span aria-hidden="true">›</span>
  </Button>
</nav>
