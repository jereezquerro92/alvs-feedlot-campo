<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]] · [[adr-22-showcase-ready-components]] · [[adr-30-market-prices-connectors]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[FEEDLOT]]
     LIVE-DOC:END -->

<!--
  The reference-prices module ([[FEEDLOT]], redesign). It DISPLAYS the market prices
  the backend keeps at `GET /api/market-prices/` and their sources at
  `GET /api/market-sources/` ([[adr-30-market-prices-connectors]]). These are external
  reference values for metrics and the financial advisor — NEVER the currency of the
  ledger, which stays ARS with a historical snapshot per movement
  ([[adr-25-account-ledger]] rule 3). Two automatic sources (Cañuelas daily / IPCVA
  monthly) measure different things and are never averaged (adr-30 rule 8) — each price
  keeps its `source`. Read-only: this view never writes; the manual POST fallback and the
  ingest command own the rows. A price row is immutable, written once per
  (source, category, date) (adr-30 rule 6). Cross-client reference — no client switcher.
  Mounts with zero props and never throws ([[adr-22-showcase-ready-components]] rule 1).
  Green `.feedlot-app` tokens ([[DESIGN-SYSTEM]]); copy via i18n ([[LOCALIZATION]]).
-->
<script lang="ts">
  import FeedlotShell from "$lib/components/feedlot/FeedlotShell.svelte";
  import { t } from "../../../i18n";

  type Source = {
    id: number | string;
    name?: string;
    slug?: string;
    kind?: string;
    is_active?: boolean;
    is_automated?: boolean;
  };
  type Price = {
    id: number | string;
    source?: number | string;
    source_slug?: string;
    category?: string;
    date?: string;
    price_avg?: number | string | null;
    price_min?: number | string | null;
    price_max?: number | string | null;
    price_median?: number | string | null;
    head_count?: number | string | null;
  };

  let {
    sources = [],
    prices = [],
    publicBackendUrl = "",
  }: {
    sources?: Source[];
    prices?: Price[];
    publicBackendUrl?: string;
  } = $props();

  // A reference number is shown honestly: a real 0 is 0, a missing value is "—",
  // never a fabricated fill (adr-30 keeps min/max/median null when the source omits them).
  function fmt(v: number | string | null | undefined): string {
    if (v === undefined || v === null || v === "") return "—";
    const n = Number(v);
    if (Number.isNaN(n)) return String(v);
    return n.toLocaleString("es-AR", { maximumFractionDigits: 2 });
  }
</script>

<FeedlotShell
  active="prices"
  breadcrumb={t("feedlot_module_precios_title")}
  showSwitcher={false}
>
  <slot name="session" slot="session" />

  <div class="mx-auto flex w-full max-w-5xl flex-col gap-6">
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-bold tracking-tight">{t("feedlot_module_precios_title")}</h1>
      <p class="text-sm text-muted-foreground">{t("feedlot_module_precios_subtitle")}</p>
    </div>

    <p class="rounded-xl px-4 py-3 text-xs text-muted-foreground"
      style="background: var(--muted); border: var(--hairline) solid var(--border);">
      {t("feedlot_precios_reference_note")}
    </p>

    <!-- Sources -->
    <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
      <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_precios_sources_title")}</h2>
      {#if sources.length === 0}
        <p class="text-sm text-muted-foreground">{t("feedlot_precios_sources_empty")}</p>
      {:else}
        <div class="flex flex-wrap gap-2">
          {#each sources as source (source.id)}
            <span class="inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm"
              style="background: var(--muted); border: var(--hairline) solid var(--border);">
              <span class="font-medium">{source.name ?? source.slug ?? `#${source.id}`}</span>
              <span class="rounded-full px-2 py-0.5 text-[0.6rem] font-bold uppercase tracking-wide"
                style="background: var(--primary); color: var(--primary-foreground);">
                {source.is_automated ? t("feedlot_precios_source_automated") : t("feedlot_precios_source_manual")}
              </span>
              {#if source.is_active === false}
                <span class="text-[0.65rem] uppercase tracking-wide text-muted-foreground">{t("feedlot_precios_source_inactive")}</span>
              {/if}
            </span>
          {/each}
        </div>
      {/if}
    </div>

    <!-- Latest prices -->
    <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
      <div class="mb-1 flex items-baseline justify-between gap-3">
        <h2 class="text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_precios_prices_title")}</h2>
      </div>
      <p class="mb-4 text-xs text-muted-foreground">{t("feedlot_precios_unit_hint")}</p>
      {#if prices.length === 0}
        <p class="text-sm text-muted-foreground">{t("feedlot_precios_empty")}</p>
      {:else}
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-xs uppercase tracking-wide text-muted-foreground">
                <th class="pb-2 pr-4 font-semibold">{t("feedlot_precios_col_source")}</th>
                <th class="pb-2 pr-4 font-semibold">{t("feedlot_precios_col_category")}</th>
                <th class="pb-2 pr-4 font-semibold">{t("feedlot_precios_col_date")}</th>
                <th class="pb-2 pr-4 font-semibold text-right">{t("feedlot_precios_col_avg")}</th>
                <th class="pb-2 pr-4 font-semibold text-right">{t("feedlot_precios_col_min")}</th>
                <th class="pb-2 pr-4 font-semibold text-right">{t("feedlot_precios_col_max")}</th>
                <th class="pb-2 pr-4 font-semibold text-right">{t("feedlot_precios_col_median")}</th>
                <th class="pb-2 font-semibold text-right">{t("feedlot_precios_col_head")}</th>
              </tr>
            </thead>
            <tbody>
              {#each prices as row (row.id)}
                <tr style="border-top: var(--hairline) solid var(--border);">
                  <td class="py-2 pr-4 text-muted-foreground">{row.source_slug ?? `#${row.source}`}</td>
                  <td class="py-2 pr-4">{row.category ?? "—"}</td>
                  <td class="py-2 pr-4 tabular-nums text-muted-foreground">{row.date ?? "—"}</td>
                  <td class="py-2 pr-4 text-right font-medium tabular-nums">{fmt(row.price_avg)}</td>
                  <td class="py-2 pr-4 text-right tabular-nums">{fmt(row.price_min)}</td>
                  <td class="py-2 pr-4 text-right tabular-nums">{fmt(row.price_max)}</td>
                  <td class="py-2 pr-4 text-right tabular-nums">{fmt(row.price_median)}</td>
                  <td class="py-2 text-right tabular-nums text-muted-foreground">{fmt(row.head_count)}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </div>
  </div>
</FeedlotShell>
