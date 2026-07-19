<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Inline single-month grid for a single-date selection — the inline-view
  sibling of form/DatePicker's popover-native-input approach. Melt 0.44 ships
  no Calendar builder ([[MELT-UI]] — same absence recorded for Pagination and
  Dropdown Menu above), so the month grid, weekday header, and prev/next nav
  are hand-rolled here rather than delegated. value/onValueChange default to
  a safe "nothing selected, current month" state and a no-op callback so a
  zero-prop invocation renders without throwing and fires no mutating call
  (adr-22 r1/r2). Color-scheme theming rides the app-wide `:root`/`.dark`
  rule (issue #174) — this component holds no native form control needing an
  explicit override, same as form/Pagination and form/TagsInput.
-->
<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";

  let {
    value = $bindable(undefined),
    onValueChange = () => {},
    min = undefined,
    max = undefined,
    class: className = undefined,
  }: {
    value?: string | undefined;
    onValueChange?: (value: string) => void;
    min?: string;
    max?: string;
    class?: string;
  } = $props();

  const todayIso = new Date().toISOString().slice(0, 10);
  const initialMonth = value ?? todayIso;
  let viewYear = $state(Number(initialMonth.slice(0, 4)));
  let viewMonth = $state(Number(initialMonth.slice(5, 7)) - 1);

  const weekdayKeys = [
    "demo_calendar_weekday_sun",
    "demo_calendar_weekday_mon",
    "demo_calendar_weekday_tue",
    "demo_calendar_weekday_wed",
    "demo_calendar_weekday_thu",
    "demo_calendar_weekday_fri",
    "demo_calendar_weekday_sat",
  ] as const;

  const monthKeys = [
    "demo_calendar_month_1",
    "demo_calendar_month_2",
    "demo_calendar_month_3",
    "demo_calendar_month_4",
    "demo_calendar_month_5",
    "demo_calendar_month_6",
    "demo_calendar_month_7",
    "demo_calendar_month_8",
    "demo_calendar_month_9",
    "demo_calendar_month_10",
    "demo_calendar_month_11",
    "demo_calendar_month_12",
  ] as const;

  function toIso(year: number, month: number, day: number): string {
    return `${String(year).padStart(4, "0")}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
  }

  function inRange(iso: string): boolean {
    if (min && iso < min) return false;
    if (max && iso > max) return false;
    return true;
  }

  const cells = $derived.by(() => {
    const firstOfMonth = new Date(viewYear, viewMonth, 1);
    const startOffset = firstOfMonth.getDay();
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
    const daysInPrevMonth = new Date(viewYear, viewMonth, 0).getDate();
    const out: { iso: string; day: number; outOfMonth: boolean }[] = [];
    for (let i = 0; i < startOffset; i++) {
      const day = daysInPrevMonth - startOffset + 1 + i;
      const [year, month] = viewMonth === 0 ? [viewYear - 1, 11] : [viewYear, viewMonth - 1];
      out.push({ iso: toIso(year, month, day), day, outOfMonth: true });
    }
    for (let day = 1; day <= daysInMonth; day++) {
      out.push({ iso: toIso(viewYear, viewMonth, day), day, outOfMonth: false });
    }
    while (out.length % 7 !== 0 || out.length < 42) {
      const last = out[out.length - 1];
      const lastDate = new Date(`${last.iso}T00:00:00`);
      lastDate.setDate(lastDate.getDate() + 1);
      out.push({
        iso: lastDate.toISOString().slice(0, 10),
        day: lastDate.getDate(),
        outOfMonth: true,
      });
      if (out.length >= 42) break;
    }
    return out;
  });

  function selectDay(iso: string): void {
    if (!inRange(iso)) return;
    value = iso;
    onValueChange(iso);
  }

  function prevMonth(): void {
    if (viewMonth === 0) {
      viewMonth = 11;
      viewYear -= 1;
    } else {
      viewMonth -= 1;
    }
  }

  function nextMonth(): void {
    if (viewMonth === 11) {
      viewMonth = 0;
      viewYear += 1;
    } else {
      viewMonth += 1;
    }
  }
</script>

<div
  class={cn(
    "flex flex-col gap-2 rounded-md border border-border bg-popover p-3 text-popover-foreground",
    className,
  )}
>
  <div class="flex items-center justify-between">
    <Button
      type="button"
      variant="ghost"
      size="icon"
      onclick={prevMonth}
      aria-label={t("demo_calendar_prev")}
    >
      <span aria-hidden="true">‹</span>
    </Button>
    <span class="text-sm font-medium">{t(monthKeys[viewMonth])} {viewYear}</span>
    <Button
      type="button"
      variant="ghost"
      size="icon"
      onclick={nextMonth}
      aria-label={t("demo_calendar_next")}
    >
      <span aria-hidden="true">›</span>
    </Button>
  </div>
  <div class="grid grid-cols-7 gap-1 text-center text-xs text-muted-foreground">
    {#each weekdayKeys as key (key)}
      <span>{t(key)}</span>
    {/each}
  </div>
  <div class="grid grid-cols-7 gap-1" role="grid" aria-label={t("demo_calendar_grid")}>
    {#each cells as cell (cell.iso)}
      <button
        type="button"
        role="gridcell"
        aria-selected={value === cell.iso}
        aria-label={cell.iso}
        disabled={!inRange(cell.iso)}
        onclick={() => selectDay(cell.iso)}
        class={cn(
          "h-8 w-8 rounded-md text-sm",
          cell.outOfMonth && "text-muted-foreground/50",
          cell.iso === todayIso && value !== cell.iso && "border border-primary",
          value === cell.iso && "bg-primary text-primary-foreground",
          !inRange(cell.iso) && "cursor-not-allowed opacity-50",
        )}
      >
        {cell.day}
      </button>
    {/each}
  </div>
</div>
