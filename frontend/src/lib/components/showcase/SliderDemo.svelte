<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of form/Slider — Slider itself defaults to a safe
  mid-range value with a no-op onValueChange (adr-22 r1/r2), so this wrapper
  only supplies the local $state value and a numeric readout, the same reason
  showcase/PinInputDemo exists over its bare form component.
-->
<script lang="ts">
  import { Slider } from "$lib/components/form";
  import { t } from "../../../i18n";

  let value = $state(60);
</script>

<div class="flex max-w-sm flex-col gap-3">
  <Slider bind:value min={0} max={100} step={1} label={t("demo_slider_label")} />
  <span class="text-sm text-muted-foreground">{t("demo_slider_value")}: {value}%</span>
</div>
