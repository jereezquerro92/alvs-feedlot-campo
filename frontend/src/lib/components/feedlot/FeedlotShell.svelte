<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  The single green app shell every feedlot module renders inside ([[FEEDLOT]]):
  dark-green sidebar + white topbar (breadcrumb, client dropdown, session slot) +
  an optional visible "back" button, then the module content as the default slot.
  Pure chrome — it never fetches or mutates. Every module page composes it so the
  new design is applied consistently instead of each page reinventing its frame.
  Mounts with zero props and never throws ([[adr-22-showcase-ready-components]]
  rule 1); all colour is `.feedlot-app` tokens ([[DESIGN-SYSTEM]]). Copy via i18n.
-->
<script lang="ts">
  import { t } from "../../../i18n";
  import FeedlotSidebar from "./FeedlotSidebar.svelte";
  import ClientSwitcher from "./ClientSwitcher.svelte";

  type Client = { id: number | string; name?: string; kind?: string };

  let {
    active = "dashboard",
    clients = [],
    currentClient = null,
    breadcrumb = "",
    /** URL template (`{id}`) the client dropdown navigates to. */
    switcherPattern = "/feedlot/{id}/",
    /** Optional "all clients" entry in the dropdown. */
    allLabel = "",
    allHref = "",
    /** Optional visible back link above the content. */
    backHref = "",
    backLabel = "",
    showSwitcher = true,
  }: {
    active?: string;
    clients?: Client[];
    currentClient?: Client | null;
    breadcrumb?: string;
    switcherPattern?: string;
    allLabel?: string;
    allHref?: string;
    backHref?: string;
    backLabel?: string;
    showSwitcher?: boolean;
  } = $props();

  const currentId = $derived(currentClient?.id ?? null);
  const KINDS: Record<string, string> = {
    boarding: t("feedlot_kind_boarding"),
    own: t("feedlot_kind_own"),
  };
  const kindLabel = $derived(
    currentClient?.kind ? (KINDS[currentClient.kind] ?? currentClient.kind) : "",
  );
</script>

<div class="feedlot-app flex min-h-screen" style="background: var(--canvas);">
  <FeedlotSidebar {active} clientId={currentId} />

  <div class="flex min-w-0 flex-1 flex-col">
    <!-- Topbar -->
    <header
      class="sticky top-0 z-20 flex items-center gap-3 px-5 py-3 sm:px-8"
      style="background: var(--card); border-bottom: var(--hairline) solid var(--border);"
    >
      <div class="flex min-w-0 flex-1 items-center gap-3">
        {#if breadcrumb}
          <span class="hidden text-sm font-medium text-muted-foreground sm:inline">{breadcrumb}</span>
          <span class="hidden text-muted-foreground/50 sm:inline" aria-hidden="true">/</span>
        {/if}

        {#if showSwitcher}
          <ClientSwitcher
            {clients}
            {currentId}
            pattern={switcherPattern}
            {allLabel}
            {allHref}
          />
        {/if}

        {#if kindLabel}
          <span class="hidden rounded-full bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary md:inline">
            {kindLabel}
          </span>
        {/if}
      </div>

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

    <!-- Mobile module nav (sidebar is hidden < lg) -->
    <nav class="flex gap-2 overflow-x-auto px-4 py-2.5 lg:hidden"
      style="background: var(--card); border-bottom: var(--hairline) solid var(--border);">
      <slot name="mobile-nav" />
    </nav>

    <main class="flex-1 px-4 py-6 sm:px-8 sm:py-8">
      {#if backHref}
        <a
          href={backHref}
          class="mb-5 inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-semibold transition-colors hover:bg-accent"
          style="border: var(--hairline) solid var(--border); color: var(--foreground);"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round" class="size-4" aria-hidden="true">
            <path d="m15 18-6-6 6-6" />
          </svg>
          {backLabel || t("feedlot_back")}
        </a>
      {/if}

      <slot />
    </main>
  </div>
</div>
