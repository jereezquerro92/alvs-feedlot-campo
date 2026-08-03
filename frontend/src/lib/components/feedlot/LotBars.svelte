<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-29-metrics-derivation]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Horizontal per-lot bar comparison for the dashboard ([[FEEDLOT]]). Renders exactly
  the rows it is handed — one real value per lot — as proportional bars. There is no
  per-lot feed-conversion metric in the backend yet (pen conversion is per-pen and
  service-only, adr-42), so the dashboard feeds this the honest per-lot figure it DOES
  have (average weight per head). No fabricated ranking; empty rows show an honest
  empty state (adr-29 rule 2). Token colours ([[DESIGN-SYSTEM]]). Mounts with zero props
  and never throws ([[adr-22-showcase-ready-components]] rule 1).
-->
<script lang="ts">
  import { formatNumber } from "$lib/components/data/NumericValue.svelte";

  let {
    rows = [],
    unit = "",
    emptyLabel = "",
  }: {
    /** {code: lot label, value: number}. */
    rows?: Array<{ code?: string; value?: string | number | null }>;
    unit?: string;
    emptyLabel?: string;
  } = $props();

  function num(v: unknown): number {
    if (v === null || v === undefined || v === "") return 0;
    const n = Number(v);
    return Number.isNaN(n) ? 0 : n;
  }

  const items = $derived(
    rows.map((r) => ({ code: String(r.code ?? ""), v: num(r.value) })).filter((r) => r.v > 0),
  );
  const max = $derived(Math.max(1, ...items.map((r) => r.v)));
  const hasData = $derived(items.length > 0);
</script>

{#if hasData}
  <div class="flex flex-col gap-3">
    {#each items as r}
      <div class="flex items-center gap-3">
        <span class="w-12 shrink-0 text-xs font-medium text-muted-foreground">{r.code}</span>
        <div class="h-3 flex-1 overflow-hidden rounded-full" style="background: var(--muted);">
          <div class="h-full rounded-full" style={`width: ${(r.v / max) * 100}%; background: var(--chart-1);`}></div>
        </div>
        <span class="w-20 shrink-0 text-right text-xs tabular-nums">{formatNumber(r.v, undefined, "es", 0)}{unit ? ` ${unit}` : ""}</span>
      </div>
    {/each}
  </div>
{:else}
  <div class="flex h-24 items-center justify-center rounded-lg border border-dashed border-border text-sm text-muted-foreground">
    {emptyLabel}
  </div>
{/if}
