<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-13-m365-graph]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  The Microsoft Graph integration status strip ([[adr-13-m365-graph]] rule 3):
  the two words `GET /api/m365/hello/` and `GET /api/m365/world/` return from the
  SharePoint workbook, shown side by side so a broken app-only token is visible
  at a glance instead of silently degrading. Pure presentation — the words are
  fetched server-side by the page and arrive as props, so nothing is requested on
  mount and no token is ever touched here ([[adr-13-m365-graph]] rule 2). Mounts with zero props,
  rendering its own em-dash placeholder per slot, and never throws
  ([[adr-22-showcase-ready-components]] rules 1–2). Colour is `.feedlot-app`
  tokens ([[DESIGN-SYSTEM]]); copy via i18n ([[LOCALIZATION]]).
-->
<script lang="ts">
  import { t } from "../../../i18n";

  let {
    /** Body of `GET /api/m365/hello/`, or the page's error-code fallback. */
    hello = "",
    /** Body of `GET /api/m365/world/`, or the page's error-code fallback. */
    world = "",
  }: {
    hello?: string;
    world?: string;
  } = $props();

  // A word slot is either a value or the placeholder — never an empty node, so
  // the card reads the same whether the page fetched, failed, or passed nothing.
  const words = $derived([hello, world].map((w) => (w ?? "").trim() || "—"));
</script>

<section
  class="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-2xl px-5 py-3.5"
  style="background: var(--card); border: var(--hairline) solid var(--border);"
  aria-label={t("m365_status")}
>
  <div class="flex items-center gap-2">
    <span class="grid size-7 place-items-center rounded-lg" aria-hidden="true"
      style="background: color-mix(in oklch, var(--primary) 12%, transparent); color: var(--primary);">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"
        stroke-linecap="round" stroke-linejoin="round" class="size-4">
        <rect x="3" y="3" width="8" height="8" rx="1" /><rect x="13" y="3" width="8" height="8" rx="1" />
        <rect x="3" y="13" width="8" height="8" rx="1" /><rect x="13" y="13" width="8" height="8" rx="1" />
      </svg>
    </span>
    <span class="text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
      {t("m365_status")}
    </span>
  </div>

  <div class="flex items-center gap-2">
    {#each words as word}
      <span
        data-testid="m365-word"
        class="rounded-lg px-2.5 py-1 font-mono text-sm"
        style="background: var(--muted); color: var(--foreground);"
      >{word}</span>
    {/each}
  </div>
</section>
