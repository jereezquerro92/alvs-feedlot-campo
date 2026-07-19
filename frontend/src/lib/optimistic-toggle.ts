/* LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-04-frontend-and-design-system]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

// Pure, DOM-free helper backing ProfileForm's avatar-visibility toggle
// (docs/bdds/bdd-05-profile-page.md: "the toggle reverts to its prior state
// on avatar failure"). Kept outside the Svelte component so the revert
// semantics are unit-testable without a browser environment.

/**
 * Optimistically flips `current`, applies it via `apply`, then persists it
 * via `persist`. If `persist` resolves false (or rejects), reverts `apply`
 * back to `current`.
 */
export async function optimisticToggle(
  current: boolean,
  apply: (next: boolean) => void,
  persist: (next: boolean) => Promise<boolean>,
): Promise<void> {
  const next = !current;
  apply(next);
  let ok = false;
  try {
    ok = await persist(next);
  } catch {
    ok = false;
  }
  if (!ok) apply(current);
}
