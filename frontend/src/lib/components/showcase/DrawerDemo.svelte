<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of overlay/Drawer — the Drawer docks to the viewport,
  so this wrapper mounts one left and one right instance (both collapsed by
  default) and leaves an inline note pointing at the two edge tabs, the same
  composition-over-a-real-component pattern the other showcase/*Demo wrappers
  use (adr-22, COMPONENTIZATION).
-->
<script lang="ts">
  import { Drawer } from "$lib/components/overlay";
  import { t } from "../../../i18n";
</script>

<p class="text-sm text-muted-foreground">{t("demo_drawer_note")}</p>

<Drawer
  side="left"
  title={t("demo_drawer_left_title")}
  openLabel={t("drawer_open")}
  closeLabel={t("drawer_close")}
>
  <p>{t("demo_drawer_left_body")}</p>
</Drawer>

<Drawer
  side="right"
  title={t("demo_drawer_right_title")}
  openLabel={t("drawer_open")}
  closeLabel={t("drawer_close")}
>
  <p>{t("demo_drawer_right_body")}</p>
</Drawer>
