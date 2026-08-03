<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]] · [[adr-44-field-operational-roles]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[FEEDLOT]]
     LIVE-DOC:END -->

<!--
  The users-and-permissions module ([[FEEDLOT]], redesign). REFERENCE-ONLY: it shows the
  current session's identity + Django groups (from `/api/me/`) and the six operative field
  roles ([[adr-44-field-operational-roles]]) with what each may see and load. It writes
  NOTHING and needs no dedicated user-list API: a role is a Django Group and a grant is an
  admin action in Django admin, never self-service ([[adr-20-authorization-lobby]] rule 3,
  [[adr-44-field-operational-roles]] decision 4) — so the page links to `/admin/` instead
  of offering a grant control. Authorization is decided in the backend off Group
  membership, never a login-provider claim ([[adr-10-auth]] rule 2); this view only
  reflects it. Mounts with zero props and never throws
  ([[adr-22-showcase-ready-components]] rule 1). Green `.feedlot-app` tokens
  ([[DESIGN-SYSTEM]]); copy via i18n ([[LOCALIZATION]]).
-->
<script lang="ts">
  import FeedlotShell from "$lib/components/feedlot/FeedlotShell.svelte";
  import { t } from "../../../i18n";
  import type { Me } from "$lib/types/user";

  let {
    me = null,
    publicBackendUrl = "",
  }: {
    me?: Me | null;
    publicBackendUrl?: string;
  } = $props();

  // The six operative field roles (adr-44). `group` is the literal Django group name
  // (never translated); the label and scope are rendered copy.
  const ROLES = [
    { group: "field_managers", label: "feedlot_role_field_managers", nature: "feedlot_role_field_managers_nature" },
    { group: "feed_operators", label: "feedlot_role_feed_operators", nature: "feedlot_role_feed_operators_nature" },
    { group: "lot_owners", label: "feedlot_role_lot_owners", nature: "feedlot_role_lot_owners_nature" },
    { group: "field_admins", label: "feedlot_role_field_admins", nature: "feedlot_role_field_admins_nature" },
    { group: "feedlot_owners", label: "feedlot_role_feedlot_owners", nature: "feedlot_role_feedlot_owners_nature" },
    { group: "workshop", label: "feedlot_role_workshop", nature: "feedlot_role_workshop_nature" },
  ] as const;

  const groups = $derived(me?.groups ?? []);
  const adminUrl = $derived(`${publicBackendUrl}/admin/`);
</script>

<FeedlotShell
  active="users"
  breadcrumb={t("feedlot_module_usuarios_title")}
  showSwitcher={false}
>
  <slot name="session" slot="session" />

  <div class="mx-auto flex w-full max-w-5xl flex-col gap-6">
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-bold tracking-tight">{t("feedlot_module_usuarios_title")}</h1>
      <p class="text-sm text-muted-foreground">{t("feedlot_module_usuarios_subtitle")}</p>
    </div>

    <!-- Current session -->
    <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
      <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_usuarios_session_title")}</h2>
      <dl class="grid gap-3 sm:grid-cols-2">
        <div>
          <dt class="text-xs uppercase tracking-wide text-muted-foreground">{t("feedlot_usuarios_session_name")}</dt>
          <dd class="text-sm font-medium">{[me?.given_name, me?.family_name].filter(Boolean).join(" ") || "—"}</dd>
        </div>
        <div>
          <dt class="text-xs uppercase tracking-wide text-muted-foreground">{t("feedlot_usuarios_session_email")}</dt>
          <dd class="text-sm font-medium">{me?.email || "—"}</dd>
        </div>
        <div class="sm:col-span-2">
          <dt class="mb-1 text-xs uppercase tracking-wide text-muted-foreground">{t("feedlot_usuarios_session_groups")}</dt>
          <dd>
            {#if groups.length === 0}
              <span class="text-sm text-muted-foreground">{t("feedlot_usuarios_session_no_groups")}</span>
            {:else}
              <div class="flex flex-wrap gap-1.5">
                {#each groups as g}
                  <span class="rounded-full px-2.5 py-1 text-xs font-medium"
                    style="background: var(--primary); color: var(--primary-foreground);">{g}</span>
                {/each}
              </div>
            {/if}
          </dd>
        </div>
        {#if me?.client}
          <div class="sm:col-span-2">
            <dt class="text-xs uppercase tracking-wide text-muted-foreground">{t("feedlot_usuarios_session_client")}</dt>
            <dd class="text-sm font-medium">{me.client.name}</dd>
          </div>
        {/if}
      </dl>
    </div>

    <!-- Roles reference -->
    <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
      <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_usuarios_roles_title")}</h2>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-xs uppercase tracking-wide text-muted-foreground">
              <th class="pb-2 pr-4 font-semibold">{t("feedlot_usuarios_col_role")}</th>
              <th class="pb-2 pr-4 font-semibold">{t("feedlot_usuarios_col_group")}</th>
              <th class="pb-2 font-semibold">{t("feedlot_usuarios_col_nature")}</th>
            </tr>
          </thead>
          <tbody>
            {#each ROLES as role (role.group)}
              {@const mine = groups.includes(role.group)}
              <tr style="border-top: var(--hairline) solid var(--border);">
                <td class="py-2.5 pr-4 font-medium">
                  {t(role.label)}
                  {#if mine}
                    <span class="ml-2 rounded-full px-2 py-0.5 text-[0.6rem] font-bold uppercase tracking-wide"
                      style="background: var(--primary); color: var(--primary-foreground);">✓</span>
                  {/if}
                </td>
                <td class="py-2.5 pr-4"><code class="text-xs text-muted-foreground">{role.group}</code></td>
                <td class="py-2.5 text-muted-foreground">{t(role.nature)}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Grants happen in Django admin (adr-20/44) -->
    <div class="rounded-2xl p-5" style="background: var(--muted); border: var(--hairline) solid var(--border);">
      <p class="mb-3 text-sm text-muted-foreground">{t("feedlot_usuarios_admin_note")}</p>
      <a
        href={adminUrl}
        class="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition-colors hover:opacity-90"
        style="background: var(--primary); color: var(--primary-foreground);"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
          stroke-linecap="round" stroke-linejoin="round" class="size-4" aria-hidden="true">
          <path d="M15 3h6v6M21 3l-9 9" /><path d="M21 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5" />
        </svg>
        {t("feedlot_usuarios_admin_link")}
      </a>
    </div>
  </div>
</FeedlotShell>
