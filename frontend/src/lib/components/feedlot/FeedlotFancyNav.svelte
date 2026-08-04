<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[COMPONENTIZATION]]
     LIVE-DOC:END -->

<!--
  Feedlot site menu: unlocked = floating FancyDrawer; locked (closed padlock) =
  permanent left rail with primary (feedlot green) fill — the old sidebar
  presence. Lock + "Menú" stays on top either way so the user can free it.
  Mobile locked mode uses a sandwich toggle over an edge overlay. Mounts with
  zero props (adr-22 r1). Pin preference persists in localStorage.
-->
<script lang="ts">
  import { onMount } from "svelte";
  import FancyDrawer from "$lib/components/overlay/FancyDrawer.svelte";
  import NavItem from "$lib/components/shell/NavItem.svelte";
  import NavLockToggle from "$lib/components/shell/NavLockToggle.svelte";
  import type { NavIconName } from "$lib/components/shell/nav";
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";

  const PIN_KEY = "feedlot-nav-pinned";
  const NAV_WIDTH = "12rem";

  let {
    clientId = null,
    active = "dashboard",
    open = $bindable(false),
  }: {
    clientId?: number | string | null;
    active?: string;
    open?: boolean;
  } = $props();

  let pinned = $state(false);
  let mobileOpen = $state(false);

  onMount(() => {
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

  function toggleMobile() {
    mobileOpen = !mobileOpen;
  }

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

  const itemTone = $derived(pinned ? ("inverse" as const) : ("default" as const));
</script>

{#snippet navBody()}
  <div class="flex flex-col gap-3">
    <NavLockToggle locked={pinned} onclick={togglePin} />
    <nav
      aria-label={t("shell_nav_label")}
      class={cn("flex flex-col gap-4", pinned ? "text-primary-foreground" : "text-foreground")}
    >
      {#each sections as section (section.title)}
        <div class="flex flex-col gap-0.5">
          <div
            class={cn(
              "px-2 pb-1 text-[0.65rem] font-semibold uppercase tracking-[0.12em]",
              pinned ? "text-primary-foreground/65" : "text-muted-foreground",
            )}
          >
            {section.title}
          </div>
          {#each section.items as item (item.key)}
            <NavItem
              href={routes[item.key] ?? "#"}
              label={item.label}
              icon={item.icon}
              active={item.key === active}
              tone={itemTone}
            />
          {/each}
        </div>
      {/each}
    </nav>
  </div>
{/snippet}

{#if pinned}
  <!-- Desktop: permanent in-flow rail (old green presence via --primary). -->
  <aside
    class="hidden shrink-0 flex-col overflow-y-auto border-r border-primary/30 bg-primary text-primary-foreground lg:flex"
    style={`width: ${NAV_WIDTH}`}
  >
    <div class="flex flex-col gap-0 px-3 py-4">
      {@render navBody()}
    </div>
  </aside>

  <!-- Mobile sandwich: opens edge overlay when locked. -->
  <button
    type="button"
    class="fixed left-3 top-3 z-50 inline-flex size-10 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-md lg:hidden"
    aria-label={t("shell_nav_sandwich_aria")}
    aria-expanded={mobileOpen}
    onclick={toggleMobile}
  >
    <span aria-hidden="true" class="text-lg leading-none">{mobileOpen ? "✕" : "☰"}</span>
  </button>

  {#if mobileOpen}
    <button
      type="button"
      class="fixed inset-0 z-40 bg-foreground/40 lg:hidden"
      aria-label={t("shell_nav_dismiss_overlay")}
      onclick={() => (mobileOpen = false)}
    ></button>
    <aside
      class="fixed inset-y-0 left-0 z-50 flex flex-col overflow-y-auto border-r border-primary/30 bg-primary text-primary-foreground shadow-xl lg:hidden"
      style={`width: ${NAV_WIDTH}`}
    >
      <div class="flex flex-col gap-0 px-3 py-4">
        {@render navBody()}
      </div>
    </aside>
  {/if}
{:else}
  <FancyDrawer
    bind:open
    side="left"
    width={NAV_WIDTH}
    title=""
    openLabel={t("shell_nav_label")}
    closeLabel={t("fancy_drawer_close")}
  >
    {@render navBody()}
  </FancyDrawer>
{/if}
