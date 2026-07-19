<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of form/ToggleGroup — ToggleGroup itself defaults to
  a safe two-option list/grid set with the first option selected and a no-op
  onValueChange (adr-22 r1/r2), so this wrapper only supplies a realistic
  three-option view-mode set and the local $state value, the same reason
  showcase/PinInputDemo exists over its bare form component.
-->
<script lang="ts">
  import { ToggleGroup, type ToggleGroupOption } from "$lib/components/form";
  import { t } from "../../../i18n";

  const options: ToggleGroupOption[] = [
    { value: "list", label: t("demo_toggle_group_option_list") },
    { value: "grid", label: t("demo_toggle_group_option_grid") },
    { value: "table", label: t("demo_toggle_group_option_table") },
  ];

  let value = $state(options[0].value);
</script>

<div class="flex flex-col gap-3">
  <ToggleGroup {options} bind:value label={t("demo_toggle_group_label")} />
  <span class="text-sm text-muted-foreground">{t("demo_toggle_group_selected")}: {value}</span>
</div>
