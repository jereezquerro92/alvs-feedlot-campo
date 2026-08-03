<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-29-metrics-derivation]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Horizontal per-lot bar comparison for the dashboard ([[FEEDLOT]]). Renders exactly
  the rows it is handed — one value (or honest null) per lot — as proportional bars.
  There is no per-lot feed-conversion metric in the backend yet (pen conversion is
  per-pen and service-only, adr-42), so the dashboard feeds this the honest per-lot
  figure it DOES have (average weight per head). No fabricated ranking; null means
  not calculable ("—", greyed row) and genuine zero stays a zero bar — never collapsed
  into the same dropped bucket (adr-29 rule 2). Token colours ([[DESIGN-SYSTEM]]).
  Mounts with zero props and never throws ([[adr-22-showcase-ready-components]] rule 1).
-->
<script lang="ts">
  import { formatNumber } from "$lib/components/data/NumericValue.svelte";

  let {
    rows = [],
    unit = "",
    emptyLabel = "",
    notCalculableLabel = "—",
    missingLabel = "sin datos",
  }: {
    /** {code: lot label, value: number | null}. null = not calculable (adr-29). */
    rows?: Array<{ code?: string; value?: string | number | null }>;
    unit?: string;
    emptyLabel?: string;
    /** Shown in place of the number when value is null. */
    notCalculableLabel?: string;
    /** Caption suffix when some rows are not calculable ("N sin datos"). */
    missingLabel?: string;
  } = $props();

  /** Parse a row value. null/undefined/""/NaN → null (not calculable); 0 stays 0. */
  function num(v: unknown): number | null {
    if (v === null || v === undefined || v === "") return null;
    const n = Number(v);
    return Number.isNaN(n) ? null : n;
  }

  const items = $derived(
    rows.map((r) => ({ code: String(r.code ?? ""), v: num(r.value) })),
  );
  const measured = $derived(items.filter((r): r is { code: string; v: number } => r.v !== null));
  const max = $derived(Math.max(1, ...measured.map((r) => r.v)));
  const missingCount = $derived(items.length - measured.length);
  const hasData = $derived(items.length > 0);
</script>

{#if hasData}
  <div class="flex flex-col gap-3">
    {#each items as r}
      <div class="flex items-center gap-3" class:opacity-60={r.v === null}>
        <span class="w-12 shrink-0 text-xs font-medium text-muted-foreground">{r.code}</span>
        <div class="h-3 flex-1 overflow-hidden rounded-full" style="background: var(--muted);">
          {#if r.v !== null}
            <div
              class="h-full rounded-full"
              style={`width: ${(r.v / max) * 100}%; background: var(--chart-1);`}
            ></div>
          {/if}
        </div>
        <span class="w-20 shrink-0 text-right text-xs tabular-nums text-muted-foreground">
          {#if r.v !== null}
            <span class="text-foreground">{formatNumber(r.v, undefined, "es", 0)}{unit ? ` ${unit}` : ""}</span>
          {:else}
            {notCalculableLabel}
          {/if}
        </span>
      </div>
    {/each}
    {#if missingCount > 0}
      <p class="text-xs text-muted-foreground">{missingCount} {missingLabel}</p>
    {/if}
  </div>
{:else}
  <div class="flex h-24 items-center justify-center rounded-lg border border-dashed border-border text-sm text-muted-foreground">
    {emptyLabel}
  </div>
{/if}
