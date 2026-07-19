<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import * as Alert from "$lib/components/ui/alert";
  import { Separator } from "$lib/components/ui/separator";
  import { SectionTitle } from "$lib/components/primitives/titles";
  import { NumericValue, StatusBadge } from "$lib/components/data";
  import { EntityGrid, EntityCard, SummaryCard, type EntityStat, type SummaryItem } from "$lib/components/dashboard";

  type GalleryCopy = {
    title: string;
    intro: string;
    recoTitle: string;
    recoBody: string;
    typography: string;
    typographyNote: string;
    scaleH1: string;
    scaleH2: string;
    scaleH3: string;
    buttonsBadges: string;
    data: string;
    dataTable: string;
    numericValue: string;
    chipFilterBar: string;
    pagination: string;
    collapsible: string;
    tree: string;
    dashboard: string;
    metricTiles: string;
    entityGrid: string;
    summaryCard: string;
    summaryTitle: string;
    chat: string;
    chatNote: string;
    form: string;
    select: string;
    combobox: string;
    checkbox: string;
    switchTitle: string;
    datePicker: string;
    dateRangePicker: string;
    pinInput: string;
    tagsInput: string;
    calendar: string;
    rangeCalendar: string;
    slider: string;
    toggleGroup: string;
    navigation: string;
    tabs: string;
    dropdownMenu: string;
    contextMenu: string;
    menubar: string;
    tableOfContents: string;
    overlay: string;
    accordion: string;
    tooltip: string;
    popover: string;
    hoverCard: string;
    scrollArea: string;
    drawer: string;
    homeTriangle: string;
    cornerNavTriangle: string;
    feedback: string;
    progress: string;
    toast: string;
    auth: string;
    theme: string;
  };

  let {
    entities = [],
    summaryItems = [],
    copy = {} as GalleryCopy,
  }: {
    entities?: { title: string; subtitle: string; stats: EntityStat[]; status: string }[];
    summaryItems?: SummaryItem[];
    copy?: GalleryCopy;
  } = $props();
</script>

