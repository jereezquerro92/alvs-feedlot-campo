<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Chip-entry field for multi-filter/recipients input. Melt 0.44 ships no
  TagsInput builder ([[MELT-UI]] — same absence recorded for Pagination and
  DropdownMenu above), so the add/remove/keyboard semantics are hand-rolled
  here rather than delegated. tags/onTagsChange default to a safe empty-list,
  no-op state so a zero-prop invocation renders without throwing and fires
  no mutating call (adr-22 r1/r2).
-->
<script lang="ts">
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";

  let {
    tags = $bindable([] as string[]),
    onTagsChange = () => {},
    disabled = false,
    label = undefined,
    placeholder = t("demo_tags_input_placeholder"),
    name = undefined,
    class: className = undefined,
  }: {
    tags?: string[];
    onTagsChange?: (tags: string[]) => void;
    disabled?: boolean;
    label?: string;
    placeholder?: string;
    name?: string;
    class?: string;
  } = $props();

  let draft = $state("");

  function commit(): void {
    tags = [...tags, draft.trim()];
    onTagsChange(tags);
    draft = "";
  }

  function addFromDraft(): void {
    if (disabled) return;
    const value = draft.trim();
    if (!value || tags.includes(value)) {
      draft = "";
      return;
    }
    commit();
  }

  function removeTag(index: number): void {
    if (disabled) return;
    tags = tags.filter((_, i) => i !== index);
    onTagsChange(tags);
  }

  function onKeydown(event: KeyboardEvent): void {
    if (event.key === "Enter") {
      event.preventDefault();
      addFromDraft();
    } else if (event.key === "Backspace" && draft === "" && tags.length > 0) {
      removeTag(tags.length - 1);
    }
  }
</script>

<div class={cn("flex flex-col gap-2", className)}>
  {#if label}<span class="text-sm text-muted-foreground">{label}</span>{/if}
  <div
    class={cn(
      "flex flex-wrap items-center gap-2 rounded-md border border-border bg-popover px-2 py-1.5",
      disabled && "cursor-not-allowed opacity-50",
    )}
  >
    {#each tags as tag, i (tag + i)}
      <span
        class="flex items-center gap-1 rounded-md bg-primary px-2 py-0.5 text-sm text-primary-foreground"
      >
        {tag}
        <button
          type="button"
          {disabled}
          onclick={() => removeTag(i)}
          aria-label={t("demo_tags_input_remove")}
          class="rounded-sm hover:opacity-75"
        >
          ×
        </button>
      </span>
    {/each}
    <input
      bind:value={draft}
      onkeydown={onKeydown}
      onblur={addFromDraft}
      {disabled}
      {placeholder}
      aria-label={t("demo_tags_input_field")}
      class="min-w-24 flex-1 bg-transparent text-sm text-popover-foreground outline-none placeholder:text-muted-foreground"
    />
  </div>
  {#if name}<input type="hidden" {name} value={tags.join(",")} />{/if}
</div>
