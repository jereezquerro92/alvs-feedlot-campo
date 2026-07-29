<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  The topbar client selector ([[FEEDLOT]]): a real dropdown that switches the
  current-client context of the whole shell. It navigates — it never fetches or
  mutates. The destination is built from a `pattern` string (`{id}` placeholder)
  so the same switcher works on the dashboard (`/feedlot/{id}/`) and on a general
  module (`/feedlot/hacienda?client={id}`). Mounts with zero props and never throws
  ([[adr-22-showcase-ready-components]] rule 1). Colours are `--primary`/`--card`
  tokens under `.feedlot-app` ([[DESIGN-SYSTEM]]). Copy via i18n ([[LOCALIZATION]]).
-->
<script lang="ts">
  import { t } from "../../../i18n";

  type Client = { id: number | string; name?: string; kind?: string };

  let {
    clients = [],
    currentId = null,
    pattern = "/feedlot/{id}/",
    allLabel = "",
    allHref = "",
  }: {
    clients?: Client[];
    currentId?: number | string | null;
    /** URL template with a `{id}` placeholder the chosen client fills. */
    pattern?: string;
    /** Optional "all clients / feedlot completo" entry label. */
    allLabel?: string;
    /** Where the "all" entry points (empty → no "all" entry). */
    allHref?: string;
  } = $props();

  let open = $state(false);

  const KINDS: Record<string, string> = {
    boarding: t("feedlot_kind_boarding"),
    own: t("feedlot_kind_own"),
  };

  const current = $derived(
    clients.find((c) => String(c.id) === String(currentId)) ?? null,
  );
  const currentLabel = $derived(
    current?.name ?? (allHref ? allLabel : t("feedlot_topbar_switch")),
  );

  function hrefFor(id: number | string): string {
    return pattern.replace("{id}", String(id));
  }

  // Close on outside click / Escape so the menu never traps focus (adr-22).
  function onWindowClick(ev: MouseEvent) {
    if (!(ev.target as HTMLElement)?.closest?.("[data-client-switcher]")) open = false;
  }
  function onKey(ev: KeyboardEvent) {
    if (ev.key === "Escape") open = false;
  }
</script>

<svelte:window onclick={onWindowClick} onkeydown={onKey} />

<div class="relative" data-client-switcher>
  <button
    type="button"
    aria-haspopup="listbox"
    aria-expanded={open}
    onclick={() => (open = !open)}
    title={t("feedlot_topbar_switch")}
    class="inline-flex min-w-0 max-w-[15rem] items-center gap-2 rounded-full px-3 py-1.5 text-sm font-semibold transition-colors hover:bg-accent"
    style="border: var(--hairline) solid var(--border);"
  >
    <span class="size-2 shrink-0 rounded-full bg-primary" aria-hidden="true"></span>
    <span class="truncate">{currentLabel}</span>
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
      stroke-linecap="round" stroke-linejoin="round"
      class="size-3.5 shrink-0 text-muted-foreground transition-transform"
      style={open ? "transform: rotate(180deg);" : ""} aria-hidden="true">
      <path d="m6 9 6 6 6-6" />
    </svg>
  </button>

  {#if open}
    <ul
      role="listbox"
      class="absolute left-0 top-[calc(100%+0.4rem)] z-30 max-h-80 w-64 overflow-y-auto rounded-xl py-1.5 shadow-lg"
      style="background: var(--card); border: var(--hairline) solid var(--border);"
    >
      {#if allHref}
        <li>
          <a
            href={allHref}
            role="option"
            aria-selected={currentId === null || currentId === ""}
            class="flex items-center gap-2.5 px-3 py-2 text-sm hover:bg-accent"
          >
            <span class="grid size-6 place-items-center rounded-md text-[0.7rem] font-bold"
              style="background: var(--muted); color: var(--muted-foreground);">∑</span>
            <span class="flex-1 truncate font-medium">{allLabel}</span>
          </a>
        </li>
        <li class="my-1 h-px" style="background: var(--border);" aria-hidden="true"></li>
      {/if}

      {#each clients as c}
        {@const active = String(c.id) === String(currentId)}
        <li>
          <a
            href={hrefFor(c.id)}
            role="option"
            aria-selected={active}
            class="flex items-center gap-2.5 px-3 py-2 text-sm hover:bg-accent"
            style={active ? "background: var(--sidebar-active-bg);" : ""}
          >
            <span class="size-2 shrink-0 rounded-full" style={active ? "background: var(--primary);" : "background: var(--muted-foreground); opacity: .4;"} aria-hidden="true"></span>
            <span class="flex-1 truncate">{c.name ?? `#${c.id}`}</span>
            {#if c.kind}
              <span class="shrink-0 rounded-full px-1.5 py-0.5 text-[0.6rem] font-medium"
                style="background: color-mix(in oklab, var(--primary) 12%, transparent); color: var(--primary);">
                {KINDS[c.kind] ?? c.kind}
              </span>
            {/if}
          </a>
        </li>
      {/each}

      {#if clients.length === 0}
        <li class="px-3 py-2 text-sm text-muted-foreground">{t("feedlot_switcher_empty")}</li>
      {/if}
    </ul>
  {/if}
</div>
