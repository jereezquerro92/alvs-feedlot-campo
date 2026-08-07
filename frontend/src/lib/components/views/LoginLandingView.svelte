<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]] · [[adr-20-authorization-lobby]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Feedlot splash / login ([[FEEDLOT]]): anonymous and role-less (pending)
  sessions land here; a role-holding session never reaches this view
  (index.astro redirects to /feedlot/). Pure presentation — Cognito
  /accounts/login/ is the only anonymous action ([[adr-10-auth]]); pending
  sessions use the session slot to log out. Mounts with zero props and never
  throws ([[adr-22-showcase-ready-components]] rule 1). Colour is `.feedlot-app`
  tokens ([[DESIGN-SYSTEM]]); copy via i18n ([[LOCALIZATION]]). Brand is
  typography-only (no glyph) — wording draws from ALVS Group public identity
  (linktr.ee/alvsgroup: holding + ganadería).
-->
<script lang="ts">
  import { t } from "../../../i18n";

  let {
    publicBackendUrl = "",
    /** Authenticated but role-less: awaiting a group grant (adr-20 lobby). */
    pending = false,
    /** Bounced off a gated page with ?denied=1 (authGate). */
    denied = false,
    loginLabel = "",
  }: {
    publicBackendUrl?: string;
    pending?: boolean;
    denied?: boolean;
    loginLabel?: string;
  } = $props();

  const supportEmail = t("login_support_email");
</script>

<div class="feedlot-app login-splash relative flex min-h-screen flex-col">
  <div class="login-splash__glow" aria-hidden="true"></div>
  <div class="login-splash__horizon" aria-hidden="true"></div>

  <div class="absolute right-5 top-5 z-20"><slot name="session" /></div>

  <main
    class="login-splash__stage relative z-10 mx-auto flex w-full max-w-lg flex-1 flex-col items-center justify-center px-6 py-16 text-center"
  >
    <div class="login-splash__brand flex flex-col items-center gap-3">
      <h1 class="login-splash__title text-4xl font-bold tracking-tight sm:text-5xl">
        {t("login_title")}
      </h1>
      <p class="login-splash__subtitle mx-auto max-w-sm text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">
        {t("login_subtitle")}
      </p>
    </div>

    <div class="login-splash__actions mt-12 flex w-full max-w-sm flex-col gap-4">
      {#if denied}
        <div
          class="rounded-xl px-4 py-3 text-left text-sm normal-case tracking-normal"
          style="background: color-mix(in oklch, var(--destructive) 12%, transparent); color: var(--destructive);"
          role="status"
        >
          <p class="font-semibold">{t("denied_title")}</p>
          <p class="mt-0.5 opacity-90">{t("denied_body")}</p>
        </div>
      {/if}

      {#if pending}
        <div
          class="rounded-xl px-4 py-3 text-left text-sm normal-case tracking-normal"
          style="background: color-mix(in oklch, var(--primary) 10%, var(--muted)); color: var(--muted-foreground);"
          role="status"
        >
          <p class="font-semibold" style="color: var(--foreground);">{t("pending_title")}</p>
          <p class="mt-0.5">{t("lobby_pending")}</p>
        </div>
        <p class="text-xs normal-case tracking-normal text-muted-foreground">{t("login_pending_hint")}</p>
      {:else}
        <a
          href={`${publicBackendUrl}/accounts/login/`}
          class="login-splash__cta inline-flex w-full items-center justify-center rounded-xl px-5 py-3.5 text-sm font-semibold normal-case tracking-normal"
          style="background: var(--primary); color: var(--primary-foreground);"
        >
          {loginLabel || t("auth_login")}
        </a>
        <p class="text-xs normal-case tracking-normal text-muted-foreground">{t("login_hint")}</p>
      {/if}
    </div>
  </main>

  <p class="relative z-10 pb-6 text-center text-xs text-muted-foreground">
    {t("login_support_prefix")}
    <a
      class="underline underline-offset-2 transition-opacity hover:opacity-80"
      href={`mailto:${supportEmail}`}
      style="color: var(--foreground);"
    >{supportEmail}</a>
  </p>
</div>

<style>
  .login-splash {
    isolation: isolate;
    overflow: hidden;
  }

  .login-splash__glow {
    pointer-events: none;
    position: absolute;
    inset: -20% -10% auto;
    height: 70%;
    background:
      radial-gradient(
        ellipse 70% 55% at 50% 0%,
        color-mix(in oklch, var(--primary) 28%, transparent) 0%,
        transparent 70%
      );
    animation: login-splash-glow 8s ease-in-out infinite alternate;
  }

  .login-splash__horizon {
    pointer-events: none;
    position: absolute;
    inset: auto 0 0;
    height: 42%;
    background: linear-gradient(
      to top,
      color-mix(in oklch, var(--sidebar) 18%, transparent) 0%,
      transparent 100%
    );
  }

  .login-splash__stage {
    animation: login-splash-rise 0.7s ease-out both;
  }

  .login-splash__title {
    letter-spacing: -0.03em;
    line-height: 1.1;
  }

  .login-splash__cta {
    transition:
      opacity 0.15s ease,
      transform 0.15s ease,
      box-shadow 0.2s ease;
    box-shadow: 0 0.75rem 1.75rem -0.75rem color-mix(in oklch, var(--primary) 45%, transparent);
  }

  .login-splash__cta:hover {
    opacity: 0.94;
    transform: translateY(-0.0625rem);
  }

  .login-splash__cta:active {
    transform: translateY(0);
  }

  .login-splash__actions {
    animation: login-splash-rise 0.7s ease-out 0.12s both;
  }

  @keyframes login-splash-rise {
    from {
      opacity: 0;
      transform: translateY(0.75rem);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes login-splash-glow {
    from {
      opacity: 0.85;
      transform: scale(1);
    }
    to {
      opacity: 1;
      transform: scale(1.04);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .login-splash__glow,
    .login-splash__stage,
    .login-splash__actions {
      animation: none;
    }

    .login-splash__cta {
      transition: none;
    }
  }
</style>
