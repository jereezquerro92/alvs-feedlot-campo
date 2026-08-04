<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Gallery note for overlay/Drawer — does NOT mount live edge instances.
  Only one left and one right docked panel may own the viewport edges in the
  gallery; that role belongs to FancyDrawerDemo. A second pair would stack
  tabs on the same edges and fight for hover/dismiss.
-->
<script lang="ts">
  import { t } from "../../../i18n";
</script>

<p class="text-sm text-muted-foreground">{t("demo_drawer_note")}</p>
