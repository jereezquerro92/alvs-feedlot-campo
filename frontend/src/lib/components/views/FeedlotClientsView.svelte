<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  The feedlot clients index page ([[FEEDLOT]]). Lists clients and their account
  balance, links each to its dashboard, and carries the "new client" form — a write
  through the declared `POST /api/clients/` endpoint ([[adr-24-feedlot-domain]] rule
  3). Like [[FeedlotLoadView]] this is a single hydrated island that renders its own
  SessionBadge and write form (rung 3, [[adr-04-frontend-and-design-system]] rule 3),
  rather than receiving them as slotted sub-islands. Copy resolves through the i18n
  layer ([[LOCALIZATION]]); values Spanish, keys English. Mounts with zero props and
  never throws, and a bare mount issues no write ([[adr-22-showcase-ready-components]]
  rules 1–2).
-->
<script lang="ts">
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import { SectionTitle } from "$lib/components/primitives/titles";
  import SessionBadge from "$lib/components/auth/SessionBadge.svelte";
  import { ClientsTable, ClientForm } from "$lib/components/feedlot";
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
    projectSlug = "",
    clients = [],
    publicBackendUrl = "",
    me = null,
    pending = false,
  }: {
    projectSlug?: string;
    clients?: Client[];
    publicBackendUrl?: string;
    me?: Me | null;
    pending?: boolean;
  } = $props();

  // A successful create reloads so the new client appears in the list. The reload
  // is submit-initiated, never on mount ([[adr-22-showcase-ready-components]] rule 2).
  function reload(): void {
    if (typeof window !== "undefined") window.location.reload();
  }
</script>

<div class="min-h-screen flex flex-col">
  <header class="flex w-full items-center justify-between gap-4 px-6 pt-8 sm:px-10">
    <Badge variant="outline" class="text-sm font-semibold tracking-wide">{projectSlug}</Badge>
    <SessionBadge
      {me}
      {pending}
      {publicBackendUrl}
      loginLabel={t("auth_login")}
      logoutLabel={t("auth_logout")}
    />
  </header>

  <main class="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 px-6 py-12">
    <div class="flex flex-col gap-2">
      <SectionTitle as="h1">{t("feedlot_clients_title")}</SectionTitle>
      <p class="max-w-2xl text-muted-foreground">{t("feedlot_clients_intro")}</p>
    </div>

    <details class="rounded-lg border border-border/40 bg-card p-4 shadow-sm">
      <summary class="cursor-pointer text-sm font-medium text-foreground">
        {t("feedlot_form_new_client_cta")}
      </summary>
      <div class="pt-4">
        <ClientForm {publicBackendUrl} onsaved={reload} />
      </div>
    </details>

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

    <div>
      <Button href="/" variant="secondary" size="sm">{t("feedlot_back_home")}</Button>
    </div>
  </main>
</div>
