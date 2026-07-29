<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]] · [[adr-22-showcase-ready-components]] · [[adr-24-feedlot-domain]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  The feedlot clients index / post-login landing ([[FEEDLOT]]). Renders inside the
  shared green FeedlotShell so the design is consistent with every module and the
  dashboard (redesign — no more plain-white revert). Lists clients with their
  balance, links each to its dashboard, carries the "new client" write form
  (`POST /api/clients/`, [[adr-24-feedlot-domain]] rule 3), and offers the topbar
  dropdown to jump straight into a client. One hydrated island that renders its own
  SessionBadge into the shell's session slot. Copy via i18n ([[LOCALIZATION]]).
  Mounts with zero props, never throws, no write on mount
  ([[adr-22-showcase-ready-components]] rules 1–2).
-->
<script lang="ts">
  import FeedlotShell from "$lib/components/feedlot/FeedlotShell.svelte";
  import SessionBadge from "$lib/components/auth/SessionBadge.svelte";
  import { ClientsTable, ClientForm, M365StatusCard } from "$lib/components/feedlot";
  import type { Me } from "$lib/types/user";
  import { t } from "../../../i18n";

  type Client = {
    id: number;
    name: string;
    kind?: string;
    tax_id?: string;
    balance?: string | number | null;
  };

  let {
    clients = [],
    publicBackendUrl = "",
    me = null,
    pending = false,
    /** Graph words fetched server-side by the page ([[adr-13-m365-graph]] rule 3). */
    m365Hello = "",
    m365World = "",
  }: {
    clients?: Client[];
    publicBackendUrl?: string;
    me?: Me | null;
    pending?: boolean;
    m365Hello?: string;
    m365World?: string;
  } = $props();

  // A successful create reloads so the new client appears in the list. The reload
  // is submit-initiated, never on mount ([[adr-22-showcase-ready-components]] rule 2).
  function reload(): void {
    if (typeof window !== "undefined") window.location.reload();
  }
</script>

<FeedlotShell
  active="clients"
  clients={clients}
  currentClient={null}
  breadcrumb={t("feedlot_clients_title")}
  switcherPattern={"/feedlot/{id}/"}
>
  <SessionBadge
    slot="session"
    {me}
    {pending}
    {publicBackendUrl}
    loginLabel={t("auth_login")}
    logoutLabel={t("auth_logout")}
  />

  <div class="mx-auto flex w-full max-w-4xl flex-col gap-6">
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-bold tracking-tight">{t("feedlot_clients_title")}</h1>
      <p class="max-w-2xl text-sm text-muted-foreground">{t("feedlot_clients_intro")}</p>
    </div>

    <!-- The Graph integration strip. Its old home was the lobby, which the
         module-first redesign removed; this roster IS the post-login landing a
         role-holding session reaches, so the status lands where it is seen. -->
    <M365StatusCard hello={m365Hello} world={m365World} />

    <details class="rounded-2xl p-5"
      style="background: var(--card); border: var(--hairline) solid var(--border);">
      <summary class="cursor-pointer text-sm font-semibold text-foreground">
        {t("feedlot_form_new_client_cta")}
      </summary>
      <div class="pt-4">
        <ClientForm {publicBackendUrl} onsaved={reload} />
      </div>
    </details>

    <div class="rounded-2xl p-2 sm:p-4"
      style="background: var(--card); border: var(--hairline) solid var(--border);">
      <ClientsTable
        {clients}
        columns={{
          name: t("feedlot_col_client"),
          kind: t("feedlot_col_kind"),
          taxId: t("feedlot_col_taxid"),
          balance: t("feedlot_col_balance"),
          action: "",
        }}
        detailLabel={t("feedlot_view_dashboard")}
        emptyLabel={t("feedlot_empty_clients")}
      />
    </div>
  </div>
</FeedlotShell>
