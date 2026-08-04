<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Seven color controls of ONE palette — canvas, dots, surface, foreground,
  primary, secondary, accent. AppearanceCard mounts it once per mode.
-->
<script lang="ts">
  import { Label } from "$lib/components/ui/label";
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { COLOR_KEYS, type ThemeColors } from "$lib/theme";
  import { t } from "../../../i18n";
  import type { MessageKey } from "../../../i18n";

  let {
    palette = $bindable<ThemeColors>({}),
    disabled = false,
    idPrefix = "palette",
  }: {
    palette?: ThemeColors;
    disabled?: boolean;
    idPrefix?: string;
  } = $props();

  const COLOR_LABELS: Record<keyof ThemeColors, MessageKey> = {
    canvas: "appearance_color_canvas",
    dots: "appearance_color_dots",
    surface: "appearance_color_surface",
    foreground: "appearance_color_foreground",
    primary: "appearance_color_primary",
    secondary: "appearance_color_secondary",
    accent: "appearance_color_accent",
  };

  /** `type="color"` needs a 6-digit hex; OKLCH/blank drafts get the token
   * `--swatch-fallback`, which never overwrites the typed value. */
  function swatch(value: string | undefined): string {
    const v = value ?? "";
    if (/^#[0-9a-fA-F]{6}$/.test(v)) return v;
    if (/^#[0-9a-fA-F]{8}$/.test(v)) return v.slice(0, 7);
    if (typeof document === "undefined") return "#888888";
    const raw = getComputedStyle(document.documentElement)
      .getPropertyValue("--swatch-fallback")
      .trim();
    return /^#[0-9a-fA-F]{6}$/.test(raw) ? raw : "#888888";
  }

  function setKey(key: keyof ThemeColors, value: string): void {
    palette = { ...palette, [key]: value };
  }

  function clearKey(key: keyof ThemeColors): void {
    const next = { ...palette };
    delete next[key];
    palette = next;
  }
</script>

<div class="flex flex-col gap-3">
  {#each COLOR_KEYS as key (key)}
    <div class="flex flex-col gap-1.5">
      <Label for={`${idPrefix}-${key}`}>{t(COLOR_LABELS[key])}</Label>
      <div class="flex items-center gap-2">
        <input
          type="color"
          aria-label={t(COLOR_LABELS[key])}
          value={swatch(palette[key])}
          oninput={(e) => setKey(key, (e.currentTarget as HTMLInputElement).value)}
          {disabled}
          class="h-9 w-10 shrink-0 cursor-pointer rounded-md border border-input bg-transparent p-1 disabled:cursor-not-allowed disabled:opacity-50"
        />
        <Input
          id={`${idPrefix}-${key}`}
          placeholder="oklch(...) / #hex"
          value={palette[key] ?? ""}
          oninput={(e) => setKey(key, (e.currentTarget as HTMLInputElement).value)}
          {disabled}
        />
        <Button
          type="button"
          variant="outline"
          size="sm"
          onclick={() => clearKey(key)}
          {disabled}
          aria-label={t("appearance_color_clear")}
        >
          ×
        </Button>
      </div>
    </div>
  {/each}
</div>
