<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Horizontal row of menu triggers, each a nav/DropdownMenu-style Melt Popover
  menu ([[MELT-UI]]) — Melt 0.44 ships no Menubar builder, so this component
  is a composition: one independent `Popover` instance per top-level menu,
  laid out in a row. Each menu reuses the exact roving-focus/typeahead item
  semantics of nav/DropdownMenu; the one addition a menubar needs beyond a
  lone dropdown is roving focus ACROSS triggers — ArrowLeft/ArrowRight move
  between menu buttons the same way ArrowUp/ArrowDown move between items
  inside one, and opening one menu while another is open swaps which is
  active (hovering a sibling trigger while a menu is open switches the open
  menu, the standard desktop-menubar convention).
-->
<script lang="ts" module>
  export type MenubarMenu = {
    value: string;
    label: string;
    items: { value: string; label: string; disabled?: boolean }[];
  };
</script>

<script lang="ts">
  import { Popover } from "melt/builders";
  import { buttonVariants } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";

  // adr-22 r1: a zero-prop invocation renders a sample two-menu bar rather
  // than throwing.
  let {
    menus = [
      {
        value: "file",
        label: t("demo_menubar_file"),
        items: [
          { value: "new", label: t("demo_menubar_new") },
          { value: "open", label: t("demo_menubar_open") },
        ],
      },
      {
        value: "edit",
        label: t("demo_menubar_edit"),
        items: [
          { value: "undo", label: t("demo_menubar_undo") },
          { value: "redo", label: t("demo_menubar_redo"), disabled: true },
        ],
      },
    ],
    onSelect,
    class: className = undefined,
  }: {
    menus?: MenubarMenu[];
    onSelect?: (menuValue: string, itemValue: string) => void;
    class?: string;
  } = $props();

  // One Popover per menu, keyed by menu value — each owns its own float/
  // dismiss state, same builder nav/DropdownMenu rides.
  const popovers = new Map(
    menus.map((menu) => [
      menu.value,
      new Popover({
        focus: {
          onOpen: () => {
            const popover = popovers.get(menu.value)!;
            return `#${popover.ids.content} [role="menuitem"]:not([aria-disabled="true"])`;
          },
        },
      }),
    ]),
  );

  let openMenu = $state<string | null>(null);
  let triggerEls: (HTMLElement | null)[] = [];
  let itemEls: Record<string, (HTMLElement | null)[]> = Object.fromEntries(
    menus.map((menu) => [menu.value, []]),
  );

  function openIndex(): number {
    return menus.findIndex((m) => m.value === openMenu);
  }

  function setOpen(value: string | null) {
    for (const [key, popover] of popovers) popover.open = key === value;
    openMenu = value;
  }

  function moveTrigger(delta: 1 | -1) {
    const current = openIndex();
    const base = current === -1 ? 0 : current;
    const next = (base + delta + menus.length) % menus.length;
    triggerEls[next]?.focus();
    if (openMenu !== null) setOpen(menus[next].value);
  }

  function enabledIndices(menu: MenubarMenu): number[] {
    return menu.items.reduce<number[]>((acc, item, i) => {
      if (!item.disabled) acc.push(i);
      return acc;
    }, []);
  }

  function select(menu: MenubarMenu, item: { value: string; disabled?: boolean }) {
    if (item.disabled) return;
    onSelect?.(menu.value, item.value);
    setOpen(null);
  }

  function currentItemFocus(menu: MenubarMenu): number {
    return (itemEls[menu.value] ?? []).findIndex((el) => el === document.activeElement);
  }

  function moveItemFocus(menu: MenubarMenu, delta: 1 | -1) {
    const enabled = enabledIndices(menu);
    if (enabled.length === 0) return;
    const pos = enabled.indexOf(currentItemFocus(menu));
    const next =
      pos === -1 ? (delta === 1 ? 0 : enabled.length - 1) : (pos + delta + enabled.length) % enabled.length;
    itemEls[menu.value]?.[enabled[next]]?.focus();
  }

  function handleTriggerKeydown(e: KeyboardEvent, menu: MenubarMenu) {
    if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
      e.preventDefault();
      moveTrigger(e.key === "ArrowRight" ? 1 : -1);
      return;
    }
    if (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setOpen(menu.value);
    }
  }

  function handleItemKeydown(e: KeyboardEvent, menu: MenubarMenu) {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      moveItemFocus(menu, e.key === "ArrowDown" ? 1 : -1);
      return;
    }
    if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
      e.preventDefault();
      moveTrigger(e.key === "ArrowRight" ? 1 : -1);
      return;
    }
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      const current = currentItemFocus(menu);
      if (current !== -1) select(menu, menu.items[current]);
    }
    // Escape falls through untouched to Melt's own listeners.
  }
</script>

<div class={cn("flex items-center gap-1 rounded-md border bg-popover p-1", className)}>
  {#each menus as menu, i (menu.value)}
    {@const popover = popovers.get(menu.value)!}
    <button
      bind:this={triggerEls[i]}
      type="button"
      {...popover.trigger}
      onclick={() => setOpen(openMenu === menu.value ? null : menu.value)}
      onmouseenter={() => openMenu !== null && setOpen(menu.value)}
      onkeydown={(e: KeyboardEvent) => handleTriggerKeydown(e, menu)}
      class={cn(
        "cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
        buttonVariants.variant.ghost,
        buttonVariants.size.sm,
        "rounded-md",
        openMenu === menu.value && "bg-accent text-accent-foreground",
      )}
    >
      {menu.label}
    </button>
    <div
      {...popover.content}
      role="menu"
      onkeydown={(e: KeyboardEvent) => handleItemKeydown(e, menu)}
      class="z-50 min-w-40 rounded-md border bg-popover p-1 text-popover-foreground shadow-md"
    >
      {#each menu.items as item, j (item.value)}
        <div
          bind:this={itemEls[menu.value][j]}
          role="menuitem"
          tabindex={item.disabled ? -1 : 0}
          aria-disabled={item.disabled}
          onclick={() => select(menu, item)}
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
  {/each}
</div>
