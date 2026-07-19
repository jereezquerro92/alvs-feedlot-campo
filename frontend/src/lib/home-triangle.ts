/* LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-04-frontend-and-design-system]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

// Pure resolver for HomeTriangle's action prop (adr-22 rules 1-2): a caller
// wires the "go home" affordance through EITHER `href` (rung-1 plain anchor,
// preferred) OR `onHome` (escalation point for a future richer behavior,
// per the issue's "it'll probably become something else" framing) — never
// both at once, and neither is required. With no prop supplied the target
// is inert: no navigation, no callback, a safe no-op affordance.
export type HomeTarget =
  | { kind: "link"; href: string }
  | { kind: "action"; onHome: () => void }
  | { kind: "inert" };

export function resolveHomeTarget(href?: string, onHome?: () => void): HomeTarget {
  if (href) return { kind: "link", href };
  if (onHome) return { kind: "action", onHome };
  return { kind: "inert" };
}

// Pure resolver for the interactive branches' accessible name (issue #283,
// WCAG 4.1.2): an inert target needs no name (its `<span>` stays
// `aria-hidden`, untouched by this function). A link/action target always
// resolves to a non-empty name — the caller-supplied `ariaLabel` when given,
// otherwise `fallbackLabel` (the component's own i18n-resolved default) —
// so an interactive HomeTriangle can never render with an empty or absent
// accessible name, regardless of whether the caller remembered `ariaLabel`.
export function resolveAccessibleLabel(
  target: HomeTarget,
  ariaLabel: string | undefined,
  fallbackLabel: string,
): string | undefined {
  if (target.kind === "inert") return undefined;
  return ariaLabel && ariaLabel.length > 0 ? ariaLabel : fallbackLabel;
}
