<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  The feedlot app's dark-green left navigation ([[FEEDLOT]]). Pure presentation:
  it renders the nav sections and highlights the active one; it never fetches or
  mutates. Colours come entirely from the `--sidebar-*` tokens defined under
  `.feedlot-app` ([[DESIGN-SYSTEM]] variable-driven theming) — no hardcoded hex.
  Mounts with zero props (renders with dead `#` links, nothing active) and never
  throws ([[adr-22-showcase-ready-components]] rule 1). Copy via i18n ([[LOCALIZATION]]).
-->
<script lang="ts">
  import { t } from "../../../i18n";

  let {
    clientId = null,
    active = "dashboard",
  }: {
    /** The client carried as `?client=` into each general module (context, not a
     *  URL segment): the redesign is module-first — you enter a module, then the
     *  module acts on the selected client ([[FEEDLOT]]). */
    clientId?: number | string | null;
    /** Which nav key is highlighted. */
    active?: string;
  } = $props();

  // Module-first routing: every operational link goes to a GENERAL module, not a
  // per-client page. The current client rides along as `?client=` so the module
  // preselects it; the dashboard is the one page that stays keyed by client id.
  // Never throws on a null id (adr-22).
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

  type Item = { key: string; label: string; icon: string; badge?: string };
  const sections = $derived([
    {
      title: t("feedlot_nav_section_operation"),
      items: [
        { key: "dashboard", label: t("feedlot_nav_dashboard"), icon: "grid" },
        { key: "intake", label: t("feedlot_nav_intake"), icon: "cow" },
        { key: "feeding", label: t("feedlot_nav_feeding"), icon: "wheat" },
        { key: "sanitary", label: t("feedlot_nav_sanitary"), icon: "shield" },
        { key: "pesajes", label: t("feedlot_nav_pesajes"), icon: "scale" },
      ] as Item[],
    },
    {
      title: t("feedlot_nav_section_nutrition"),
      items: [
        { key: "mixer", label: t("feedlot_nav_mixer"), icon: "truck" },
        { key: "racion", label: t("feedlot_nav_racion"), icon: "blend" },
        { key: "stocks", label: t("feedlot_nav_stocks"), icon: "box" },
      ] as Item[],
    },
    {
      title: t("feedlot_nav_section_admin"),
      items: [
        { key: "ledger", label: t("feedlot_nav_ledger"), icon: "receipt" },
        { key: "gastos", label: t("feedlot_nav_gastos"), icon: "coins" },
        { key: "clients", label: t("feedlot_nav_clients"), icon: "users" },
        { key: "advisors", label: t("feedlot_nav_advisors"), icon: "spark" },
        { key: "users", label: t("feedlot_nav_users"), icon: "key" },
      ] as Item[],
    },
    {
      title: t("feedlot_nav_section_reference"),
      items: [{ key: "prices", label: t("feedlot_nav_prices"), icon: "tag" }] as Item[],
    },
  ]);
</script>

