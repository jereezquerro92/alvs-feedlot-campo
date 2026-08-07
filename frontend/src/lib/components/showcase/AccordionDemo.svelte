<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Gallery composition of overlay/Accordion — supplies realistic sample items
  so the .astro route does not author demo data inline.
-->
<script lang="ts">
  import { Accordion } from "$lib/components/overlay";
  import { t } from "../../../i18n";

  const items = [
    {
      id: "settlement",
      title: t("demo_accordion_settlement_title"),
      content: t("demo_accordion_settlement_body"),
    },
    {
      id: "audit",
      title: t("demo_accordion_audit_title"),
      content: t("demo_accordion_audit_body"),
    },
    {
      id: "contact",
      title: t("demo_accordion_contact_title"),
      content: t("demo_accordion_contact_body"),
    },
  ];
</script>

<Accordion {items} />
