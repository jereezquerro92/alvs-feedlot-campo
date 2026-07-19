import { describe, expect, test } from "bun:test";
import { createTypewriterCycle, type Scheduler } from "../src/lib/typewriter-placeholder";

// Deterministic coverage for the typewriter placeholder cycle. No real
// timers, no DOM — a fake scheduler drives the cycle synchronously by
// running the next queued callback on demand, mirroring this template's
// DOM-free bun:test convention (see optimistic-toggle.test.ts).

function createFakeScheduler() {
  let nextId = 0;
  const queue = new Map<number, { cb: () => void; ms: number }>();

  const scheduler: Scheduler = {
    set(cb, ms) {
      const id = nextId++;
      queue.set(id, { cb, ms });
      return id;
    },
    clear(handle) {
      queue.delete(handle as number);
    },
  };

  return {
    scheduler,
    /** Runs the single pending timer and asserts its scheduled delay. */
    fire(expectedMs?: number): void {
      const [id, entry] = [...queue.entries()][0] ?? [];
      if (id === undefined || !entry) throw new Error("no pending timer to fire");
      if (expectedMs !== undefined) expect(entry.ms).toBe(expectedMs);
      queue.delete(id);
      entry.cb();
    },
    pendingCount(): number {
      return queue.size;
    },
  };
}

const PHRASES = ["ab", "c", "de"];
const TIMINGS = { typeMs: 45, holdMs: 10000, deleteMs: 25 };

describe("createTypewriterCycle", () => {
  test("types char-by-char at typeMs, holds at holdMs, deletes at deleteMs", () => {
    const { scheduler, fire } = createFakeScheduler();
    const cycle = createTypewriterCycle(PHRASES, TIMINGS, scheduler);
    const updates: string[] = [];
    cycle.onUpdate((text) => updates.push(text));

    cycle.start();
    expect(updates).toEqual([""]);

    fire(45);
    expect(updates.at(-1)).toBe("a");
    fire(45);
    expect(updates.at(-1)).toBe("ab");
    fire(45); // charIndex now past phrase.length -> schedules the hold

    fire(10000);
    expect(updates.at(-1)).toBe("ab");

    fire(25);
    expect(updates.at(-1)).toBe("a");
    fire(25);
    expect(updates.at(-1)).toBe("");
  });

  test("cycles to the next phrase immediately after deleting, wrapping index % length", () => {
    const { scheduler, fire } = createFakeScheduler();
    const cycle = createTypewriterCycle(["a", "b"], TIMINGS, scheduler);
    const updates: string[] = [];
    cycle.onUpdate((text) => updates.push(text));

    cycle.start(); // type "a"
    fire(45); // "a"
    fire(45); // charIndex past phrase.length -> schedules the hold
    fire(10000); // hold -> delete
    fire(25); // "a" -> "" (charIndex 1 -> 0)
    fire(25); // charIndex -1 -> wraps to phrase 1

    // next scheduled timer types phrase index 1 ("b") immediately (typeMs, no extra pause)
    fire(45);
    expect(updates.at(-1)).toBe("");
    fire(45);
    expect(updates.at(-1)).toBe("b");
    fire(45); // charIndex past phrase.length -> schedules the hold

    fire(10000);
    fire(25); // delete "b" -> "" and wraps back to phrase 0 ("a")
    expect(updates.at(-1)).toBe("");
  });

  test("stop() cancels the pending timer and clears the rendered text", () => {
    const { scheduler, fire, pendingCount } = createFakeScheduler();
    const cycle = createTypewriterCycle(PHRASES, TIMINGS, scheduler);
    const updates: string[] = [];
    cycle.onUpdate((text) => updates.push(text));

    cycle.start();
    fire(45); // "a"
    cycle.stop();

    expect(updates.at(-1)).toBe("");
    expect(pendingCount()).toBe(0);
  });

  test("start() after stop() restarts from phrase 0", () => {
    const { scheduler, fire } = createFakeScheduler();
    const cycle = createTypewriterCycle(PHRASES, TIMINGS, scheduler);
    const updates: string[] = [];
    cycle.onUpdate((text) => updates.push(text));

    cycle.start();
    fire(45); // "a"
    fire(45); // "ab"
    cycle.stop();
    updates.length = 0;

    cycle.start();
    expect(updates).toEqual([""]);
    fire(45);
    expect(updates.at(-1)).toBe("a");
  });
});
