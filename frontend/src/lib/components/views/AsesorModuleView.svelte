<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]] · [[adr-22-showcase-ready-components]] · [[adr-24-feedlot-domain]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[FEEDLOT]]
     LIVE-DOC:END -->

<!--
  The AI-advisor module ([[adr-35-conversational-assistant]], [[adr-27-advisors-generative]]).
  Module-first: pick a client in the topbar, then ask the advisor about THAT client's
  data. The advisor has reach across every client the operator may see (the switcher
  lists them all), but each answer is scoped to one client by a hard backend boundary
  — a lot-owner portal session is confined to its own client and can never query
  another account (adr-27 rule 2, [[adr-44-field-operational-roles]] decision 3). The
  chat itself lives in `AsesorChat`; this view only frames it in the green shell.
  Mounts with zero props and never throws ([[adr-22-showcase-ready-components]] rule 1);
  no request until the user asks (rule 2). Green tokens ([[DESIGN-SYSTEM]]); i18n copy.
-->
<script lang="ts">
  import FeedlotShell from "$lib/components/feedlot/FeedlotShell.svelte";
  import { AsesorChat } from "$lib/components/feedlot";
  import { t } from "../../../i18n";

  type Client = { id: number | string; name?: string; kind?: string };

  let {
    clients = [],
    currentClient = null,
    publicBackendUrl = "",
  }: {
    clients?: Client[];
    currentClient?: Client | null;
    publicBackendUrl?: string;
  } = $props();

  const clientId = $derived(currentClient ? Number(currentClient.id) : null);
  const clientName = $derived(currentClient?.name ?? "");
</script>

<FeedlotShell
  active="advisors"
  clients={clients}
  currentClient={currentClient}
  breadcrumb={t("feedlot_module_asesor_title")}
  switcherPattern={`/feedlot/asesor?client={id}`}
>
  <slot name="session" slot="session" />

  <div class="mx-auto flex w-full max-w-4xl flex-col gap-6">
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-bold tracking-tight">{t("feedlot_module_asesor_title")}</h1>
      <p class="text-sm text-muted-foreground">{t("feedlot_module_asesor_subtitle")}</p>
    </div>

    {#if !currentClient}
      <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
        <p class="text-sm text-muted-foreground">{t("feedlot_asesor_pick_client")}</p>
      </div>
    {:else}
      <div class="rounded-2xl px-4 py-3 text-sm" style="background: var(--muted);">
        {t("feedlot_asesor_asks_about")} <span class="font-semibold text-foreground">{currentClient.name}</span>
      </div>
      <AsesorChat
        clientId={clientId}
        clientName={clientName}
        publicBackendUrl={publicBackendUrl}
      />
    {/if}
  </div>
</FeedlotShell>
