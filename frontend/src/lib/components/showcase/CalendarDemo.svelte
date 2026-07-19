<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of form/Calendar — Calendar itself defaults to a
  safe current-month, nothing-selected view with a no-op onValueChange
  (adr-22 r1/r2), so this wrapper supplies the local $state value, the
  formatted selection readout, and the Clear affordance.
-->
<script lang="ts">
  import { Calendar } from "$lib/components/form";
  import { Button } from "$lib/components/ui/button";
  import { t } from "../../../i18n";

  let value = $state<string | undefined>(undefined);

  function clear(): void {
    value = undefined;
  }
</script>

<div class="flex flex-col gap-3">
  <Calendar bind:value onValueChange={(v) => (value = v)} />
  <div class="flex items-center gap-3">
    <Button type="button" variant="outline" onclick={clear}>{t("demo_calendar_clear")}</Button>
    {#if value}
      <span class="text-sm text-muted-foreground">{t("demo_calendar_selected")}: {value}</span>
    {/if}
  </div>
</div>
