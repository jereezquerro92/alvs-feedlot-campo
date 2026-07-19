<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of form/RangeCalendar — RangeCalendar itself
  defaults to a safe current-month, nothing-selected view with a no-op
  onRangeChange (adr-22 r1/r2), so this wrapper supplies the local $state
  from/to, the formatted range readout, and the Clear affordance.
-->
<script lang="ts">
  import { RangeCalendar } from "$lib/components/form";
  import { Button } from "$lib/components/ui/button";
  import { t } from "../../../i18n";

  let from = $state<string | undefined>(undefined);
  let to = $state<string | undefined>(undefined);

  function clear(): void {
    from = undefined;
    to = undefined;
  }
</script>

<div class="flex flex-col gap-3">
  <RangeCalendar
    bind:from
    bind:to
    onRangeChange={(range) => {
      from = range.from;
      to = range.to;
    }}
  />
  <div class="flex items-center gap-3">
    <Button type="button" variant="outline" onclick={clear}>{t("demo_range_calendar_clear")}</Button>
    {#if from}
      <span class="text-sm text-muted-foreground">
        {t("demo_range_calendar_selected")}: {from}{#if to} – {to}{/if}
      </span>
    {/if}
  </div>
</div>
