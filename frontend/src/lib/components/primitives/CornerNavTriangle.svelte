<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Fixed, bottom-right, isosceles-triangle nav cycling home/chat/showcase
  (bdd-11-corner-nav-triangle, #374, mounted globally in Base.astro by
  #377). Distinct from primitives/HomeTriangle.svelte (#255): top-left,
  right-angle, single-target. Rounded-corner polygon has no Melt builder
  (adr-04 r8 last resort) — drawn as an SVG path instead of clip-path.
  Zero props is a safe default (adr-22 r1/r2): a plain, non-mutating
  `<a href>` derived from the current route.
-->
<script lang="ts">
  import { resolveCurrentFront, nextFront, frontHref, type Front } from "$lib/corner-nav-triangle";
  import { t } from "../../../i18n";

  let {
    pathname = undefined,
  }: {
    /** Current route; defaults to `undefined`, which resolves to "home"
     * (adr-22 r1 safe default). Astro pages pass `Astro.url.pathname`. */
    pathname?: string;
  } = $props();

  const current = $derived(resolveCurrentFront(pathname));
  const destination = $derived(nextFront(current));
  const href = $derived(frontHref(destination));

  const ariaLabelKey = $derived(
    destination === "chat"
      ? "corner_nav_triangle_aria_label_chat"
      : destination === "showcase"
        ? "corner_nav_triangle_aria_label_showcase"
        : "corner_nav_triangle_aria_label_home",
  );
</script>

<!-- Styles ride the markup via {@html <style>}, not a component <style>
     block and not svelte:head: Astro drops both for an SSR-only (never
     hydrated) framework component — scoped CSS ships inside the client JS
     module that never runs, and framework head payloads are not injected.
     Inline <style> in the body is the one channel that always SSRs. -->
{@html `<style>
  @font-face {
    font-family: "Corner Nav Symbols";
    font-style: normal;
    font-weight: 400;
    src: url(data:font/woff2;base64,d09GMgABAAAAAAN8AA4AAAAAB5gAAAMnAAL1wwAAAAAAAAAAAAAAAAAAAAAAAAAAHCoGYD9TVEFUYgBEEQgKhECEEgE2AiQDCgsKAAQgBYRyByAMBxtmBiAeB+XGMwlJckb9GFvwPN+fee57P2NVPxVTiCNhldRedVIJix2EdXievL1/G40mNKJ5d13gSXdhLsEIEi3/6Ut9/veb+YI3/um4lUpsYg+8iUeauKREyBZJHE6nbktheWsLeTp14RnReSBYW1xM/P2PIMBLT72pOWNeAn5XbkMVEQyACwAAYJQbsh6L0LA00aKAPADwgTO36JncePX48ynDdDnBGKQDAeilbwCmfoTwYIAQGgyj/vz4kwWYuU+eJoLcNfVtolBPcUmDaDQ3QToTQsULAKGoeBMBNA2Yrwf1AqRAP8QnJWWwfceDB4VXjz+f+HzKxbNdRobFnvgIYkIob/YHwgDgAYLAU+AfABgAwIemezCNnxbo5xfRPSh75TURx3Vv71VXwX7FKwXaJp2Sr/MWr9wEAznifPEmBX5IK0o+DjwSiwb+UEVV/g6HaINfzpg4zrLZUKiLyd7iOOztveogeLOQRBLS1RTtOB6evH9Vj8QtR/sUe608JOI4VIoPgP1A7lqyTp6ZROV16+x9d+sPqzOdal+H4ecUpOigl87grWt3+my1LeMnt31d0GbN/PyZnt7V6FAtIvaEVy/GRscBrwA74Ps98wXsaDM/77c8CCwKdFr8QUvJETw9C6LPkmD5svOiR0S3fJHgEusPawvVmgIxZVWL9Ue0WSJbKOn25QDUEKD+2+6N8iXbf9x/D6VvAHxoepsD8GGhT45r6Sf6FuBGARB8GBG9CPjEDYII+Gse0CKGEwFGKukKQNgjX7vQpHoCObiUC5scueJnvVyLs0NumOSX3CIqNpmbcZmjJ+CRpXLBK2vliohsl2t8cgJezCvv8sYjD5iqWo1WdUoVK9HANITNECOYZqqe5sUqFDLNE081kElNVpExxUl99cBzheoVqtOkUIGB5svVACZK5YruxWtVKU+1Ci+v1qhKgdmakGLoL1fIVWeIgUYbwWasmaJFm2ls2+ExaqwYYLNd0irTfUlyUu9UtSr3Iue3MDJDhgoy89KXS+uPVqNBqfyF9pdqUyhZ4UsvX6BanUpSYohhoiMtLInSC+JacsJYAw==) format("woff2");
  }

  .corner-nav-glyph {
    position: absolute;
    right: 0.5625rem;
    bottom: 0.5625rem;
    font-family: "Corner Nav Symbols";
    font-size: 2.25rem;
    line-height: 1;
    color: var(--color-background);
  }
</style>`}

<a
  href={href}
  aria-label={t(ariaLabelKey)}
  class="fixed bottom-[0.01rem] right-[0.01rem] z-50 block h-24 w-24 select-none [-webkit-user-select:none]"
  style="cursor: pointer;"
>
  <svg
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
    class="h-full w-full"
    aria-hidden="true"
  >
    <!--
      Isosceles triangle filling the bottom-right corner of its 24x24 box,
      every corner (both base corners AND the bottom-right vertex touching
      the box's own corner) rounded by the SAME arc radius via cubic-bezier
      corner cuts — the mechanism a plain clip-path polygon cannot express.
    -->
    <path
      d="M 22.5 6.5
         C 22.5 5.67 21.83 5 21 5
         C 20.45 5 19.97 5.30 19.71 5.75
         L 5.75 19.71
         C 5.30 19.97 5 20.45 5 21
         C 5 21.83 5.67 22.5 6.5 22.5
         L 21 22.5
         C 21.83 22.5 22.5 21.83 22.5 21
         Z"
      fill="var(--color-primary)"
      style="filter: drop-shadow(0 0.5px 0.75px oklch(0 0 0 / 0.22));"
    />
    <!-- Volume fillet: a hairline light stroke along the hypotenuse only —
         the lit upper edge that, with the drop shadow below, reads as a
         minimal thickness difference rather than a border. -->
    <path
      d="M 19.71 5.75 L 5.75 19.71"
      fill="none"
      stroke="oklch(1 0 0 / 0.35)"
      stroke-width="0.5"
      stroke-linecap="round"
    />
  </svg>
  <!-- Icon: Material Symbols Rounded glyph (codepoint, not ligature — the
       embedded subset carries only these three), set directly on the
       triangle in the page-background color. Font is subset to <1KB and
       embedded right here so the component is self-contained. -->
  <span class="corner-nav-glyph" aria-hidden="true">{destination === "chat" ? "\ue0cb" : destination === "showcase" ? "\ue9b0" : "\ue9b2"}</span>
</a>
