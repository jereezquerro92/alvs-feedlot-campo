<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Feedlot site menu: unlocked = floating FancyDrawer; locked (closed padlock) =
  permanent left rail (no fill — page canvas shows through). Footer holds
  lock / profile / theme icon discs, separated below the menu. Floating mode
  opens from FancyDrawer's edge tab. Mounts with zero props (adr-22 r1). Pin
  preference persists in localStorage.
-->
<script lang="ts">
  import { onMount } from "svelte";
  import FancyDrawer from "$lib/components/overlay/FancyDrawer.svelte";
  import NavItem from "$lib/components/shell/NavItem.svelte";
  import NavLockToggle from "$lib/components/shell/NavLockToggle.svelte";
  import NavGlyph from "$lib/components/shell/NavGlyph.svelte";
  import type { NavIconName } from "$lib/components/shell/nav";
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

  const PIN_KEY = "feedlot-nav-pinned";
  const NAV_WIDTH = "12rem";

  let {
    clientId = null,
    active = "dashboard",
    open = $bindable(false),
    /** Mobile overlay when the rail is pinned. */
    mobileOpen = $bindable(false),
    /** Pin preference; Shell binds it. */
    pinned = $bindable(false),
    /** Dock edge from theme_config.sidebarSide ([[DESIGN-SYSTEM]]). */
    side = "left" as SidebarSide,
  }: {
    clientId?: number | string | null;
    active?: string;
    open?: boolean;
    mobileOpen?: boolean;
    pinned?: boolean;
    side?: SidebarSide;
  } = $props();

  let mode = $state<ThemeMode>(DEFAULTS.mode);

  onMount(() => {
    mode = readThemeCookie().mode ?? DEFAULTS.mode;
    try {
      pinned = localStorage.getItem(PIN_KEY) === "1";
    } catch {
      /* private mode / denied */
    }
  });

  function persistPin(next: boolean) {
    pinned = next;
    try {
      localStorage.setItem(PIN_KEY, next ? "1" : "0");
    } catch {
      /* ignore */
    }
    if (next) {
      open = true;
      mobileOpen = false;
    } else {
      mobileOpen = false;
    }
  }

  function togglePin() {
    persistPin(!pinned);
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
    <NavLockToggle locked={pinned} onclick={togglePin} />
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
        <div class="flex flex-col gap-1.5">
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
              active={item.key === active}
              tone="default"
            />
          {/each}
        </div>
      {/each}
    </nav>
    {@render navFooter()}
  </div>
{/snippet}

{#if pinned}
  <!-- Desktop: permanent in-flow rail — no aside fill; canvas shows through. -->
  <aside
    class={cn(
      "hidden min-h-0 shrink-0 flex-col overflow-y-auto border-border text-foreground lg:flex",
      side === "right" ? "order-last border-l" : "border-r",
    )}
    style={`width: ${NAV_WIDTH}`}
  >
    <div class="flex h-full min-h-0 flex-col px-3 py-4">
      {@render navBody()}
    </div>
  </aside>

  {#if mobileOpen}
    <button
      type="button"
      class="fixed inset-0 z-40 bg-foreground/40 lg:hidden"
      aria-label={t("shell_nav_dismiss_overlay")}
      onclick={() => (mobileOpen = false)}
    ></button>
    <aside
      class={cn(
        "fixed inset-y-0 z-50 flex flex-col overflow-y-auto border-border text-foreground shadow-xl lg:hidden",
        side === "right" ? "right-0 border-l" : "left-0 border-r",
      )}
      style={`width: ${NAV_WIDTH}`}
    >
      <div class="flex h-full min-h-0 flex-col px-3 py-4">
        {@render navBody()}
      </div>
    </aside>
  {/if}
{:else}
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
{/if}
