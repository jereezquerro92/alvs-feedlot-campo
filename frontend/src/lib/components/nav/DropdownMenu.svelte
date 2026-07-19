<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Floating action menu on the melt/builders Popover ([[MELT-UI]]) — Melt 0.44
  ships no Dropdown Menu builder, so Popover supplies the float/anchor/
  dismissal plumbing and this component hand-rolls the menu semantics on
  top: roving DOM focus across items, arrow-key cycling with wraparound,
  typeahead-by-first-character, and a disabled item excluded from both.
  `focus.onOpen` is a Popover option (not a manual effect) — a CSS-selector
  getter scoped to this popover's own content id, resolved and `.focus()`'d
  by the builder itself once `open` flips true, landing focus on the first
  enabled `role="menuitem"`. `focus.onClose` is left at its default (the
  trigger element), so focus return on select/Escape needs no extra code.
  Escape is deliberately unhandled here — it bubbles to Melt's own
  document-level Escape listener untouched.

  Unlike overlay/Tooltip.svelte or nav/Tabs.svelte, the trigger takes no
  Snippet: every item here is a plain text label, so the trigger self-renders
  as a Button — DropdownMenuDemo exists purely for realistic sample data and
  a visible demo action, not to work around an Astro/Snippet-passing limit.
-->
<script lang="ts" module>
  export type DropdownMenuItem = {
    value: string;
    label: string;
    disabled?: boolean;
  };
</script>

<script lang="ts">
  import { Popover } from "melt/builders";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";

  let {
    items = [],
    triggerLabel = "",
    onSelect,
    class: className = undefined,
  }: {
    items?: DropdownMenuItem[];
    triggerLabel?: string;
    onSelect?: (value: string) => void;
    class?: string;
  } = $props();

  const popover = new Popover({
    focus: {
      onOpen: () => `#${popover.ids.content} [role="menuitem"]:not([aria-disabled="true"])`,
    },
  });

  let itemEls: (HTMLElement | null)[] = [];
  let typeaheadBuffer = $state("");
  let typeaheadTimer: ReturnType<typeof setTimeout> | undefined;

  const enabledIndices = $derived(
    items.reduce<number[]>((acc, item, i) => {
      if (!item.disabled) acc.push(i);
      return acc;
    }, []),
  );

  // Roving tabindex (WAI-ARIA menu pattern): exactly one item — the last
  // focused one — sits at tabindex 0, every other item (enabled or not) at
  // -1. `onfocus` on each item is the single point that advances it, so
  // keyboard nav, typeahead, mouse click, and Melt's own open-focus all
  // converge on the same state. Falls back to the first enabled item when
  // the tracked index no longer matches an enabled item (e.g. `items` prop
  // changed under it).
  let focusedIndex = $state(enabledIndices[0] ?? -1);
  const rovingIndex = $derived(
    enabledIndices.includes(focusedIndex) ? focusedIndex : (enabledIndices[0] ?? -1),
  );

  function currentFocusedIndex(): number {
    return itemEls.findIndex((el) => el === document.activeElement);
  }

  function focusItem(index: number) {
    itemEls[index]?.focus();
  }

  function select(item: DropdownMenuItem) {
    if (item.disabled) return;
    onSelect?.(item.value);
    popover.open = false;
  }

  function moveFocus(delta: 1 | -1) {
    if (enabledIndices.length === 0) return;
    const pos = enabledIndices.indexOf(currentFocusedIndex());
    const next =
      pos === -1
        ? delta === 1
          ? 0
          : enabledIndices.length - 1
        : (pos + delta + enabledIndices.length) % enabledIndices.length;
    focusItem(enabledIndices[next]);
  }

  function typeahead(char: string) {
    if (enabledIndices.length === 0) return;
    clearTimeout(typeaheadTimer);
    typeaheadBuffer += char;
    typeaheadTimer = setTimeout(() => (typeaheadBuffer = ""), 500);

    // shadcn/Radix convention: a run of the same character (e.g. "dd") cycles
    // through same-letter matches rather than searching a literal "dd" prefix.
    const repeated = [...typeaheadBuffer].every((c) => c === typeaheadBuffer[0]);
    const search = repeated ? typeaheadBuffer[0] : typeaheadBuffer;

    const pos = enabledIndices.indexOf(currentFocusedIndex());
    const startAfter = pos === -1 ? 0 : pos + 1;
    const ordered = [...enabledIndices.slice(startAfter), ...enabledIndices.slice(0, startAfter)];
    const match = ordered.find((i) => items[i].label.toLowerCase().startsWith(search));
    if (match !== undefined) focusItem(match);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      moveFocus(e.key === "ArrowDown" ? 1 : -1);
      return;
    }
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      const current = currentFocusedIndex();
      if (current !== -1) select(items[current]);
      return;
    }
    if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
      e.preventDefault();
      typeahead(e.key.toLowerCase());
    }
    // Escape (and anything else) falls through untouched to Melt's listeners.
  }
</script>

<Button type="button" variant="outline" {...popover.trigger} class={className}>
  {triggerLabel}
</Button>
<div
  {...popover.content}
  role="menu"
  onkeydown={handleKeydown}
  class="z-50 min-w-40 rounded-md border bg-popover p-1 text-popover-foreground shadow-md"
>
  {#each items as item, i (item.value)}
    <div
      bind:this={itemEls[i]}
      role="menuitem"
      tabindex={item.disabled ? -1 : i === rovingIndex ? 0 : -1}
      aria-disabled={item.disabled}
      onclick={() => select(item)}
      onfocus={() => (focusedIndex = i)}
      class={cn(
        "cursor-pointer rounded-sm px-2 py-1.5 text-sm outline-none",
        "hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground",
        item.disabled && "pointer-events-none cursor-default text-muted-foreground opacity-50",
      )}
    >
      {item.label}
    </div>
  {/each}
</div>
