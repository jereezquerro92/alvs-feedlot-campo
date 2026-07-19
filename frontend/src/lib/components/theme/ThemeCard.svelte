<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[MELT-UI]]
     LIVE-DOC:END -->

<!--
  Rung 3 of the interactivity ladder (docs/bdds/bdd-06-profile-theming.md):
  five continuously-varying, client-owned controls that must repaint the
  page's CSS custom properties before any server round trip. Mode uses
  ThemeModeToggle ([[MELT-UI]]); bgPreset uses a second melt/builders
  control (RadioGroup) inline below — the same escape-hatch reasoning, a
  shipped shadcn-svelte toggle-group is not vendored in this template.
-->
<script lang="ts">
  import { RadioGroup } from "melt/builders";
  import { Card, CardHeader, CardTitle, CardContent } from "$lib/components/ui/card";
  import { Button } from "$lib/components/ui/button";
  import { Label } from "$lib/components/ui/label";
  import { Input } from "$lib/components/ui/input";
  import { Alert } from "$lib/components/ui/alert";
  import { cn } from "$lib/utils";
  import ThemeModeToggle from "$lib/components/theme/ThemeModeToggle.svelte";
  import { readCsrfTokenFromCookie } from "$lib/csrf";
  import {
    DEFAULTS,
    COLOR_KEYS,
    sanitizeColor,
    sanitizeRadius,
    sanitizeThemeConfig,
    applyTheme,
    writeThemeCookie,
    type ThemeConfig,
    type ThemeMode,
    type ThemeBgPreset,
    type ThemeColors,
  } from "$lib/theme";
  import type { Me } from "$lib/types/user";

  let {
    me = null,
    publicBackendUrl = "",
  }: {
    /** `null` is the zero-prop default (adr-22 rule 1): the card falls back to
     * DEFAULTS rather than a saved `theme_config`, and never throws. */
    me?: Me | null;
    publicBackendUrl?: string;
  } = $props();

  type ColorState = Record<keyof ThemeColors, string>;
  const BG_PRESETS: readonly ThemeBgPreset[] = ["default", "melt"];

  function colorsFromConfig(config: ThemeConfig | undefined): ColorState {
    return {
      background: config?.colors?.background ?? "",
      primary: config?.colors?.primary ?? "",
      secondary: config?.colors?.secondary ?? "",
      accent: config?.colors?.accent ?? "",
    };
  }

  function snapshotFromConfig(config: ThemeConfig | undefined) {
    return {
      mode: config?.mode ?? DEFAULTS.mode,
      bgPreset: config?.bgPreset ?? DEFAULTS.bgPreset,
      colors: colorsFromConfig(config),
      radius: config?.radius ?? "",
    };
  }

  // Last-confirmed state: seeded from `me.theme_config` (SSR-provided),
  // updated only after a successful Save. Reset reverts the draft to this.
  let saved = $state(snapshotFromConfig(me?.theme_config));

  let mode = $state<ThemeMode>(saved.mode);
  let bgPreset = $state<ThemeBgPreset>(saved.bgPreset);
  let colors = $state<ColorState>({ ...saved.colors });
  let radius = $state(saved.radius);

  let saving = $state(false);
  let error = $state("");
  let success = $state(false);

  const bgGroup = new RadioGroup({
    value: () => bgPreset,
    onValueChange: (value) => {
      bgPreset = value as ThemeBgPreset;
    },
    orientation: () => "horizontal",
  });

  function buildDraftBlob(): ThemeConfig {
    const blob: ThemeConfig = { mode, bgPreset };
    const sanitizedColors: ThemeColors = {};
    for (const key of COLOR_KEYS) {
      const safe = sanitizeColor(colors[key]);
      if (safe) sanitizedColors[key] = safe;
    }
    if (Object.keys(sanitizedColors).length > 0) blob.colors = sanitizedColors;
    const safeRadius = sanitizeRadius(radius);
    if (safeRadius) blob.radius = safeRadius;
    return blob;
  }

  const draftBlob = $derived.by(buildDraftBlob);

  // Live preview (bdd-06 "Live preview before save"): every control change
  // repaints the page immediately, client-local — no request fires here.
  $effect(() => {
    applyTheme(draftBlob);
  });

  function resetDraft(): void {
    mode = saved.mode;
    bgPreset = saved.bgPreset;
    colors = { ...saved.colors };
    radius = saved.radius;
    error = "";
    success = false;
  }

  /** `type="color"` needs a valid 6-digit hex at all times; this is a
   * display-only fallback swatch for an OKLCH/HSL/RGB or blank draft value —
   * it never overwrites the actual typed value in the paired text input. */
  function swatch(value: string): string {
    return /^#[0-9a-fA-F]{6}$/.test(value) ? value : "#888888";
  }

  async function save(): Promise<void> {
    saving = true;
    error = "";
    success = false;
    try {
      const res = await fetch(`${publicBackendUrl}/api/me/`, {
        method: "PATCH",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": readCsrfTokenFromCookie(),
        },
        body: JSON.stringify({ theme_config: draftBlob }),
      });
      if (!res.ok) {
        error = `Save failed (${res.status})`;
        return;
      }
      const data = (await res.json()) as Me;
      const confirmed = sanitizeThemeConfig(data.theme_config);
      saved = snapshotFromConfig(confirmed);
      // Cookie mirror fires only on this confirmed 200 (bdd-06's
      // error-handling clause) — never speculatively from the live-preview
      // effect above.
      writeThemeCookie(confirmed);
      success = true;
    } catch {
      error = "Save failed";
    } finally {
      saving = false;
    }
  }
