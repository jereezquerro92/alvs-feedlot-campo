<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]] · [[adr-22-showcase-ready-components]] · [[adr-49-domain-layer-and-growth-by-addition]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[FEEDLOT]]
     LIVE-DOC:END -->

<!--
  The "servir ración" module (tasks #21/#22): the easy multi-target feeding surface.
  It's module-first — the operator enters here and picks one OR more clients and
  their destination lots INSIDE the form, adds one OR more feeds each with its own
  ORIGEN, and optionally a day range. It writes `FeedingEvent`s through the `feed`
  app ([[adr-25-account-ledger]] rule 4: own_stock charges, client_stock does not).
  This is executed feeding, not a plan — no `LoadingOrder`, no direct ledger write
  ([[adr-33-feedyard-operating-loop]] decision 1/2). Mounts with zero props and never
  throws ([[adr-22-showcase-ready-components]] rule 1). Green tokens ([[DESIGN-SYSTEM]]);
  copy via i18n ([[LOCALIZATION]]).
-->
<script lang="ts">
  import FeedlotShell from "$lib/components/feedlot/FeedlotShell.svelte";
  import { RationServeForm } from "$lib/components/feedlot";
  import { t } from "../../../i18n";

  type Client = { id: number | string; name?: string; kind?: string };
  type Row = Record<string, any>;

  let {
    clients = [],
    currentClient = null,
    lots = [],
    feedTypes = [],
    today = "",
    publicBackendUrl = "",
  }: {
    clients?: Client[];
    currentClient?: Client | null;
    lots?: Row[];
    feedTypes?: Row[];
    today?: string;
    publicBackendUrl?: string;
  } = $props();

  function reload() {
    if (typeof window !== "undefined") window.location.reload();
  }
</script>

<FeedlotShell
  active="racion"
  clients={clients}
  currentClient={currentClient}
  breadcrumb={t("feedlot_module_racion_title")}
  switcherPattern={`/feedlot/racion?client={id}`}
>
  <slot name="session" slot="session" />

  <div class="mx-auto flex w-full max-w-4xl flex-col gap-6">
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-bold tracking-tight">{t("feedlot_module_racion_title")}</h1>
      <p class="text-sm text-muted-foreground">{t("feedlot_module_racion_subtitle")}</p>
    </div>

    <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
      <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_serve")}</h2>
      <RationServeForm
        clients={clients}
        lots={lots}
        feedTypes={feedTypes}
        today={today}
        publicBackendUrl={publicBackendUrl}
        onsaved={reload}
      />
    </div>
  </div>
</FeedlotShell>
