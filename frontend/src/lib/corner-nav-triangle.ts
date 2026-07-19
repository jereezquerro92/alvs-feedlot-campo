/* LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-04-frontend-and-design-system]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

// Pure resolver for CornerNavTriangle's route -> next-front mapping
// (bdd-11-corner-nav-triangle). The fixed cycle is home -> chat ->
// showcase -> home; the icon shown is always the DESTINATION of the next
// click, derived from the current route, never from persisted client
// state (bdd-11 "Chosen cycle semantics"). An unrecognized route falls
// back to the same default as the zero-props case: "currently home",
// so the next stop is chat.

export type Front = "home" | "chat" | "showcase";

const CYCLE: readonly Front[] = ["home", "chat", "showcase"];

const FRONT_PATH: Record<Front, string> = {
  home: "/",
  chat: "/chatui/",
  showcase: "/showcase/components/",
};

// Resolve which front the CURRENT route belongs to, defaulting to "home"
// for any unrecognized path (adr-22 r1: a safe default, never a throw).
export function resolveCurrentFront(pathname: string | undefined): Front {
  if (pathname === FRONT_PATH.chat) return "chat";
  if (pathname === FRONT_PATH.showcase) return "showcase";
  return "home";
}

// The next front in the fixed cycle, wrapping showcase -> home.
export function nextFront(current: Front): Front {
  const index = CYCLE.indexOf(current);
  return CYCLE[(index + 1) % CYCLE.length];
}

// The plain-anchor href for a given front (rung-1 navigation, no client
// router — adr-04 r3 interactivity ladder).
export function frontHref(front: Front): string {
  return FRONT_PATH[front];
}
