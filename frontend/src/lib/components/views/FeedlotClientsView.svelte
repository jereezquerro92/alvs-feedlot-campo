<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  The feedlot clients index page ([[FEEDLOT]]). Read-only: it lists clients and
  their account balance and links each to its dashboard. Copy resolves through
  the i18n layer ([[LOCALIZATION]]); values are Spanish, keys English. Mounts
  with zero props and never throws ([[adr-22-showcase-ready-components]] rule 1).
-->
<script lang="ts">
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import { SectionTitle } from "$lib/components/primitives/titles";
  import { ClientsTable } from "$lib/components/feedlot";
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
  }: {
    projectSlug?: string;
    clients?: Client[];
  } = $props();
</script>

<div class="min-h-screen flex flex-col">
  <header class="flex w-full items-center justify-between gap-4 px-6 pt-8 sm:px-10">
    <Badge variant="outline" class="text-sm font-semibold tracking-wide">{projectSlug}</Badge>
    <slot name="session" />
  </header>

  <main class="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 px-6 py-12">
    <div class="flex flex-col gap-2">
      <SectionTitle as="h1">{t("feedlot_clients_title")}</SectionTitle>
      <p class="max-w-2xl text-muted-foreground">{t("feedlot_clients_intro")}</p>
    </div>

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
