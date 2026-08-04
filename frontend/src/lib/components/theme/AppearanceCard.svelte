<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-53-api-membrane]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[COMPONENTIZATION]] · [[MELT-UI]]
     API: [[API]]
     LIVE-DOC:END -->

<!--
  /profile Appearance editor: closed theme packs, mode, bgPreset, sidebarSide,
  dual-mode PaletteFields, radius. Live preview via applyTheme; Save PATCHes
  theme_config. Refuses Save until both modes define canvas + dots.
-->
<script lang="ts">
  import { onMount } from "svelte";
  import { RadioGroup } from "melt/builders";
  import { Card, CardHeader, CardTitle, CardContent } from "$lib/components/ui/card";
  import { Button } from "$lib/components/ui/button";
  import { Label } from "$lib/components/ui/label";
  import { Input } from "$lib/components/ui/input";
  import { Alert } from "$lib/components/ui/alert";
  import { cn } from "$lib/utils";
  import PaletteFields from "./PaletteFields.svelte";
  import ThemeModeToggle from "./ThemeModeToggle.svelte";
  import { readCsrfTokenFromCookie } from "$lib/csrf";
  import {
    DEFAULTS,
    MODES,
    SIDEBAR_SIDES,
    sanitizeRadius,
    sanitizeThemeConfig,
    resolvePalette,
    applyTheme,
    writeThemeCookie,
    readThemeCookie,
    type ThemeConfig,
    type ThemeColors,
    type ThemeMode,
    type ThemeBgPreset,
    type SidebarSide,
  } from "$lib/theme";
  import {
    THEME_PACK_IDS,
    THEME_PACK_LABELS,
    themeConfigFromPack,
    type ThemePackId,
  } from "$lib/theme-packs";
  import { t } from "../../../i18n";
  import type { MessageKey } from "../../../i18n";
  import type { Me } from "$lib/types/user";

  let {
    me = null,
    publicBackendUrl = "",
  }: {
    me?: Me | null;
    publicBackendUrl?: string;
  } = $props();

  type Draft = {
    mode: ThemeMode;
    bgPreset: ThemeBgPreset;
    sidebarSide: SidebarSide;
    palettes: Record<ThemeMode, ThemeColors>;
    radius: string;
  };

  const BG_PRESETS: readonly ThemeBgPreset[] = ["default", "melt"];

  const BG_PRESET_LABELS: Record<ThemeBgPreset, MessageKey> = {
    default: "appearance_bg_default",
    melt: "appearance_bg_melt",
  };

  const SIDEBAR_SIDE_LABELS: Record<SidebarSide, MessageKey> = {
    left: "appearance_sidebar_left",
    right: "appearance_sidebar_right",
  };

  const MODE_LABELS: Record<ThemeMode, MessageKey> = {
    light: "appearance_mode_light",
    dark: "appearance_mode_dark",
  };

  function draftFrom(config: ThemeConfig | undefined): Draft {
    return {
      mode: config?.mode ?? DEFAULTS.mode,
      bgPreset: config?.bgPreset ?? DEFAULTS.bgPreset,
      sidebarSide: config?.sidebarSide ?? DEFAULTS.sidebarSide,
      palettes: {
        light: { ...(config?.colors?.light ?? {}) },
        dark: { ...(config?.colors?.dark ?? {}) },
      },
      radius: config?.radius ?? "",
    };
  }

  function blobFrom(source: Draft): ThemeConfig {
    const blob: ThemeConfig = {
      mode: source.mode,
      bgPreset: source.bgPreset,
      sidebarSide: source.sidebarSide,
    };

    const colors: NonNullable<ThemeConfig["colors"]> = {};
    for (const mode of MODES) {
      if (Object.keys(source.palettes[mode]).length > 0) colors[mode] = source.palettes[mode];
    }
    if (Object.keys(colors).length > 0) blob.colors = colors;

    const safeRadius = sanitizeRadius(source.radius);
    if (safeRadius) blob.radius = safeRadius;

    return sanitizeThemeConfig(blob);
  }

  const initialConfig = sanitizeThemeConfig(me?.theme_config);
  let saved = $state(draftFrom(initialConfig));
  let draft = $state(draftFrom(initialConfig));

  let lastApplied: string | null = null;
  let saving = $state(false);
  let error = $state("");
  let success = $state(false);

  onMount(() => {
    const cookieBlob = readThemeCookie();
    const seedSource =
      Object.keys(cookieBlob).length > 0 ? sanitizeThemeConfig(cookieBlob) : initialConfig;
    const seeded = draftFrom(seedSource);
    seeded.palettes.light = resolvePalette(seeded.palettes.light);
    seeded.palettes.dark = resolvePalette(seeded.palettes.dark);
    draft = seeded;
    saved = {
      ...seeded,
      palettes: {
        light: { ...seeded.palettes.light },
        dark: { ...seeded.palettes.dark },
      },
    };
  });

  const bgGroup = new RadioGroup({
    value: () => draft.bgPreset,
    onValueChange: (value) => {
      draft.bgPreset = value as ThemeBgPreset;
    },
    orientation: () => "horizontal",
  });

  const sideGroup = new RadioGroup({
    value: () => draft.sidebarSide,
    onValueChange: (value) => {
      draft.sidebarSide = value as SidebarSide;
    },
    orientation: () => "horizontal",
  });

  const draftBlob = $derived.by(() => blobFrom(draft));

  const canSave = $derived(
    Boolean(draft.palettes.light.canvas && draft.palettes.light.dots) &&
      Boolean(draft.palettes.dark.canvas && draft.palettes.dark.dots),
  );

  $effect(() => {
    const key = JSON.stringify(draftBlob);
    if (key === lastApplied) return;
    lastApplied = key;
    applyTheme(draftBlob);
  });

  function applyPack(id: ThemePackId): void {
    const next = themeConfigFromPack(id, blobFrom(draft));
    draft = draftFrom(next);
    error = "";
    success = false;
  }

  function resetDraft(): void {
    draft = {
      mode: saved.mode,
      bgPreset: saved.bgPreset,
      sidebarSide: saved.sidebarSide,
      palettes: {
        light: { ...saved.palettes.light },
        dark: { ...saved.palettes.dark },
      },
      radius: saved.radius,
    };
    error = "";
    success = false;
  }

  async function save(): Promise<void> {
    if (!canSave) {
      error = t("appearance_incomplete");
      return;
    }
    saving = true;
    error = "";
    success = false;
    const sideChanged = draft.sidebarSide !== saved.sidebarSide;
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
        error = t("appearance_save_failed").replace("{status}", String(res.status));
        return;
      }
      const data = (await res.json()) as Me;
      const confirmed = sanitizeThemeConfig(data.theme_config);
      saved = draftFrom(confirmed);
      draft = draftFrom(confirmed);
      writeThemeCookie(confirmed);
      success = true;
      if (sideChanged && typeof window !== "undefined") {
        window.location.reload();
      }
    } catch {
      error = t("appearance_save_failed_network");
    } finally {
      saving = false;
    }
  }
