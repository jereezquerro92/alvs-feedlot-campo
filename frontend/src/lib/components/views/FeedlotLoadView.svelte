<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Data-entry surface for one client ([[FEEDLOT]], [[bdd-13-feedlot-data-entry]]).
  Unlike the read-only views, this one is a single hydrated island (rung 3 of the
  interactivity ladder, [[adr-04-frontend-and-design-system]] rule 3): it owns two
  write forms whose submit state lives client-side. Each form posts through a
  declared endpoint that routes to a domain service, never a raw write
  ([[adr-24-feedlot-domain]] rule 3). The view holds no mutation of its own and
  mounts safely with zero props ([[adr-22-showcase-ready-components]] rules 1–2).
  Copy through the i18n layer, Spanish rendered / English keys ([[LOCALIZATION]]).
-->
<script lang="ts">
  import * as Card from "$lib/components/ui/card";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import { SectionTitle } from "$lib/components/primitives/titles";
  import SessionBadge from "$lib/components/auth/SessionBadge.svelte";
  import { FeedingForm, WeighingForm } from "$lib/components/feedlot";
  import type { Me } from "$lib/types/user";
  import { t } from "../../../i18n";

  let {
    projectSlug = "",
    client = null,
    animals = [],
    lots = [],
    feedTypes = [],
    today = "",
    publicBackendUrl = "",
    me = null,
    pending = false,
  }: {
    projectSlug?: string;
    client?: { id: number; name: string } | null;
    animals?: Array<Record<string, any>>;
    lots?: Array<Record<string, any>>;
    feedTypes?: Array<Record<string, any>>;
    today?: string;
    publicBackendUrl?: string;
    me?: Me | null;
    pending?: boolean;
  } = $props();
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

  <main class="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-6 py-12">
    <div class="flex flex-col gap-2">
      <SectionTitle as="h1">{t("feedlot_load_title")}</SectionTitle>
      <p class="text-sm text-muted-foreground">{client?.name ?? t("feedlot_dash_fallback")}</p>
      <p class="max-w-2xl text-sm text-muted-foreground">{t("feedlot_load_intro")}</p>
      {#if client?.id}
        <div>
          <Button href={`/feedlot/${client.id}/`} variant="secondary" size="sm">
            {t("feedlot_load_view_panel")}
          </Button>
        </div>
      {/if}
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <Card.Root class="border-border/40 shadow-sm">
        <Card.Header>
          <Card.Title class="text-base">{t("feedlot_form_feeding_title")}</Card.Title>
          <Card.Description>{t("feedlot_form_feeding_desc")}</Card.Description>
        </Card.Header>
        <Card.Content>
          <FeedingForm
            clientId={client?.id ?? null}
            {animals}
            {lots}
            {feedTypes}
            {today}
            {publicBackendUrl}
          />
        </Card.Content>
      </Card.Root>

      <Card.Root class="border-border/40 shadow-sm">
        <Card.Header>
          <Card.Title class="text-base">{t("feedlot_form_weighing_title")}</Card.Title>
          <Card.Description>{t("feedlot_form_weighing_desc")}</Card.Description>
        </Card.Header>
        <Card.Content>
          <WeighingForm {animals} {lots} {today} {publicBackendUrl} />
        </Card.Content>
      </Card.Root>
    </div>

    <div>
      <Button href="/feedlot/" variant="secondary" size="sm">{t("feedlot_back_clients")}</Button>
    </div>
  </main>
</div>
