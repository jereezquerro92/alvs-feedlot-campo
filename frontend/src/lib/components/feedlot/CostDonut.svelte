<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-29-metrics-derivation]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Donut of the month's cost broken down by ledger concept ([[FEEDLOT]],
  [[adr-25-account-ledger]]). Displays exactly the real `cost_breakdown.by_concept`
  debits it is handed — non-zero slices only, real percentages, real centre total.
  No fabricated slices; with nothing to plot it shows an honest empty state
  (adr-29 rule 2). Inline SVG, token colours ([[DESIGN-SYSTEM]]). Mounts with zero
  props and never throws ([[adr-22-showcase-ready-components]] rule 1).

  Layout follows *container* width, not the viewport: the dashboard parks this
  card in a narrow `lg:grid-cols-3` third, so viewport `sm:` breakpoints wrongly
  force a side-by-side that truncates legend labels. Stack until the card itself
  is wide enough; labels wrap, never truncate.
-->
<script lang="ts">
  import { formatNumber } from "$lib/components/data/NumericValue.svelte";

  let {
    slices = [],
    centerLabel = "",
    emptyLabel = "",
    ariaLabel = "",
  }: {
    /** {label, value, color: a CSS colour or var()}. */
    slices?: Array<{ label?: string; value?: string | number | null; color?: string }>;
    centerLabel?: string;
    emptyLabel?: string;
    ariaLabel?: string;
  } = $props();

  function num(v: unknown): number {
    if (v === null || v === undefined || v === "") return 0;
    const n = Number(v);
    return Number.isNaN(n) || n < 0 ? 0 : n;
  }

  const parts = $derived(
    slices
      .map((s) => ({ label: String(s.label ?? ""), v: num(s.value), color: s.color ?? "var(--chart-6)" }))
      .filter((s) => s.v > 0),
  );
  const total = $derived(parts.reduce((a, s) => a + s.v, 0));

  // Donut geometry: one arc per slice via stroke-dasharray on a circle.
  const R = 60;
  const C = 2 * Math.PI * R;
  const arcs = $derived.by(() => {
    let offset = 0;
    return parts.map((s) => {
      const frac = total > 0 ? s.v / total : 0;
      const arc = { ...s, frac, dash: frac * C, offset: -offset * C };
      offset += frac;
      return arc;
    });
  });

  const hasData = $derived(total > 0);
</script>

<div class="@container w-full min-w-0">
  {#if hasData}
    <div
      class="flex flex-col items-center gap-4 @[24rem]:flex-row @[24rem]:items-center @[24rem]:gap-6"
    >
      <svg
        viewBox="0 0 160 160"
        class="size-36 shrink-0 -rotate-90 @[24rem]:size-40"
        role="img"
        aria-label={ariaLabel}
      >
        {#each arcs as a (a.label)}
          <circle
            cx="80"
            cy="80"
            r={R}
            fill="none"
            stroke={a.color}
            stroke-width="20"
            stroke-dasharray={`${a.dash} ${C - a.dash}`}
            stroke-dashoffset={a.offset}
          />
        {/each}
      </svg>
      <div class="flex w-full min-w-0 flex-1 flex-col gap-2">
        <div class="mb-1 text-center @[24rem]:text-left">
          <div class="text-xs uppercase tracking-wide text-muted-foreground">{centerLabel}</div>
          <div class="text-xl font-bold tabular-nums">{formatNumber(total, "ARS", "es", 0)}</div>
        </div>
        {#each arcs as a (a.label)}
          <div class="flex min-w-0 items-start gap-2 text-sm">
            <span class="mt-1 size-3 shrink-0 rounded-sm" style={`background: ${a.color};`}></span>
            <span class="min-w-0 flex-1 break-words leading-snug">{a.label}</span>
            <span class="shrink-0 tabular-nums text-muted-foreground">{Math.round(a.frac * 100)}%</span>
          </div>
        {/each}
      </div>
    </div>
  {:else}
    <div
      class="flex h-40 w-full items-center justify-center rounded-lg border border-dashed border-border text-sm text-muted-foreground"
    >
      {emptyLabel}
    </div>
  {/if}
</div>
