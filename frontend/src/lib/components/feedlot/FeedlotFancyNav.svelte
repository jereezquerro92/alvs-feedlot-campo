<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Feedlot site menu driven by shell/nav-fsm: preference (cookie, SSR), viewport
  band (matchMedia), presentation (rail|drawer), active (from Base). Locked
  preference mounts rail + drawer together; CSS at RAIL_MIN_WIDTH picks which
  is visible so navigation never flashes unlocked. Unlocked = FancyDrawer only.
-->
<script lang="ts">
  import { onMount } from "svelte";
  import FancyDrawer from "$lib/components/overlay/FancyDrawer.svelte";
  import NavItem from "$lib/components/shell/NavItem.svelte";
  import NavLockToggle from "$lib/components/shell/NavLockToggle.svelte";
  import NavGlyph from "$lib/components/shell/NavGlyph.svelte";
  import type { NavIconName } from "$lib/components/shell/nav";
  import {
    DESK_MIN_WIDTH,
    RAIL_MIN_WIDTH,
    migrateLegacyNavLock,
    resolveNavFsm,
    resolvePresentation,
    resolveViewport,
    writeNavLockCookie,
    type NavLockPreference,
    type NavViewport,
  } from "$lib/components/shell/nav-fsm";
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";
  import {
    DEFAULTS,
    applyTheme,
    readThemeCookie,
    writeThemeCookie,
    type SidebarSide,
    type ThemeMode,
  } from "$lib/theme";

  const NAV_WIDTH = "12rem";

  let {
    clientId = null,
    active = "dashboard",
    /** SSR lock preference from the `nav_lock` cookie ([[adr-54-site-menu-lock-modes]]). */
    preference: preferenceProp = "unlocked" as NavLockPreference,
    open = $bindable(false),
    /** Dock edge from theme_config.sidebarSide ([[DESIGN-SYSTEM]]). */
    side = "left" as SidebarSide,
  }: {
    clientId?: number | string | null;
    active?: string;
    preference?: NavLockPreference;
    open?: boolean;
    side?: SidebarSide;
  } = $props();

  let localPreference = $state<NavLockPreference | null>(null);
  let viewport = $state<NavViewport>("desk");
  let mode = $state<ThemeMode>(DEFAULTS.mode);

  // SSR cookie wins until the user toggles; a new preferenceProp (navigation) clears the override.
  $effect(() => {
    preferenceProp;
    localPreference = null;
  });

  const preference = $derived(localPreference ?? preferenceProp);

  const fsm = $derived(
    resolveNavFsm({ preference, viewport, active }),
  );

  onMount(() => {
    mode = readThemeCookie().mode ?? DEFAULTS.mode;
    const migrated = migrateLegacyNavLock();
    if (migrated) localPreference = migrated;

    const railMq = window.matchMedia(`(min-width: ${RAIL_MIN_WIDTH})`);
    const deskMq = window.matchMedia(`(min-width: ${DESK_MIN_WIDTH})`);
    const syncViewport = () => {
      viewport = resolveViewport(railMq.matches, deskMq.matches);
    };
    syncViewport();
    railMq.addEventListener("change", syncViewport);
    deskMq.addEventListener("change", syncViewport);
    return () => {
      railMq.removeEventListener("change", syncViewport);
      deskMq.removeEventListener("change", syncViewport);
    };
  });

  function persistPreference(next: NavLockPreference) {
    localPreference = next;
    writeNavLockCookie(next);
    if (next === "locked" && resolvePresentation(next, viewport) === "rail") {
      open = true;
    }
  }

  function togglePin() {
    if (preference === "unlocked" && viewport === "mobile") return;
    persistPreference(preference === "locked" ? "unlocked" : "locked");
  }

  function toggleTheme() {
    const next: ThemeMode = mode === "dark" ? "light" : "dark";
    mode = next;
    const merged = { ...readThemeCookie(), mode: next };
    applyTheme(merged);
    writeThemeCookie(merged);
  }

  const themeIcon = $derived(mode === "dark" ? ("moon" as const) : ("sun" as const));

  const c = $derived(clientId ?? null);
  const q = $derived(c ? `?client=${c}` : "");
  const routes = $derived({
    dashboard: c ? `/feedlot/${c}/` : "/feedlot/",
    intake: `/feedlot/hacienda${q}`,
    feeding: `/feedlot/alimentacion${q}`,
    sanitary: `/feedlot/sanidad${q}`,
    pesajes: `/feedlot/pesajes${q}`,
    mixer: `/feedlot/mixer${q}`,
    racion: `/feedlot/racion${q}`,
    stocks: `/feedlot/stocks${q}`,
    ledger: `/feedlot/cuenta${q}`,
    gastos: `/feedlot/gastos${q}`,
    clients: "/feedlot/",
    advisors: `/feedlot/asesor${q}`,
    users: "/feedlot/usuarios",
    prices: "/feedlot/precios",
  } as Record<string, string>);

  type Item = { key: string; label: string; icon: NavIconName };
  const sections = $derived([
    {
      title: t("feedlot_nav_section_operation"),
      items: [
        { key: "dashboard", label: t("feedlot_nav_dashboard"), icon: "grid" as const },
        { key: "intake", label: t("feedlot_nav_intake"), icon: "cow" as const },
        { key: "feeding", label: t("feedlot_nav_feeding"), icon: "wheat" as const },
        { key: "sanitary", label: t("feedlot_nav_sanitary"), icon: "shield" as const },
        { key: "pesajes", label: t("feedlot_nav_pesajes"), icon: "scale" as const },
      ] as Item[],
    },
    {
      title: t("feedlot_nav_section_nutrition"),
      items: [
        { key: "mixer", label: t("feedlot_nav_mixer"), icon: "truck" as const },
        { key: "racion", label: t("feedlot_nav_racion"), icon: "blend" as const },
        { key: "stocks", label: t("feedlot_nav_stocks"), icon: "box" as const },
      ] as Item[],
    },
    {
      title: t("feedlot_nav_section_admin"),
      items: [
        { key: "ledger", label: t("feedlot_nav_ledger"), icon: "receipt" as const },
        { key: "gastos", label: t("feedlot_nav_gastos"), icon: "coins" as const },
        { key: "clients", label: t("feedlot_nav_clients"), icon: "users" as const },
        { key: "advisors", label: t("feedlot_nav_advisors"), icon: "spark" as const },
        { key: "users", label: t("feedlot_nav_users"), icon: "key" as const },
      ] as Item[],
    },
    {
      title: t("feedlot_nav_section_reference"),
      items: [
        { key: "prices", label: t("feedlot_nav_prices"), icon: "tag" as const },
      ] as Item[],
    },
  ]);

  const iconDisc =
    "inline-flex size-8 shrink-0 items-center justify-center rounded-full bg-foreground text-background transition-opacity hover:opacity-90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";