</script>

<Card class="w-full max-w-md">
  <CardHeader>
    <CardTitle>Appearance</CardTitle>
  </CardHeader>
  <CardContent class="flex flex-col gap-6">
    <div class="flex items-center justify-between gap-4">
      <Label>Mode</Label>
      <ThemeModeToggle bind:mode disabled={saving} />
    </div>

    <div class="flex flex-col gap-2">
      <Label {...bgGroup.label}>Background preset</Label>
      <div {...bgGroup.root} class="inline-flex gap-2">
        {#each BG_PRESETS as preset (preset)}
          {@const item = bgGroup.getItem(preset)}
          <Button
            type="button"
            variant="bare"
            {...item.attrs}
            disabled={saving}
            class={cn(
              "rounded-md border px-3 py-1.5 text-sm capitalize",
              item.checked
                ? "border-primary bg-primary/10 text-foreground"
                : "border-input bg-background text-muted-foreground hover:bg-accent",
            )}
          >
            {preset}
          </Button>
        {/each}
      </div>
    </div>

    {#each COLOR_KEYS as key (key)}
      <div class="flex flex-col gap-1.5">
        <Label for={`theme-${key}`} class="capitalize">{key}</Label>
        <div class="flex items-center gap-2">
          <input
            type="color"
            aria-label={`Pick a ${key} color`}
            value={swatch(colors[key])}
            oninput={(e) => (colors[key] = (e.currentTarget as HTMLInputElement).value)}
            disabled={saving}
            class="h-9 w-10 shrink-0 cursor-pointer rounded-md border border-input bg-transparent p-1 disabled:cursor-not-allowed disabled:opacity-50"
          />
          <Input
            id={`theme-${key}`}
            placeholder="oklch(...) / #hex — blank uses the default"
            bind:value={colors[key]}
            disabled={saving}
          />
        </div>
      </div>
    {/each}

    <div class="flex flex-col gap-1.5">
      <Label for="theme-radius">Radius</Label>
      <Input id="theme-radius" placeholder="0.625rem" bind:value={radius} disabled={saving} />
    </div>

    {#if error}
      <Alert variant="destructive">{error}</Alert>
    {/if}
    {#if success}
      <Alert>Theme saved.</Alert>
    {/if}

    <div class="flex items-center justify-end gap-2">
      <Button type="button" variant="outline" onclick={resetDraft} disabled={saving}>Reset</Button>
      <Button type="button" onclick={save} disabled={saving}>{saving ? "Saving…" : "Save"}</Button>
    </div>
  </CardContent>
</Card>
