<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]] · [[adr-24-feedlot-domain]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  The feedlot clients index / post-login landing ([[FEEDLOT]]). Initial click:
  a centered ChoiceList of clients inside PageStage — pick one, open its
  operation. Secondary: M365 strip + new-client form. Mounts with zero props,
  never throws, no write on mount ([[adr-22-showcase-ready-components]] rules
  1–2). Copy via i18n ([[LOCALIZATION]]).
-->
<script lang="ts">
  import FeedlotShell from "$lib/components/feedlot/FeedlotShell.svelte";
  import SessionBadge from "$lib/components/auth/SessionBadge.svelte";
  import { ClientForm, M365StatusCard } from "$lib/components/feedlot";
  import { ChoiceList, type ChoiceItem } from "$lib/components/dashboard";
  import { PageStage } from "$lib/components/primitives/titles";
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
    /** Graph words fetched server-side by the page ([[adr-13-m365-graph]] rule 3). */
    m365Hello = "",
    m365World = "",
  }: {
    clients?: Client[];
    publicBackendUrl?: string;
    me?: Me | null;
    m365Hello?: string;
    m365World?: string;
  } = $props();

  const KINDS: Record<string, string> = {
    boarding: t("feedlot_kind_boarding"),
    own: t("feedlot_kind_own"),
  };

  const choices = $derived.by((): ChoiceItem[] =>
    clients.map((c) => ({
      id: c.id,
      label: c.name,
      href: `/feedlot/${c.id}/`,
      badge: KINDS[c.kind ?? ""] ?? c.kind ?? undefined,
      badgeVariant: "success" as const,
    })),
  );

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
    {publicBackendUrl}
    loginLabel={t("auth_login")}
    logoutLabel={t("auth_logout")}
  />

  <PageStage>
    <!-- Graph status stays reachable on the landing without competing for the pick. -->
    <M365StatusCard hello={m365Hello} world={m365World} />

    <ChoiceList
      title={t("feedlot_clients_title")}
      subtitle={t("feedlot_clients_intro")}
      items={choices}
      emptyLabel={t("feedlot_empty_clients")}
    >
      {#snippet footer()}
        <details class="w-full">
          <summary class="cursor-pointer text-sm font-semibold text-foreground">
            {t("feedlot_form_new_client_cta")}
          </summary>
          <div class="pt-3">
            <ClientForm {publicBackendUrl} onsaved={reload} />
          </div>
        </details>
      {/snippet}
    </ChoiceList>
  </PageStage>
</FeedlotShell>
