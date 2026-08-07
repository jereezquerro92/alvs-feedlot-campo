<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Gallery composition of feedback/Progress — Progress itself defaults to an
  empty bar (adr-22); this wrapper supplies a mid-range sample value + label.
-->
<script lang="ts">
  import { Progress } from "$lib/components/feedback";
  import { t } from "../../../i18n";
</script>

<Progress value={62} max={100} label={t("demo_progress_label")} />
