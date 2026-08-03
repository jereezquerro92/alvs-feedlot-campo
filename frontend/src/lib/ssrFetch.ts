/* LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-52-frontend-and-design-system]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

/** Default SSR backend fetch budget — stalls degrade instead of hanging the render. */
export const DEFAULT_SSR_FETCH_TIMEOUT_MS = 10_000;

export type SsrFetchInit = RequestInit & {
  /** Abort after this many ms. Defaults to {@link DEFAULT_SSR_FETCH_TIMEOUT_MS}. */
  timeoutMs?: number;
};

/**
 * `fetch` with AbortController timeout for Astro SSR → Django calls.
 * Callers keep their existing try/catch / null fallbacks; AbortError surfaces as rejection.
 */
export async function ssrFetch(
  input: string | URL,
  init: SsrFetchInit = {},
): Promise<Response> {
  const { timeoutMs = DEFAULT_SSR_FETCH_TIMEOUT_MS, signal: outerSignal, ...rest } =
    init;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  const onOuterAbort = () => controller.abort();
  if (outerSignal) {
    if (outerSignal.aborted) controller.abort();
    else outerSignal.addEventListener("abort", onOuterAbort, { once: true });
  }

  try {
    return await fetch(input, { ...rest, signal: controller.signal });
  } finally {
    clearTimeout(timer);
    outerSignal?.removeEventListener("abort", onOuterAbort);
  }
}
