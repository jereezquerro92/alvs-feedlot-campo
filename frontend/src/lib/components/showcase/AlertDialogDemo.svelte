<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Gallery composition of the raw ui/alert-dialog primitives — ConfirmDialog
  wraps the same atoms for app use; this demo shows the compound parts
  composed bare, with a no-op Action (adr-22 r2: default invocation mutates
  nothing).
-->
<script lang="ts">
  import * as AlertDialog from "$lib/components/ui/alert-dialog";
  import { Button } from "$lib/components/ui/button";
  import { t } from "../../../i18n";
</script>

<AlertDialog.Root>
  <AlertDialog.Trigger>
    <Button type="button" variant="outline">{t("demo_alert_dialog_trigger")}</Button>
  </AlertDialog.Trigger>
  <AlertDialog.Content>
    <AlertDialog.Header>
      <AlertDialog.Title>{t("demo_alert_dialog_title")}</AlertDialog.Title>
      <AlertDialog.Description>{t("demo_alert_dialog_desc")}</AlertDialog.Description>
    </AlertDialog.Header>
    <AlertDialog.Footer>
      <AlertDialog.Cancel>{t("demo_alert_dialog_cancel")}</AlertDialog.Cancel>
      <AlertDialog.Action>{t("demo_alert_dialog_confirm")}</AlertDialog.Action>
    </AlertDialog.Footer>
  </AlertDialog.Content>
</AlertDialog.Root>
