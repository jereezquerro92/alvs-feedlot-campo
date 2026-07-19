<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of form/PinInput — PinInput itself defaults to a
  safe empty 6-digit state with a no-op onComplete (adr-22 r1/r2), so this
  wrapper supplies the local $state value, the onComplete confirmation
  message, and the Clear affordance, the same reason showcase/PaginationDemo
  exists: a second-factor confirm gate the gallery can show actually filling.
-->
<script lang="ts">
  import { PinInput } from "$lib/components/form";
  import { Button } from "$lib/components/ui/button";
  import { t } from "../../../i18n";

  let value = $state("");
  let confirmed = $state(false);

  function clear(): void {
    value = "";
    confirmed = false;
  }
</script>

<div class="flex flex-col gap-3">
  <PinInput bind:value onComplete={() => (confirmed = true)} label={t("demo_pin_input_label")} />
  <div class="flex items-center gap-3">
    <Button type="button" variant="outline" onclick={clear}>{t("demo_pin_input_clear")}</Button>
    {#if confirmed}
      <span class="text-sm text-muted-foreground">{t("demo_pin_input_confirmed")}</span>
    {/if}
  </div>
</div>