{#snippet icon(name: string)}
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"
    stroke-linecap="round" stroke-linejoin="round" class="size-[1.05rem] shrink-0" aria-hidden="true">
    {#if name === "grid"}
      <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
    {:else if name === "wheat"}
      <path d="M12 22V8" /><path d="M12 8c0-2 1.5-3 3-3 0 2-1.5 3-3 3Z" /><path d="M12 8c0-2-1.5-3-3-3 0 2 1.5 3 3 3Z" /><path d="M12 13c0-2 1.5-3 3-3 0 2-1.5 3-3 3Z" /><path d="M12 13c0-2-1.5-3-3-3 0 2 1.5 3 3 3Z" />
    {:else if name === "cow"}
      <path d="M5 8c-1.5 0-2-1.5-2-2.5S4 4 5 5" /><path d="M19 8c1.5 0 2-1.5 2-2.5S20 4 19 5" /><path d="M5 8v3a7 7 0 0 0 14 0V8" /><path d="M9 15h6" /><circle cx="9.5" cy="11" r=".6" fill="currentColor" /><circle cx="14.5" cy="11" r=".6" fill="currentColor" />
    {:else if name === "shield"}
      <path d="M12 3 5 6v5c0 4 3 7 7 8 4-1 7-4 7-8V6Z" /><path d="m9 12 2 2 4-4" />
    {:else if name === "wrench"}
      <path d="M14.5 6a3.5 3.5 0 0 0-4.9 4.4L3 17v4h4l6.6-6.6A3.5 3.5 0 0 0 18 9.5" />
    {:else if name === "scale"}
      <path d="M12 3v18" /><path d="M7 21h10" /><path d="M5 7h14" /><path d="M5 7 2 13a3 3 0 0 0 6 0Z" /><path d="M19 7l-3 6a3 3 0 0 0 6 0Z" />
    {:else if name === "truck"}
      <path d="M3 6h11v9H3Z" /><path d="M14 9h4l3 3v3h-7Z" /><circle cx="7" cy="17.5" r="1.6" /><circle cx="17" cy="17.5" r="1.6" />
    {:else if name === "blend"}
      <circle cx="9" cy="9" r="6" /><circle cx="15" cy="15" r="6" />
    {:else if name === "box"}
      <path d="M3 8 12 3l9 5v8l-9 5-9-5Z" /><path d="M3 8l9 5 9-5" /><path d="M12 13v8" />
    {:else if name === "coins"}
      <ellipse cx="8" cy="6" rx="5" ry="2.5" /><path d="M3 6v5c0 1.4 2.2 2.5 5 2.5s5-1.1 5-2.5V6" /><path d="M11 15.5c0 1.4 2.2 2.5 5 2.5s5-1.1 5-2.5v-5c0-1.4-2.2-2.5-5-2.5" />
    {:else if name === "receipt"}
      <path d="M5 3v18l2-1 2 1 2-1 2 1 2-1 2 1V3l-2 1-2-1-2 1-2-1-2 1Z" /><path d="M9 8h6M9 12h6" />
    {:else if name === "users"}
      <circle cx="9" cy="8" r="3" /><path d="M3 20c0-3 3-5 6-5s6 2 6 5" /><path d="M16 6a3 3 0 0 1 0 6M21 20c0-2-1-3.5-3-4.3" />
    {:else if name === "spark"}
      <path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2 2M16 16l2 2M18 6l-2 2M8 16l-2 2" /><circle cx="12" cy="12" r="2.4" />
    {:else if name === "key"}
      <circle cx="8" cy="15" r="3.5" /><path d="m10.5 12.5 8-8M15 5l2 2M18 8l2-2" />
    {:else if name === "tag"}
      <path d="M3 12V4h8l9 9-8 8Z" /><circle cx="7.5" cy="7.5" r="1.3" />
    {/if}
  </svg>
{/snippet}

<aside
  class="hidden w-60 shrink-0 flex-col lg:flex"
  style="background: var(--sidebar); color: var(--sidebar-foreground); border-right: var(--hairline) solid var(--sidebar-border);"
>
  <!-- Brand -->
  <div class="flex items-center gap-3 px-5 py-5" style="border-bottom: var(--hairline) solid var(--sidebar-border);">
    <span
      class="grid size-9 place-items-center rounded-xl text-lg font-black"
      style="background: var(--sidebar-logo-bg); color: var(--sidebar-logo-foreground);"
    >A</span>
    <div class="leading-tight">
      <div class="text-sm font-bold tracking-wide">ALVS</div>
      <div class="text-xs" style="color: var(--sidebar-muted);">{t("feedlot_brand_subtitle")}</div>
    </div>
  </div>

  <nav class="flex flex-1 flex-col gap-6 overflow-y-auto px-3 py-5">
    {#each sections as section}
      <div class="flex flex-col gap-1">
        <div class="px-3 pb-1 text-[0.65rem] font-semibold uppercase tracking-[0.12em]" style="color: var(--sidebar-muted);">
          {section.title}
        </div>
        {#each section.items as item}
          {@const isActive = item.key === active}
          <a
            href={routes[item.key] ?? "#"}
            aria-current={isActive ? "page" : undefined}
            class="feedlot-nav-item group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors"
            style={isActive
              ? "background: var(--sidebar-active-bg); color: var(--sidebar-active-foreground);"
              : "color: var(--sidebar-foreground);"}
          >
            {@render icon(item.icon)}
            <span class="flex-1 truncate">{item.label}</span>
            {#if item.badge}
              <span
                class="rounded-full px-2 py-0.5 text-[0.6rem] font-bold uppercase tracking-wide"
                style="background: var(--sidebar-logo-bg); color: var(--sidebar-logo-foreground);"
              >{item.badge}</span>
            {/if}
          </a>
        {/each}
      </div>
    {/each}
  </nav>
</aside>

<style>
  /* Hover tint for non-active items — token-driven, both themes. */
  .feedlot-nav-item:not([aria-current="page"]):hover {
    background: var(--sidebar-hover-bg);
  }
</style>
