<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  The feedlot app's white top bar ([[FEEDLOT]]): breadcrumb, the current-client
  dropdown (a real ClientSwitcher when a `clients` list is given, else a static pill
  linking back to the roster), the client-kind pill, and a `session` slot for the auth
  badge. Pure presentation/navigation, read-only. Mounts with zero props and never
  throws ([[adr-22-showcase-ready-components]] rule 1). Copy via i18n ([[LOCALIZATION]]).
-->
<script lang="ts">
  import { t } from "../../../i18n";
  import ClientSwitcher from "./ClientSwitcher.svelte";

  let {
    breadcrumb = "",
    client = null,
    clients = [],
    switcherPattern = "/feedlot/{id}/",
    allLabel = "",
    allHref = "",
  }: {
    breadcrumb?: string;
    client?: { id?: number; name?: string; kind?: string } | null;
    /** When non-empty, render the real dropdown instead of the static pill. */
    clients?: Array<{ id: number | string; name?: string; kind?: string }>;
    switcherPattern?: string;
    allLabel?: string;
    allHref?: string;
  } = $props();

  const KINDS: Record<string, string> = {
    boarding: t("feedlot_kind_boarding"),
    own: t("feedlot_kind_own"),
  };
  const kindLabel = $derived(client?.kind ? (KINDS[client.kind] ?? client.kind) : "");
</script>

<header
  class="sticky top-0 z-20 flex items-center gap-3 px-5 py-3 sm:px-8"
  style="background: var(--card); border-bottom: var(--hairline) solid var(--border);"
>
  <!-- Breadcrumb + client selector -->
  <div class="flex min-w-0 flex-1 items-center gap-3">
    {#if breadcrumb}
      <span class="hidden text-sm font-medium text-muted-foreground sm:inline">{breadcrumb}</span>
      <span class="hidden text-muted-foreground/50 sm:inline" aria-hidden="true">/</span>
    {/if}

    {#if clients.length > 0}
      <ClientSwitcher
        {clients}
        currentId={client?.id ?? null}
        pattern={switcherPattern}
        {allLabel}
        {allHref}
      />
    {:else if client?.name}
      <a
        href="/feedlot/"
        title={t("feedlot_topbar_switch")}
        class="inline-flex min-w-0 items-center gap-2 rounded-full px-3 py-1.5 text-sm font-semibold transition-colors hover:bg-accent"
        style="border: var(--hairline) solid var(--border);"
      >
        <span class="size-2 shrink-0 rounded-full bg-primary" aria-hidden="true"></span>
        <span class="truncate">{client.name}</span>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
          stroke-linecap="round" stroke-linejoin="round" class="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </a>
    {/if}

    {#if kindLabel}
      <span class="hidden rounded-full bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary md:inline">
        {kindLabel}
      </span>
    {/if}
  </div>

  <!-- Right-hand actions + session -->
  <div class="flex items-center gap-1.5">
    <span class="grid size-9 place-items-center rounded-full text-muted-foreground" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"
        stroke-linecap="round" stroke-linejoin="round" class="size-[1.1rem]">
        <circle cx="11" cy="11" r="7" /><path d="m20 20-3-3" />
      </svg>
    </span>
    <span class="grid size-9 place-items-center rounded-full text-muted-foreground" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"
        stroke-linecap="round" stroke-linejoin="round" class="size-[1.1rem]">
        <path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6" /><path d="M10 20a2 2 0 0 0 4 0" />
      </svg>
    </span>
    <div class="ml-1"><slot name="session" /></div>
  </div>
</header>
