<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Right-click menu on the melt/builders Popover ([[MELT-UI]]) — Melt 0.44
  ships no Context Menu builder, so, exactly like nav/DropdownMenu, Popover
  supplies the dismissal/portal plumbing and this component hand-rolls the
  menu semantics on top (roving DOM focus, arrow-key cycling with wraparound,
  typeahead-by-first-character, disabled items excluded from both). The one
  divergence from DropdownMenu: there is no visible trigger element — the
  trigger is the `contextmenu` (right-click) event on the wrapped region, so
  `popover.open` is flipped by hand and the content is positioned at the
  pointer coordinates captured off that event, rather than anchored to a
  Button via `popover.trigger`. `focus.onOpen` still lands focus on the first
  enabled `role="menuitem"` the same way DropdownMenu does.
-->
<script lang="ts" module>
  export type ContextMenuItem = {
    value: string;
    label: string;
    disabled?: boolean;
  };
</script>

<script lang="ts">
  import { Popover } from "melt/builders";
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";
  import type { Snippet } from "svelte";

  // adr-22 r1: a zero-prop invocation renders its own sample region and
  // sample items rather than throwing — `children` defaults to a plain
  // labeled `<div>`, `items` to three demo entries.
  let {
    items = [
      { value: "copy", label: t("demo_context_menu_copy") },
      { value: "paste", label: t("demo_context_menu_paste") },
      { value: "delete", label: t("demo_context_menu_delete") },
    ],
    onSelect,
    children,
    class: className = undefined,
  }: {
    items?: ContextMenuItem[];
    onSelect?: (value: string) => void;
    children?: Snippet;
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
  let point = $state({ x: 0, y: 0 });

  const enabledIndices = $derived(
    items.reduce<number[]>((acc, item, i) => {
      if (!item.disabled) acc.push(i);
      return acc;
    }, []),
  );

  // Roving tabindex, same convention as nav/DropdownMenu.
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

  function select(item: ContextMenuItem) {
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
    // Escape falls through untouched to Melt's own listeners.
  }

  function handleContextMenu(e: MouseEvent) {
    e.preventDefault();
    point = { x: e.clientX, y: e.clientY };
    popover.open = true;
  }
</script>

<div
  oncontextmenu={handleContextMenu}
  class={cn(
    !children && "flex items-center justify-center rounded-md border border-dashed p-8 text-sm text-muted-foreground",
    className,
  )}
>
  {#if children}
    {@render children()}
  {:else}
    {t("demo_context_menu_region")}
  {/if}
</div>
<div
  {...popover.content}
  role="menu"
  onkeydown={handleKeydown}
  style={`position: fixed; left: ${point.x}px; top: ${point.y}px;`}
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
