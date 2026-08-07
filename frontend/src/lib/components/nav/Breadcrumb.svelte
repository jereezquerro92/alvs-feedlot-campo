<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Pill breadcrumb matching SessionBadge's chrome exactly ([[DESIGN-SYSTEM]]):
  same outer pill classes (`py-1 pl-1 pr-2`, `gap-2`, border, shadow) and a
  `size-8` home control matching the Avatar hitbox. Fill is
  `bg-foreground text-background` so light gets a black disc / light house and
  dark theme inverts. Pure navigation — links only, no fetch/mutate. Mounts
  with zero props and never throws ([[adr-22-showcase-ready-components]]
  rule 1). Copy via i18n ([[LOCALIZATION]]).
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
    "flex min-w-0 max-w-full items-center gap-2 rounded-full border border-border bg-card py-1 pl-1 pr-3 text-card-foreground shadow-sm",
    className,
  )}
>
  <a
    href={homeHref}
    aria-label={t("nav_home")}
    title={t("nav_home")}
    class="inline-flex size-8 shrink-0 items-center justify-center rounded-full bg-foreground text-background transition-opacity hover:opacity-90"
  >
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      class="size-4"
      aria-hidden="true"
    >
      <path d="M12 3.2 3 10.4V21a1 1 0 0 0 1 1h5.5v-6.5h5V22H20a1 1 0 0 0 1-1V10.4L12 3.2Z" />
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
