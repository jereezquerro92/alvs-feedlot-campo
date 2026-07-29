<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]] · [[adr-22-showcase-ready-components]] · [[adr-24-feedlot-domain]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[FEEDLOT]]
     LIVE-DOC:END -->

<!--
  The feed-stock module ([[FEEDLOT]], redesign). It DISPLAYS the balances the backend
  derives at `GET /api/feed-stock/` — Σ `in` − Σ `out` `FeedStockMovement` by
  `(owner_kind, feed_type)` ([[adr-25-account-ledger]] rule 4). Two audiences of stock:
  OWN stock is the feedlot's own feed, common to every client (cross-feedlot), so it
  shows with no client picked; the CLIENT column is that client's brought-in feed
  (`origin=client_stock` consumption draws it down, uncharged — rule 4) and appears only
  when a client is selected. Read-only: this view never writes; deliveries/feedings own
  the movements. A stock is a derived number, never an editable field ([[adr-24-feedlot-domain]]
  rule 3). Mounts with zero props and never throws ([[adr-22-showcase-ready-components]]
  rule 1). Green `.feedlot-app` tokens ([[DESIGN-SYSTEM]]); copy via i18n ([[LOCALIZATION]]).
-->
<script lang="ts">
  import FeedlotShell from "$lib/components/feedlot/FeedlotShell.svelte";
  import { t } from "../../../i18n";

  type Client = { id: number | string; name?: string; kind?: string };
  type StockRow = {
    feed_type: number | string;
    name?: string;
    unit?: string;
    own?: number | string;
    client?: number | string;
  };

  let {
    clients = [],
    currentClient = null,
    stockRows = [],
    publicBackendUrl = "",
  }: {
    clients?: Client[];
    currentClient?: Client | null;
    stockRows?: StockRow[];
    publicBackendUrl?: string;
  } = $props();

  // Rows carry a `client` key only when the backend was queried with `?client=`.
  const hasClient = $derived(currentClient !== null);

  // Format a derived balance honestly: a real 0 is shown as 0, never blanked.
  function fmt(v: number | string | undefined): string {
    if (v === undefined || v === null || v === "") return "—";
    const n = Number(v);
    if (Number.isNaN(n)) return String(v);
    return n.toLocaleString("es-AR", { maximumFractionDigits: 2 });
  }
</script>

<FeedlotShell
  active="stocks"
  clients={clients}
  currentClient={currentClient}
  breadcrumb={t("feedlot_module_stocks_title")}
  switcherPattern={`/feedlot/stocks?client={id}`}
>
  <slot name="session" slot="session" />

  <div class="mx-auto flex w-full max-w-5xl flex-col gap-6">
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-bold tracking-tight">{t("feedlot_module_stocks_title")}</h1>
      <p class="text-sm text-muted-foreground">{t("feedlot_module_stocks_subtitle")}</p>
    </div>

    <div class="grid gap-5">
      <!-- Own stock: cross-feedlot, always shown (no client needed) -->
      <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
        <h2 class="text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_stock_own")}</h2>
        <p class="mb-4 text-xs text-muted-foreground">{t("feedlot_module_group_stock_own_hint")}</p>
        {#if stockRows.length === 0}
          <p class="text-sm text-muted-foreground">{t("feedlot_stock_empty")}</p>
        {:else}
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th class="pb-2 pr-4 font-semibold">{t("feedlot_stock_col_feed")}</th>
                  <th class="pb-2 pr-4 font-semibold">{t("feedlot_stock_col_unit")}</th>
                  <th class="pb-2 font-semibold text-right">{t("feedlot_stock_col_balance")}</th>
                </tr>
              </thead>
              <tbody>
                {#each stockRows as row (row.feed_type)}
                  <tr style="border-top: var(--hairline) solid var(--border);">
                    <td class="py-2 pr-4">{row.name ?? `#${row.feed_type}`}</td>
                    <td class="py-2 pr-4 text-muted-foreground">{row.unit ?? "—"}</td>
                    <td class="py-2 text-right tabular-nums">{fmt(row.own)}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>

      <!-- Client's brought-in stock: only when a client is selected -->
      <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
        <h2 class="text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_stock_client")}</h2>
        <p class="mb-4 text-xs text-muted-foreground">{t("feedlot_module_group_stock_client_hint")}</p>
        {#if !hasClient}
          <p class="text-sm text-muted-foreground">{t("feedlot_module_stock_pick_client_hint")}</p>
        {:else if stockRows.length === 0}
          <p class="text-sm text-muted-foreground">{t("feedlot_stock_client_empty")}</p>
        {:else}
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th class="pb-2 pr-4 font-semibold">{t("feedlot_stock_col_feed")}</th>
                  <th class="pb-2 pr-4 font-semibold">{t("feedlot_stock_col_unit")}</th>
                  <th class="pb-2 font-semibold text-right">{t("feedlot_stock_col_balance")}</th>
                </tr>
              </thead>
              <tbody>
                {#each stockRows as row (row.feed_type)}
                  <tr style="border-top: var(--hairline) solid var(--border);">
                    <td class="py-2 pr-4">{row.name ?? `#${row.feed_type}`}</td>
                    <td class="py-2 pr-4 text-muted-foreground">{row.unit ?? "—"}</td>
                    <td class="py-2 text-right tabular-nums">{fmt(row.client)}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>
    </div>
  </div>
</FeedlotShell>
