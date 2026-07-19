/* LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-04-frontend-and-design-system]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

// Pure, DOM-free typewriter cycle. The scheduler is injected so this module
// has zero global setTimeout/clearTimeout calls, keeping it testable with a
// fake clock (frontend/tests/optimistic-toggle.test.ts convention) and
// reusable by ChatComposer.svelte as a real-timer-backed placeholder overlay.

export type TimerHandle = unknown;

export type Scheduler = {
  set: (cb: () => void, ms: number) => TimerHandle;
  clear: (handle: TimerHandle) => void;
};

export type TypewriterTimings = {
  typeMs: number;
  holdMs: number;
  deleteMs: number;
};

export type TypewriterCycle = {
  /** Begins (or restarts from phrase 0) the type/hold/delete/cycle loop. */
  start(): void;
  /** Cancels any pending timer and clears the rendered text. */
  stop(): void;
  /** Subscribes to every text update; returns an unsubscribe function. */
  onUpdate(cb: (text: string) => void): () => void;
};

export function createTypewriterCycle(
  phrases: readonly string[],
  timings: TypewriterTimings,
  scheduler: Scheduler,
): TypewriterCycle {
  const { typeMs, holdMs, deleteMs } = timings;
  let phraseIndex = 0;
  let timerHandle: TimerHandle | undefined;
  const listeners = new Set<(text: string) => void>();

  function emit(text: string): void {
    for (const listener of listeners) listener(text);
  }

  function clearTimer(): void {
    if (timerHandle !== undefined) scheduler.clear(timerHandle);
    timerHandle = undefined;
  }

  function typePhrase(charIndex: number): void {
    const phrase = phrases[phraseIndex] ?? "";
    if (charIndex <= phrase.length) {
      emit(phrase.slice(0, charIndex));
      timerHandle = scheduler.set(() => typePhrase(charIndex + 1), typeMs);
    } else {
      timerHandle = scheduler.set(() => deletePhrase(phrase.length), holdMs);
    }
  }

  function deletePhrase(charIndex: number): void {
    if (charIndex >= 0) {
      emit((phrases[phraseIndex] ?? "").slice(0, charIndex));
      timerHandle = scheduler.set(() => deletePhrase(charIndex - 1), deleteMs);
    } else {
      phraseIndex = phrases.length === 0 ? 0 : (phraseIndex + 1) % phrases.length;
      timerHandle = scheduler.set(() => typePhrase(0), typeMs);
    }
  }

  return {
    start(): void {
      clearTimer();
      if (phrases.length === 0) return;
      typePhrase(0);
    },
    stop(): void {
      clearTimer();
      emit("");
    },
    onUpdate(cb: (text: string) => void): () => void {
      listeners.add(cb);
      return () => listeners.delete(cb);
    },
  };
}