<main class="mx-auto max-w-5xl p-8 flex flex-col gap-8">
  <div class="flex flex-col gap-2">
    <SectionTitle as="h1">{copy.title}</SectionTitle>
    <p class="text-muted-foreground">{copy.intro}</p>
  </div>

  <Alert.Root>
    <Alert.Title>{copy.recoTitle}</Alert.Title>
    <Alert.Description>{copy.recoBody}</Alert.Description>
  </Alert.Root>

  <Separator />

  <section class="flex flex-col gap-3">
    <SectionTitle as="h2">{copy.typography}</SectionTitle>
    <p class="text-sm text-muted-foreground">{copy.typographyNote}</p>
    <SectionTitle as="h1">{copy.scaleH1}</SectionTitle>
    <SectionTitle as="h2">{copy.scaleH2}</SectionTitle>
    <SectionTitle as="h3">{copy.scaleH3}</SectionTitle>
  </section>

  <Separator />

  <section class="flex flex-col gap-4">
    <SectionTitle as="h2">{copy.buttonsBadges}</SectionTitle>
    <div class="flex flex-wrap gap-3">
      <Button>Default</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="destructive">Destructive</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="link" href="/showcase/">Link</Button>
    </div>
    <div class="flex flex-wrap gap-3">
      <Badge>Default</Badge>
      <Badge variant="secondary">Secondary</Badge>
      <Badge variant="destructive">Destructive</Badge>
      <Badge variant="outline">Outline</Badge>
    </div>
    <div class="flex flex-wrap gap-3">
      <StatusBadge status="approved" />
      <StatusBadge status="pending" />
      <StatusBadge status="rejected" />
    </div>
  </section>

  <Separator />

  <section class="flex flex-col gap-6">
    <SectionTitle as="h2">{copy.data}</SectionTitle>

    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.dataTable}</SectionTitle>
      <slot name="data-table" />
    </div>

    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.numericValue}</SectionTitle>
      <div class="flex flex-wrap gap-6">
        <NumericValue value={128400} currency="USD" />
        <NumericValue value={-5200} currency="USD" />
      </div>
    </div>

    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.chipFilterBar}</SectionTitle>
      <slot name="chip-filter-bar" />
    </div>

    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.pagination}</SectionTitle>
      <slot name="pagination" />
    </div>

    <div class="flex flex-col gap-2 max-w-xl">
      <SectionTitle as="h3">{copy.collapsible}</SectionTitle>
      <slot name="collapsible" />
    </div>

    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.tree}</SectionTitle>
      <slot name="tree" />
    </div>
  </section>

  <Separator />

  <section class="flex flex-col gap-6">
    <SectionTitle as="h2">{copy.dashboard}</SectionTitle>

    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.metricTiles}</SectionTitle>
      <slot name="metric-tiles" />
    </div>

    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.entityGrid}</SectionTitle>
      <EntityGrid>
        {#each entities as entity (entity.title)}
          <EntityCard title={entity.title} subtitle={entity.subtitle} stats={entity.stats} status={entity.status} />
        {/each}
      </EntityGrid>
    </div>

    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.summaryCard}</SectionTitle>
      <SummaryCard title={copy.summaryTitle} items={summaryItems} />
    </div>
  </section>

  <Separator />

  <section class="flex flex-col gap-6">
    <SectionTitle as="h2">{copy.form}</SectionTitle>

    <div class="flex flex-col gap-2 max-w-xs">
      <SectionTitle as="h3">{copy.select}</SectionTitle>
      <slot name="select" />
    </div>

    <div class="flex flex-col gap-2 max-w-xs">
      <SectionTitle as="h3">{copy.combobox}</SectionTitle>
      <slot name="combobox" />
    </div>

    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.checkbox}</SectionTitle>
      <slot name="checkbox" />
    </div>

    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.switchTitle}</SectionTitle>
      <slot name="switch" />
    </div>

    <div class="flex flex-col gap-2 max-w-xs">
      <SectionTitle as="h3">{copy.datePicker}</SectionTitle>
      <slot name="date-picker" />
    </div>

    <div class="flex flex-col gap-2 max-w-sm">
      <SectionTitle as="h3">{copy.dateRangePicker}</SectionTitle>
      <slot name="date-range-picker" />
    </div>

    <div class="flex flex-col gap-2 max-w-sm">
      <SectionTitle as="h3">{copy.pinInput}</SectionTitle>
      <slot name="pin-input" />
    </div>

    <div class="flex flex-col gap-2 max-w-sm">
      <SectionTitle as="h3">{copy.tagsInput}</SectionTitle>
      <slot name="tags-input" />
    </div>

    <div class="flex flex-col gap-2 max-w-xs">
      <SectionTitle as="h3">{copy.calendar}</SectionTitle>
      <slot name="calendar" />
    </div>

    <div class="flex flex-col gap-2 max-w-sm">
      <SectionTitle as="h3">{copy.rangeCalendar}</SectionTitle>
      <slot name="range-calendar" />
    </div>

    <div class="flex flex-col gap-2 max-w-sm">
      <SectionTitle as="h3">{copy.slider}</SectionTitle>
      <slot name="slider" />
    </div>

    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.toggleGroup}</SectionTitle>
      <slot name="toggle-group" />
    </div>
  </section>

  <Separator />

  <section class="flex flex-col gap-3">
    <SectionTitle as="h2">{copy.navigation}</SectionTitle>
    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.tabs}</SectionTitle>
      <slot name="tabs" />
    </div>
    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.dropdownMenu}</SectionTitle>
      <slot name="dropdown-menu" />
    </div>
    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.contextMenu}</SectionTitle>
      <slot name="context-menu" />
    </div>
    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.menubar}</SectionTitle>
      <slot name="menubar" />
    </div>
    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.tableOfContents}</SectionTitle>
      <slot name="table-of-contents" />
    </div>
  </section>

  <Separator />

  <section class="flex flex-col gap-3">
    <SectionTitle as="h2">{copy.chat}</SectionTitle>
    <p class="text-sm text-muted-foreground">{copy.chatNote}</p>
    <div class="relative h-[28rem] w-full overflow-hidden rounded-xl border">
      <slot name="chat" />
    </div>
  </section>

  <Separator />

  <section class="flex flex-col gap-4">
    <SectionTitle as="h2">{copy.overlay}</SectionTitle>
    <div class="flex flex-wrap gap-3">
      <slot name="overlay-triggers" />
    </div>
    <div class="flex flex-col gap-2 max-w-xl">
      <SectionTitle as="h3">{copy.accordion}</SectionTitle>
      <slot name="accordion" />
    </div>
    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.tooltip}</SectionTitle>
      <slot name="tooltip" />
    </div>
    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.popover}</SectionTitle>
      <slot name="popover" />
    </div>
    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.hoverCard}</SectionTitle>
      <slot name="hover-card" />
    </div>
    <div class="flex flex-col gap-2 max-w-xl">
      <SectionTitle as="h3">{copy.scrollArea}</SectionTitle>
      <slot name="scroll-area" />
    </div>
    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.drawer}</SectionTitle>
      <slot name="drawer" />
    </div>
    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.homeTriangle}</SectionTitle>
      <slot name="home-triangle" />
    </div>
    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.cornerNavTriangle}</SectionTitle>
      <slot name="corner-nav-triangle" />
    </div>
  </section>

  <Separator />

  <section class="flex flex-col gap-3">
    <SectionTitle as="h2">{copy.feedback}</SectionTitle>
    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.progress}</SectionTitle>
      <slot name="progress" />
    </div>
    <div class="flex flex-col gap-2">
      <SectionTitle as="h3">{copy.toast}</SectionTitle>
      <slot name="toast" />
    </div>
  </section>

  <Separator />

  <section class="flex flex-col gap-3">
    <SectionTitle as="h2">{copy.auth}</SectionTitle>
    <slot name="auth" />
  </section>

  <Separator />

  <section class="flex flex-col gap-3">
    <SectionTitle as="h2">{copy.theme}</SectionTitle>
    <slot name="theme-toggle" />
  </section>
</main>