</script>

<Card class="w-full max-w-3xl">
  <CardHeader class="flex flex-row items-center justify-between gap-4">
    <CardTitle>{t("appearance_title")}</CardTitle>
    <ThemeModeToggle bind:mode={draft.mode} disabled={saving} />
  </CardHeader>
  <CardContent class="flex flex-col gap-6">
    <div class="flex flex-col gap-2">
      <Label>{t("appearance_packs")}</Label>
      <p class="text-sm text-muted-foreground">{t("appearance_packs_hint")}</p>
      <div class="flex flex-wrap gap-2">
        {#each THEME_PACK_IDS as packId (packId)}
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={saving}
            onclick={() => applyPack(packId)}
          >
            {t(THEME_PACK_LABELS[packId])}
          </Button>
        {/each}
      </div>
    </div>

    <div class="flex flex-col gap-2">
      <Label {...bgGroup.label}>{t("appearance_bg_preset")}</Label>
      <div {...bgGroup.root} class="inline-flex gap-2">
        {#each BG_PRESETS as preset (preset)}
          {@const item = bgGroup.getItem(preset)}
          <Button
            type="button"
            variant="bare"
            {...item.attrs}
            disabled={saving}
            class={cn(
              "rounded-md border px-3 py-1.5 text-sm",
              item.checked
                ? "border-primary bg-primary/10 text-foreground"
                : "border-input bg-background text-muted-foreground hover:bg-accent",
            )}
          >
            {t(BG_PRESET_LABELS[preset])}
          </Button>
        {/each}
      </div>
    </div>

    <div class="flex flex-col gap-2">
      <Label {...sideGroup.label}>{t("appearance_sidebar_side")}</Label>
      <div {...sideGroup.root} class="inline-flex gap-2">
        {#each SIDEBAR_SIDES as side (side)}
          {@const item = sideGroup.getItem(side)}
          <Button
            type="button"
            variant="bare"
            {...item.attrs}
            disabled={saving}
            class={cn(
              "rounded-md border px-3 py-1.5 text-sm",
              item.checked
                ? "border-primary bg-primary/10 text-foreground"
                : "border-input bg-background text-muted-foreground hover:bg-accent",
            )}
          >
            {t(SIDEBAR_SIDE_LABELS[side])}
          </Button>
        {/each}
      </div>
    </div>

    <div class="grid gap-6 md:grid-cols-2">
      {#each MODES as mode (mode)}
        <div class="flex flex-col gap-3 rounded-md border border-border p-3">
          <h3 class="text-sm font-semibold">{t(MODE_LABELS[mode])}</h3>
          <PaletteFields
            bind:palette={draft.palettes[mode]}
            disabled={saving}
            idPrefix={`appearance-${mode}`}
          />
        </div>
      {/each}
    </div>

    <div class="flex flex-col gap-1.5">
      <Label for="theme-radius">{t("appearance_radius")}</Label>
      <Input
        id="theme-radius"
        placeholder="0.625rem"
        bind:value={draft.radius}
        disabled={saving}
      />
    </div>

    {#if error}
      <Alert variant="destructive">{error}</Alert>
    {/if}
    {#if success}
      <Alert>{t("appearance_saved")}</Alert>
    {/if}

    <div class="flex items-center justify-end gap-2">
      <Button type="button" variant="outline" onclick={resetDraft} disabled={saving}>
        {t("appearance_reset")}
      </Button>
      <Button type="button" onclick={save} disabled={saving || !canSave}>
        {saving ? t("appearance_saving") : t("appearance_save")}
      </Button>
    </div>
  </CardContent>
</Card>
