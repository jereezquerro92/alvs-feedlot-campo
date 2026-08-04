<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Gallery demo of overlay/FancyDrawer — the only live edge-docked pair in the
  showcase: one left + one right (collapsed by default). Do not also mount
  overlay/Drawer here; two pairs would share the same viewport edges.
-->
<script lang="ts">
  import { FancyDrawer } from "$lib/components/overlay";
  import { t } from "../../../i18n";
</script>

<p class="text-sm text-muted-foreground">{t("demo_fancy_drawer_note")}</p>

<FancyDrawer
  side="left"
  title={t("demo_fancy_drawer_left_title")}
  openLabel={t("fancy_drawer_open")}
  closeLabel={t("fancy_drawer_close")}
>
  <p>{t("demo_fancy_drawer_left_body")}</p>
</FancyDrawer>

<FancyDrawer
  side="right"
  title={t("demo_fancy_drawer_right_title")}
  openLabel={t("fancy_drawer_open")}
  closeLabel={t("fancy_drawer_close")}
>
  <p>{t("demo_fancy_drawer_right_body")}</p>
</FancyDrawer>
