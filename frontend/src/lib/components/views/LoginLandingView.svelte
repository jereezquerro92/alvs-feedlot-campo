<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]] · [[adr-20-authorization-lobby]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  The landing IS the login ([[FEEDLOT]], redesign): a logged-out visitor sees a
  single green sign-in screen, not the old feedlot/showcase/chat menu — of that
  menu only the design-system gallery link survives, and a role-holding
  session is redirected straight to the feedlot before this view ever renders
  (index.astro). This screen is reached only by an anonymous or role-less
  (pending) session. Pure presentation; the only actions are two links — Cognito
  /dev-login ([[adr-10-auth]]) and the gallery — no mutation, no fetch. Mounts with
  zero props and never throws ([[adr-22-showcase-ready-components]] rule 1). Colour
  is `.feedlot-app` tokens ([[DESIGN-SYSTEM]]); copy via i18n ([[LOCALIZATION]]).
-->
<script lang="ts">
  import { t } from "../../../i18n";

  let {
    projectSlug = "",
    publicBackendUrl = "",
    /** Authenticated but role-less: awaiting a group grant (adr-20 lobby). */
    pending = false,
    /** Bounced off a gated page with ?denied=1 (authGate). */
    denied = false,
    loginLabel = "",
  }: {
    projectSlug?: string;
    publicBackendUrl?: string;
    pending?: boolean;
    denied?: boolean;
    loginLabel?: string;
  } = $props();
</script>

<div class="feedlot-app relative flex min-h-screen flex-col items-center justify-center px-6 py-12">
  <!-- Session control (logout for a pending session) -->
  <div class="absolute right-5 top-5"><slot name="session" /></div>

  <div class="flex w-full max-w-md flex-col items-center gap-8">
    <!-- Brand -->
    <div class="flex flex-col items-center gap-3 text-center">
      <span class="grid size-14 place-items-center rounded-2xl text-2xl"
        style="background: var(--primary); color: var(--primary-foreground);" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"
          stroke-linecap="round" stroke-linejoin="round" class="size-7">
          <path d="M3 21V10l9-6 9 6v11" /><path d="M9 21v-6h6v6" />
        </svg>
      </span>
      <div class="flex flex-col gap-1">
        <h1 class="text-2xl font-bold tracking-tight">{t("login_title")}</h1>
        <p class="text-sm text-muted-foreground">{t("login_subtitle")}</p>
      </div>
    </div>

    <!-- Card -->
    <div class="flex w-full flex-col gap-5 rounded-2xl p-6"
      style="background: var(--card); border: var(--hairline) solid var(--border);">
      {#if denied}
        <div class="rounded-xl px-4 py-3 text-sm"
          style="background: color-mix(in oklch, var(--destructive) 12%, transparent); color: var(--destructive);">
          <p class="font-semibold">{t("denied_title")}</p>
          <p class="mt-0.5 opacity-90">{t("denied_body")}</p>
        </div>
      {/if}

      {#if pending}
        <div class="rounded-xl px-4 py-3 text-sm"
          style="background: var(--muted); color: var(--muted-foreground);">
          <p class="font-semibold" style="color: var(--foreground);">{t("pending_title")}</p>
          <p class="mt-0.5">{t("lobby_pending")}</p>
        </div>
        <!-- A pending session is authenticated already; the session menu (topbar)
             offers logout. Nothing to log into again. -->
        <p class="text-center text-xs text-muted-foreground">{t("login_pending_hint")}</p>
      {:else}
        <a
          href={`${publicBackendUrl}/accounts/login/`}
          class="inline-flex w-full items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold transition-opacity hover:opacity-90"
          style="background: var(--primary); color: var(--primary-foreground);"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round" class="size-4" aria-hidden="true">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" /><path d="M10 17l5-5-5-5" /><path d="M15 12H3" />
          </svg>
          {loginLabel || t("auth_login")}
        </a>
        <p class="text-center text-xs text-muted-foreground">{t("login_hint")}</p>

        <!-- The design-system gallery stays reachable from the landing.
             It is an affordance only: the route itself is gated, so an anonymous
             visitor following it is bounced back here ([[adr-20-authorization-lobby]]). -->
        <a
          href="/showcase/components/"
          class="inline-flex w-full items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition-colors hover:bg-accent"
          style="border: var(--hairline) solid var(--border); color: var(--foreground);"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"
            stroke-linecap="round" stroke-linejoin="round" class="size-4" aria-hidden="true">
            <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" />
            <rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
          </svg>
          {t("nav_showcase")}
        </a>
      {/if}
    </div>

    <p class="text-xs text-muted-foreground/70">{projectSlug}</p>
  </div>
</div>
