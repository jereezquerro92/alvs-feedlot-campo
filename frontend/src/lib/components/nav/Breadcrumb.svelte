<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Pill breadcrumb matching SessionBadge's chrome exactly ([[DESIGN-SYSTEM]]):
  same outer pill classes (`py-1 pl-1 pr-2`, `gap-2`, border, shadow) and a
  `size-7` home control mirroring the avatar / hamburger hitbox. Pure
  navigation — links only, no fetch/mutate. Mounts with zero props and never
  throws ([[adr-22-showcase-ready-components]] rule 1). Copy via i18n
  ([[LOCALIZATION]]).
-->
<script lang="ts" module>
  export type BreadcrumbItem = {
    label: string;
    /** Omit on the current page (rendered as plain text, aria-current). */
    href?: string;
  };
</script>

<script lang="ts">
  import { t } from "../../../i18n";
  import { cn } from "$lib/utils";

  let {
    items = [],
    homeHref = "/feedlot/",
    class: className = undefined,
  }: {
    items?: BreadcrumbItem[];
    /** Destination for the leading home control. */
    homeHref?: string;
    class?: string;
  } = $props();
</script>

<nav
  aria-label={t("breadcrumb_nav")}
  class={cn(
    "flex min-w-0 max-w-full items-center gap-2 rounded-full border border-border bg-card py-1 pl-1 pr-2 text-card-foreground shadow-sm",
    className,
  )}
>
  <a
    href={homeHref}
    aria-label={t("nav_home")}
    title={t("nav_home")}
    class="inline-flex size-7 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
  >
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.75"
      stroke-linecap="round"
      stroke-linejoin="round"
      class="size-3.5"
      aria-hidden="true"
    >
      <path d="M3 21V10l9-6 9 6v11" />
      <path d="M9 21v-6h6v6" />
    </svg>
  </a>

  {#each items as item, i (i)}
    <span class="select-none text-sm font-medium text-muted-foreground/50" aria-hidden="true">/</span>
    {#if item.href}
      <a
        href={item.href}
        class="min-w-0 truncate text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
      >
        {item.label}
      </a>
    {:else}
      <span class="min-w-0 truncate text-sm font-medium" aria-current="page">
        {item.label}
      </span>
    {/if}
  {/each}
</nav>
