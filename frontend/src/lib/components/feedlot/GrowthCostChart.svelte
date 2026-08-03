<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-29-metrics-derivation]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Combined bars + line chart for the dashboard ([[FEEDLOT]]). Renders ONE real
  backend series — daily charge totals (`daily_cost`, [[adr-29-metrics-derivation]])
  — as bars, and their running cumulative as the line. It fabricates no data: with
  no points it shows an honest empty state, never invented values (adr-29 rule 2).
  Inline SVG, self-contained, theme-token colours ([[DESIGN-SYSTEM]]). Mounts with
  zero props and never throws ([[adr-22-showcase-ready-components]] rule 1).
-->
<script lang="ts">
  import { formatNumber } from "$lib/components/data/NumericValue.svelte";

  let {
    points = [],
    barLabel = "",
    lineLabel = "",
    emptyLabel = "",
    ariaLabel = "",
  }: {
    /** Ordered daily points: {label: date, value: charge total}. */
    points?: Array<{ label?: string; value?: string | number | null }>;
    barLabel?: string;
    lineLabel?: string;
    emptyLabel?: string;
    ariaLabel?: string;
  } = $props();

  function num(v: unknown): number {
    if (v === null || v === undefined || v === "") return 0;
    const n = Number(v);
    return Number.isNaN(n) ? 0 : n;
  }

  const W = 720;
  const H = 240;
  const PAD = { top: 16, right: 16, bottom: 28, left: 16 };
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;

  const daily = $derived(points.map((p) => ({ label: String(p.label ?? ""), v: num(p.value) })));

  // Running cumulative for the line.
  const cumulative = $derived.by(() => {
    let acc = 0;
    return daily.map((d) => (acc += d.v));
  });

  const barMax = $derived(Math.max(1, ...daily.map((d) => d.v)));
  const lineMax = $derived(Math.max(1, ...cumulative));

  const n = $derived(daily.length);
  const slot = $derived(n > 0 ? plotW / n : plotW);
  const barW = $derived(Math.max(2, Math.min(28, slot * 0.55)));

  const bars = $derived(
    daily.map((d, i) => {
      const h = (d.v / barMax) * plotH;
      return {
        x: PAD.left + slot * i + (slot - barW) / 2,
        y: PAD.top + (plotH - h),
        h,
        label: d.label,
        v: d.v,
      };
    }),
  );

  const linePath = $derived(
    cumulative
      .map((v, i) => {
        const x = PAD.left + slot * i + slot / 2;
        const y = PAD.top + (plotH - (v / lineMax) * plotH);
        return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" "),
  );

  const total = $derived(cumulative.length ? cumulative[cumulative.length - 1] : 0);
  const hasData = $derived(n > 0 && barMax > 0);
</script>

<div class="flex flex-col gap-3">
  {#if hasData}
    <svg
      viewBox={`0 0 ${W} ${H}`}
      class="h-56 w-full"
      preserveAspectRatio="none"
      role="img"
      aria-label={ariaLabel}
    >
      <!-- bars: daily total -->
      {#each bars as b}
        <rect x={b.x} y={b.y} width={barW} height={Math.max(0, b.h)} rx="2" fill="var(--chart-1)" opacity="0.85" />
      {/each}
      <!-- line: cumulative -->
      <path d={linePath} fill="none" stroke="var(--chart-2)" stroke-width="2.5"
        stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke" />
      {#each cumulative as v, i}
        <circle
          cx={PAD.left + slot * i + slot / 2}
          cy={PAD.top + (plotH - (v / lineMax) * plotH)}
          r="2.5" fill="var(--chart-2)"
        />
      {/each}
    </svg>

    <div class="flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-muted-foreground">
      <span class="inline-flex items-center gap-1.5">
        <span class="size-2.5 rounded-sm" style="background: var(--chart-1);"></span>{barLabel}
      </span>
      <span class="inline-flex items-center gap-1.5">
        <span class="size-2.5 rounded-full" style="background: var(--chart-2);"></span>{lineLabel}
      </span>
      <span class="ml-auto tabular-nums">{formatNumber(total, "ARS", "es", 0)}</span>
    </div>
  {:else}
    <div class="flex h-56 items-center justify-center rounded-lg border border-dashed border-border text-sm text-muted-foreground">
      {emptyLabel}
    </div>
  {/if}
</div>
