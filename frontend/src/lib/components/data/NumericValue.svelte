<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts" module>
  /**
   * Formats a number for display, grouping by locale (dot-grouped under `es`)
   * with the sign kept adjacent to the digits. With `currency` set it renders
   * `"<currency> $<sign><grouped>"` (e.g. `"ARS $-32.950.952"`); without it,
   * just the signed grouped number (e.g. `"-32.950.952"`). Currency is a plain
   * label, not an `Intl` currency style, so any code renders uniformly.
   */
  export function formatNumber(
    value: number,
    currency: string | undefined = undefined,
    locale = "es",
    fractionDigits = 0,
  ): string {
    const sign = value < 0 ? "-" : "";
    const grouped = new Intl.NumberFormat(locale, {
      minimumFractionDigits: fractionDigits,
      maximumFractionDigits: fractionDigits,
    }).format(Math.abs(value));
    const prefix = currency ? `${currency} $` : "";
    return `${prefix}${sign}${grouped}`;
  }
</script>

<script lang="ts">
  import { cn } from "$lib/utils";
  import { defaultLocale } from "../../../i18n";

  let {
    value,
    currency = undefined,
    locale = defaultLocale,
    fractionDigits = 0,
    colored = true,
    class: className = undefined,
    ...rest
  }: {
    value: number;
    /** Optional currency label prefix; omit for a plain number. */
    currency?: string;
    locale?: string;
    fractionDigits?: number;
    /** Tint by sign: negative → `--negative`, positive → `--success`. */
    colored?: boolean;
    class?: string;
    [key: string]: unknown;
  } = $props();

  const text = $derived(formatNumber(value, currency, locale, fractionDigits));
  const tone = $derived(
    !colored ? "" : value < 0 ? "text-negative" : value > 0 ? "text-success" : "text-muted-foreground",
  );
</script>

<span class={cn("tabular-nums font-medium", tone, className)} {...rest}>{text}</span>
