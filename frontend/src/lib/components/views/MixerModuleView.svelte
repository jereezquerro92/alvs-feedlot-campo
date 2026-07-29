<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]] · [[adr-22-showcase-ready-components]] · [[adr-24-feedlot-domain]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[FEEDLOT]]
     LIVE-DOC:END -->

<!--
  The mixer module ([[adr-33-feedyard-operating-loop]]): create corrales (`Pen`) and
  raciones (`Ration`), then register the loading order (`LoadingOrder`) — the PLAN of
  what the mixer takes to a pen, and see the orders already loaded. This is genuinely
  module-first: pens, rations and orders are feedyard catalogs/events, NOT client-
  scoped, so no client needs picking to operate here. Nothing here charges — feedyard
  plans and monitors, the debit is the served `FeedingEvent`'s (decision 1). The
  previous gap (task #21: "no me deja cargar nada") was that with zero pens and zero
  rations the loading-order dropdowns were always empty and the form could never
  validate; this view surfaces the creation of both so the order form can be filled.
  Mounts with zero props and never throws ([[adr-22-showcase-ready-components]] rule 1).
  Green `.feedlot-app` tokens ([[DESIGN-SYSTEM]]); copy via i18n ([[LOCALIZATION]]).
-->
<script lang="ts">
  import FeedlotShell from "$lib/components/feedlot/FeedlotShell.svelte";
  import { PenForm, RationForm, LoadingOrderForm } from "$lib/components/feedlot";
  import { t } from "../../../i18n";

  type Client = { id: number | string; name?: string; kind?: string };
  type Row = Record<string, any>;

  let {
    clients = [],
    currentClient = null,
    pens = [],
    rations = [],
    feedTypes = [],
    loadingOrders = [],
    today = "",
    publicBackendUrl = "",
  }: {
    clients?: Client[];
    currentClient?: Client | null;
    pens?: Row[];
    rations?: Row[];
    feedTypes?: Row[];
    loadingOrders?: Row[];
    today?: string;
    publicBackendUrl?: string;
  } = $props();

  const penLabel = (id: number | string): string =>
    pens.find((p) => String(p.id) === String(id))?.code ??
    pens.find((p) => String(p.id) === String(id))?.name ??
    `#${id}`;
  const rationLabel = (id: number | string): string =>
    rations.find((r) => String(r.id) === String(id))?.name ?? `#${id}`;

  // Newest first; show a reasonable window.
  const recent = $derived(
    [...loadingOrders]
      .sort((a, b) => String(b.date ?? "").localeCompare(String(a.date ?? "")))
      .slice(0, 12),
  );

  function reload() {
    if (typeof window !== "undefined") window.location.reload();
  }
</script>

<FeedlotShell
  active="mixer"
  clients={clients}
  currentClient={currentClient}
  breadcrumb={t("feedlot_module_mixer_title")}
  switcherPattern={`/feedlot/mixer?client={id}`}
>
  <slot name="session" slot="session" />

  <div class="mx-auto flex w-full max-w-5xl flex-col gap-6">
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-bold tracking-tight">{t("feedlot_module_mixer_title")}</h1>
      <p class="text-sm text-muted-foreground">{t("feedlot_module_mixer_subtitle")}</p>
    </div>

    <div class="grid gap-5 lg:grid-cols-2">
      <!-- Create a pen -->
      <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
        <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_pen")}</h2>
        <PenForm publicBackendUrl={publicBackendUrl} onsaved={reload} />
      </div>

      <!-- Create a ration -->
      <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
        <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_ration")}</h2>
        <RationForm feedTypes={feedTypes} publicBackendUrl={publicBackendUrl} onsaved={reload} />
      </div>

      <!-- Register the loading order -->
      <div class="rounded-2xl p-5 lg:col-span-2" style="background: var(--card); border: var(--hairline) solid var(--border);">
        <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_order")}</h2>
        {#if pens.length === 0}
          <p class="mb-3 rounded-md p-3 text-sm text-muted-foreground" style="background: var(--muted);">{t("feedlot_module_no_pens")}</p>
        {/if}
        {#if rations.length === 0}
          <p class="mb-3 rounded-md p-3 text-sm text-muted-foreground" style="background: var(--muted);">{t("feedlot_module_no_rations")}</p>
        {/if}
        <LoadingOrderForm pens={pens} rations={rations} today={today} publicBackendUrl={publicBackendUrl} onsaved={reload} />
      </div>

      <!-- Recent loading orders -->
      <div class="rounded-2xl p-5 lg:col-span-2" style="background: var(--card); border: var(--hairline) solid var(--border);">
        <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_recent_orders")}</h2>
        {#if recent.length === 0}
          <p class="text-sm text-muted-foreground">{t("feedlot_module_recent_orders_empty")}</p>
        {:else}
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th class="pb-2 pr-4 font-semibold">{t("feedlot_module_order_col_date")}</th>
                  <th class="pb-2 pr-4 font-semibold">{t("feedlot_module_order_col_pen")}</th>
                  <th class="pb-2 pr-4 font-semibold">{t("feedlot_module_order_col_ration")}</th>
                  <th class="pb-2 font-semibold text-right">{t("feedlot_module_order_col_kg")}</th>
                </tr>
              </thead>
              <tbody>
                {#each recent as o (o.id)}
                  <tr style="border-top: var(--hairline) solid var(--border);">
                    <td class="py-2 pr-4">{o.date ?? "—"}</td>
                    <td class="py-2 pr-4">{penLabel(o.pen)}</td>
                    <td class="py-2 pr-4">{rationLabel(o.ration)}</td>
                    <td class="py-2 text-right tabular-nums">{o.planned_as_fed_kg ?? "—"}</td>
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
