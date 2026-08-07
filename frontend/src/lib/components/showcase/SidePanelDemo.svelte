<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Gallery composition of overlay/SidePanel — one left and one right instance
  (both collapsed by default). Contained in a clipped relative box so the
  panels do not steal the live viewport edges owned by FancyDrawerDemo.
  `[&_aside]:!absolute` strips the component's own `position: fixed`.
-->
<script lang="ts">
  import { SidePanel } from "$lib/components/overlay";
  import { t } from "../../../i18n";
</script>

<p class="text-sm text-muted-foreground">{t("demo_side_panel_note")}</p>
<div
  class="relative h-48 w-full overflow-hidden rounded-md border border-border [&_aside]:!absolute [&_aside]:!inset-y-0"
>
  <SidePanel
    side="left"
    title={t("demo_side_panel_left_title")}
    openLabel={t("side_panel_open")}
    closeLabel={t("side_panel_close")}
  >
    <p>{t("demo_side_panel_left_body")}</p>
  </SidePanel>

  <SidePanel
    side="right"
    title={t("demo_side_panel_right_title")}
    openLabel={t("side_panel_open")}
    closeLabel={t("side_panel_close")}
  >
    <p>{t("demo_side_panel_right_body")}</p>
  </SidePanel>
</div>
