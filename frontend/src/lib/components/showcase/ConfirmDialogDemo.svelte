<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Gallery composition of overlay/ConfirmDialog — onconfirm defaults to a
  no-op in the component; this demo only supplies labeled sample copy.
-->
<script lang="ts">
  import { ConfirmDialog } from "$lib/components/overlay";
  import { t } from "../../../i18n";
</script>

<ConfirmDialog
  title={t("demo_confirm_dialog_title")}
  description={t("demo_confirm_dialog_desc")}
  confirmLabel={t("demo_confirm_dialog_confirm")}
  cancelLabel={t("demo_confirm_dialog_cancel")}
  triggerLabel={t("demo_confirm_dialog_trigger")}
  onconfirm={() => {}}
/>
