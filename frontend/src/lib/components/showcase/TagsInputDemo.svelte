<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of form/TagsInput — TagsInput itself defaults to a
  safe empty tag list with a no-op onTagsChange (adr-22 r1/r2), so this
  wrapper supplies a starter sample and the Clear affordance, the same reason
  showcase/PinInputDemo exists: a gallery slice the demo can show actually
  filling.
-->
<script lang="ts">
  import { TagsInput } from "$lib/components/form";
  import { Button } from "$lib/components/ui/button";
  import { t } from "../../../i18n";

  let tags = $state(["acme", "nimbus"]);

  function clear(): void {
    tags = [];
  }
</script>

<div class="flex flex-col gap-3">
  <TagsInput bind:tags label={t("demo_tags_input_label")} />
  <div class="flex items-center gap-3">
    <Button type="button" variant="outline" onclick={clear}>{t("demo_tags_input_clear")}</Button>
  </div>
</div>
