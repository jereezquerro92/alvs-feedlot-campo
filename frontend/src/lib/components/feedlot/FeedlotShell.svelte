<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  The single green app shell every feedlot module renders inside ([[FEEDLOT]]):
  dark-green sidebar + default header (Breadcrumb pill + session slot) +
  an optional visible "back" button, then the module content as the default slot.
  Pure chrome — it never fetches or mutates. Every module page composes it so the
  new design is applied consistently instead of each page reinventing its frame.
  Mounts with zero props and never throws ([[adr-22-showcase-ready-components]]
  rule 1); colour tokens come from `.feedlot-app` ([[DESIGN-SYSTEM]]), while the
  page canvas (melt dots / spotlight) stays on `body` — no solid `--canvas` fill here.
  Copy via i18n.
-->
<script lang="ts">
  import { t } from "../../../i18n";
  import FeedlotSidebar from "./FeedlotSidebar.svelte";
  import { Breadcrumb, type BreadcrumbItem } from "$lib/components/nav";

  type Client = { id: number | string; name?: string; kind?: string };

  let {
    active = "dashboard",
    currentClient = null,
    breadcrumb = "",
    /** Optional visible back link above the content. */
    backHref = "",
    backLabel = "",
    // Retained so existing callers keep compiling; default header has no switcher.
    clients: _clients = [],
    switcherPattern: _switcherPattern = "/feedlot/{id}/",
    allLabel: _allLabel = "",
    allHref: _allHref = "",
    showSwitcher: _showSwitcher = true,
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

  const crumbs = $derived.by((): BreadcrumbItem[] => {
    const trail: BreadcrumbItem[] = [];
    if (currentClient?.id != null) {
      const label = currentClient.name || t("feedlot_dash_fallback");
      // On the client dashboard the client name is the current page; elsewhere it links home to that client.
      if (active === "dashboard") {
        trail.push({ label });
      } else {
        trail.push({ label, href: `/feedlot/${currentClient.id}/` });
        if (breadcrumb) trail.push({ label: breadcrumb });
      }
    } else if (breadcrumb) {
      trail.push({ label: breadcrumb });
    }
    return trail;
  });
</script>

<div class="feedlot-app flex min-h-screen">
  <FeedlotSidebar {active} clientId={currentId} />

  <div class="flex min-w-0 flex-1 flex-col">
    <header class="flex w-full items-center justify-end gap-3 px-6 pt-8 sm:px-10">
      <Breadcrumb items={crumbs} />
      <slot name="session" />
    </header>

    <!-- Mobile module nav (sidebar is hidden < lg) -->
    <nav class="flex gap-2 overflow-x-auto px-4 py-2.5 lg:hidden">
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
