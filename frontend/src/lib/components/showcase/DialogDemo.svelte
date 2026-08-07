<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Gallery composition of overlay/Dialog — children is a Snippet Astro cannot
  pass through a slot, so the body lives here (same reason PopoverDemo exists).
-->
<script lang="ts">
  import { Dialog } from "$lib/components/overlay";
  import { t } from "../../../i18n";
</script>

<Dialog
  triggerLabel={t("demo_dialog_trigger")}
  title={t("demo_dialog_title")}
  description={t("demo_dialog_desc")}
>
  <p class="text-sm text-muted-foreground">{t("demo_dialog_body")}</p>
</Dialog>
