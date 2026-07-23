<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  A minimal inline-SVG line chart. Colour rides `currentColor` (token-driven via
  the `text-primary` class — [[DESIGN-SYSTEM]] variable theming), never a hard hex.
  Mounts with zero props (renders the empty-state, no data) and never throws
  ([[adr-22-showcase-ready-components]] rule 1). It only PLOTS what the backend
  derived — it computes no metric ([[adr-29-metrics-derivation]] rule 1).
-->
<script lang="ts">
  let {
    points = [],
    height = 72,
    emptyLabel = "Sin datos para graficar",
    ariaLabel = "",
  }: {
    /** Ordered series; each `value` string|number, optional `label`. */
    points?: Array<{ value: number | string; label?: string }>;
    height?: number;
    emptyLabel?: string;
    ariaLabel?: string;
  } = $props();

  const W = 260;
  const PAD = 6;

  const clean = $derived(
    (points ?? [])
      .map((p) => ({ value: Number(p?.value), label: p?.label ?? "" }))
      .filter((p) => !Number.isNaN(p.value)),
  );

  const geom = $derived.by(() => {
    const n = clean.length;
    if (n === 0) return null;
    const values = clean.map((p) => p.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = max - min || 1;
    const usableW = W - PAD * 2;
    const usableH = height - PAD * 2;
    const dx = n > 1 ? usableW / (n - 1) : 0;
    const pts = clean.map((p, i) => ({
      x: PAD + dx * i,
      y: PAD + usableH * (1 - (p.value - min) / span),
    }));
    return { pts, min, max };
  });

  const line = $derived(geom ? geom.pts.map((p) => `${p.x},${p.y}`).join(" ") : "");
  const area = $derived(
    geom
      ? `${geom.pts[0].x},${height - PAD} ${line} ${geom.pts[geom.pts.length - 1].x},${height - PAD}`
      : "",
  );
  const last = $derived(geom ? geom.pts[geom.pts.length - 1] : null);
</script>

{#if geom}
  <svg
    viewBox={`0 0 ${W} ${height}`}
    class="w-full text-primary"
    role="img"
    aria-label={ariaLabel}
    preserveAspectRatio="none"
  >
    <polygon points={area} fill="currentColor" opacity="0.12" />
    <polyline
      points={line}
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linejoin="round"
      stroke-linecap="round"
      vector-effect="non-scaling-stroke"
    />
    {#if last}
      <circle cx={last.x} cy={last.y} r="3" fill="currentColor" />
    {/if}
  </svg>
{:else}
  <div
    class="flex items-center justify-center rounded-md border border-dashed border-border/50 text-xs text-muted-foreground"
    style={`height:${height}px`}
  >
    {emptyLabel}
  </div>
{/if}
