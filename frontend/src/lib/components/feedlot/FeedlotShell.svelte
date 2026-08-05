<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  The single app shell every feedlot module renders inside ([[FEEDLOT]]):
  full-width header (Breadcrumb + session), then a row of FancyDrawer /
  pinned rail + module content. Nav never climbs into the header band.
  Pure chrome — it never fetches or mutates. Mounts with zero props and
  never throws ([[adr-22-showcase-ready-components]] rule 1). Copy via i18n.
-->
<script lang="ts">
  import { onMount } from "svelte";
  import { t } from "../../../i18n";
  import FeedlotFancyNav from "./FeedlotFancyNav.svelte";
  import { Breadcrumb, type BreadcrumbItem } from "$lib/components/nav";
  import { DEFAULTS, readThemeCookie, type SidebarSide } from "$lib/theme";

  type Client = { id: number | string; name?: string; kind?: string };

  let {
    active = "dashboard",
    currentClient = null,
    breadcrumb = "",
    /** Optional visible back link above the content. */
    backHref = "",
    backLabel = "",
    /** Dock edge from theme_config.sidebarSide; defaults from cookie / DEFAULTS. */
    sidebarSide = undefined,
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
    sidebarSide?: SidebarSide;
  } = $props();

  let navOpen = $state(false);
  let mobileOpen = $state(false);
  let navPinned = $state(false);
  let resolvedSide = $state<SidebarSide>(sidebarSide ?? DEFAULTS.sidebarSide);

  onMount(() => {
    if (sidebarSide) {
      resolvedSide = sidebarSide;
      return;
    }
    resolvedSide = readThemeCookie().sidebarSide ?? DEFAULTS.sidebarSide;
  });

  const currentId = $derived(currentClient?.id ?? null);

  const crumbs = $derived.by((): BreadcrumbItem[] => {
    const trail: BreadcrumbItem[] = [];
    if (currentClient?.id != null) {
      const label = currentClient.name || t("feedlot_dash_fallback");
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

<div class="feedlot-app flex min-h-screen flex-col">
  <header class="flex w-full shrink-0 items-center justify-end gap-3 px-6 pt-8 sm:px-10">
    <Breadcrumb items={crumbs} />
    <slot name="session" />
  </header>

  <div class="flex min-h-0 min-w-0 flex-1">
    <FeedlotFancyNav
      {active}
      clientId={currentId}
      side={resolvedSide}
      bind:open={navOpen}
      bind:mobileOpen
      bind:pinned={navPinned}
    />

    <div class="flex min-w-0 flex-1 flex-col">
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
</div>