</script>

{#snippet navFooter()}
  <div
    class="mt-6 flex shrink-0 items-center justify-center gap-2.5 border-t border-border pt-4"
    role="group"
    aria-label={t("shell_nav_label")}
  >
    <NavLockToggle locked={fsm.presentation === "rail"} onclick={togglePin} />
    <a
      href="/profile/"
      aria-label={t("nav_profile")}
      title={t("nav_profile")}
      class={iconDisc}
    >
      <NavGlyph name="user" class="size-4" />
    </a>
    <button
      type="button"
      aria-label={t("theme_toggle_mode")}
      title={t("theme_toggle_mode")}
      class={iconDisc}
      onclick={toggleTheme}
    >
      <NavGlyph name={themeIcon} class="size-4" />
    </button>
  </div>
{/snippet}

{#snippet navBody()}
  <div class="flex h-full min-h-0 flex-col">
    <nav aria-label={t("shell_nav_label")} class="flex min-h-0 flex-1 flex-col gap-7 overflow-y-auto text-foreground">
      {#each sections as section (section.title)}
        <div class="flex flex-col gap-2.5">
          <div
            class="px-2 pb-1.5 text-[0.65rem] font-semibold uppercase tracking-[0.12em] text-muted-foreground"
          >
            {section.title}
          </div>
          {#each section.items as item (item.key)}
            <NavItem
              href={routes[item.key] ?? "#"}
              label={item.label}
              icon={item.icon}
              active={item.key === fsm.active}
              tone="default"
            />
          {/each}
        </div>
      {/each}
    </nav>
    {@render navFooter()}
  </div>
{/snippet}

{#snippet rail()}
  <aside
    class={cn(
      "flex min-h-0 shrink-0 flex-col overflow-y-auto border-border text-foreground",
      /* Soft wash + backdrop blur: melt dots read out of focus; labels stay sharp. */
      "bg-background/45 backdrop-blur-[0.35rem] supports-[backdrop-filter]:bg-background/35",
      side === "right" ? "order-last border-l" : "border-r",
    )}
    style={`width: ${NAV_WIDTH}`}
  >
    <div class="relative z-10 flex h-full min-h-0 flex-col px-3 pb-4 pt-20">
      {@render navBody()}
    </div>
  </aside>
{/snippet}

{#snippet drawer()}
  <FancyDrawer
    bind:open
    {side}
    width={NAV_WIDTH}
    title=""
    openLabel={t("shell_nav_label")}
    closeLabel={t("fancy_drawer_close")}
  >
    {@render navBody()}
  </FancyDrawer>
{/snippet}

{#if preference === "locked"}
  <!-- CSS picks rail vs drawer so SSR + navigation never flash unlocked. -->
  <div class="hidden min-[43.75rem]:contents">
    {@render rail()}
  </div>
  <div class="contents min-[43.75rem]:hidden">
    {@render drawer()}
  </div>
{:else}
  {@render drawer()}
{/if}
