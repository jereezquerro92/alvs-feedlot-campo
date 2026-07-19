# cast.md — the node spec

SSOT for what every node in **triage-and-fix** *is*, mechanically. The script that
implements it is `workflows/triage-and-fix.js`; the shared context handed to every node is
`team-party.md`; the human-facing frames are `scenes.md`.

Names are English, always — they are identifiers. The only Spanish in this system is the
party's spoken lines — the `SAY` table in the script and the scene bank's frames.

## Runtime contract (verified, not assumed)

Read out of the shipped Claude Code **2.1.212** binary's own strings, and re-checked by
`workflows/validate.mjs`, which applies the same gate the runtime applies.

- A workflow is **plain JavaScript**. TypeScript syntax fails to parse. The file must be
  `.js` — discovery logs `.mjs` / `.cjs` / `.ts` as *near-miss extensions* and skips them.
- `export const meta = { name, description, whenToUse?, phases? }` must be the **first
  statement** and a **pure literal**: no interpolation, no spread, no computed keys, no
  calls. `name` and `description` must be non-empty strings. This workflow's `phases` is
  `['forest', 'tavern', 'camp', 'stalking', 'plaza']`.
- Named workflows resolve from the **user** and **project** `.claude/workflows/` directories.
  Invoke as `Workflow({name: 'triage-and-fix', args: {...}})`.
- `agent(prompt, opts)` — `opts = {label?, phase?, schema?, model?, effort?, isolation?, agentType?}`.
  `effort` ∈ `low|medium|high|xhigh|max`. **Every call in this script pins both `model` and
  `effort` explicitly.** The v1 bug — nodes silently inheriting the session's model, scouts
  firing as opus because nobody set the option — is closed by making the pin mandatory at
  every call site, not by convention.
- **`agent()` returns `null` when the subagent dies.** Every call site must handle it. With
  `schema`, the subagent is forced to call `StructuredOutput` exactly once; there is a retry
  cap and a stall detector behind it.
- `opts.agentType` resolves from the **same registry as the Agent tool** and is checked
  against permission rules. An unknown type fails the call with the available list.
- `parallel(thunks)` is a **barrier** and takes **thunks**, not promises: `() => agent(...)`.
  Passing promises is rejected.
- `pipeline(items, stage1, stage2, …)` has no barrier between stages.
- `phase(title)`, `log(message)`, `args`, `budget.remaining()` exist. `workflow('<name>')`
  nests another workflow.
- **The script has no filesystem and no shell.** It coordinates control flow over
  already-typed values. Agents do all I/O. This is why `team-party.md` is inlined into the
  script as a constant rather than read at run time.
- `Date.now()`, `Math.random()`, argless `new Date()` **throw** — they break resume.
  `import()` and `with` are unavailable.
- No mid-run user input. A run cannot pause to ask a human anything.

## The standing rule — the fiction is a render, never an input

Every schema carries typed fields and the two machine tags (`difficulty`, `size`) — never a
prey name, never a scene. **A prey name is a render of state, not an input to a decision.**
No node reads "skaven" or "goblins" out of another node's output. Flavour is derived from
the tags *after* every decision is made, and never feeds back into a schema. The priest's
`clean|blocked` verdict follows the same law: it is a typed field, never a rendered word.

A node whose behaviour changes because of a scene description is a defect, exactly as a
live-doc block that becomes a second SSOT is a defect.

### The quote contract

Every node has a voice: **one short Spanish line, in character, announcing its step**. The
lines live in the `SAY` table in the script and, per node, at the top of its agent
definition. The script `log()`s them at stage transitions.

They are a **closed set, written in advance** — exactly the discipline `scenes.md` states
for its frames: *nothing here is generated at runtime*. **No node ever produces its own
line**, and there is no `quote` field in any schema. This matters more than it looks: a
model-generated line would be model output, and model output that reaches the log is a
channel — inert today, load-bearing the first time someone parses it. Keeping the voice in
a const table means it can never become state. Strip the `SAY` table and every outcome is
byte-identical.

The familiars' lines live only in their agent definitions, because the mage spawns them
itself and the script never witnesses those transitions.

This is the exact line the earlier draft of this spec crossed. It wrote that the owl was
"the only familiar considered trustworthy" — an animal's trait promoted to an engineering
claim, which a reader then acted on. The owl is reliable in exactly one situation: a closed
question against first-party docs, which is a property of **the question shape and the
domain allowlist**, not of the bird. Reliability here has three sources and no others:
**model tier, tool grant, and the schema that closes the output.**

## The prey table

Rows `difficulty`, columns `size`. The hunter assigns both during its paperwork call. This
is where the table becomes machine-readable; the names are printed and never parsed.
Unchanged from v1 — the phase rewrite touches the cast, not the tags.

```
             small          medium         large

 easy        hierbas        ratas gig.     goblins
 medium      puma           huargos        orcos
 hard        jabalies       skaven         waaaagh!

 out-of-table ................... vampiro (unresolvable)
```

| difficulty | size | flavour | what it means mechanically |
|---|---|---|---|
| easy | small | hierbas | trivial — solved without thought (a typo-class fix) |
| easy | medium | ratas gigantes | many, but individually dumb — volume, not danger |
| easy | large | goblins | same faction sized up — visible, not dangerous |
| medium | small | puma | one actor, serious |
| medium | medium | huargos | a pair, coordinated — the fix must land in **both services at once** |
| medium | large | orcos | same faction, escalated |
| hard | small | jabalies | a herd — each looks easy, volume kills (compounding small issues) |
| hard | medium | skaven asesino | one actor, hidden, lethal — a hard-to-find single dangerous bug |
| hard | large | waaaagh! | the full horde — same faction at max scale |

`large` reading goblins/orcos/waaaagh! is one faction at three sizes, not three unrelated
prey — it makes "how big" legible without a separate axis explaining itself.

**Vampiro** sits off the grid: impossible not because it is *big* but because it **does not
stay dead** — already "fixed" and back again. That is a recurring/regressed defect. It maps
to `outOfScope: 'recurring-defect'` on the hunter's schema and routes straight to quick-exit,
the same terminal shape as the falcon's `emergencia` and the priest's `blocked`.

## Cast

Every node is a real agent definition under `agents/`, symlinked into `~/.agents/agents/`.
The `tools:` list in each definition is the enforcement — not the prompt.

| # | Node | Phase | agentType | model | effort | tools (exact) |
|---|---|---|---|---|---|---|
| 1 | 🎯 hunter | forest | `wf-hunter` | sonnet | low | Bash, Read, Glob, Grep |
| 2 | 🦅 falcon | forest | `wf-falcon` | haiku | low | Bash |
| 3 | 🐕 hound (scout) | forest | `wf-hound` | sonnet | low | Read, Glob, Grep |
| — | 📋 the task | forest→tavern | *script* | — | — | — |
| — | 🍺 tavernkeeper | tavern | *script `if`* | — | — | — |
| 4 | 🧙 mage | tavern | `wf-mage` | fable | low | Read, Glob, Grep, **Agent** — no write, no web |
| 4a | 🦉 owl | tavern | `wf-owl` | haiku | low | WebSearch, WebFetch |
| 4b | 🐈‍⬛ cat | tavern | `wf-cat` | haiku | low | WebSearch, WebFetch |
| 4c | 🐕 hound (familiar) | tavern | `wf-hound` | haiku | low | Read, Glob, Grep |
| 4d | 🐁 mouse | tavern | `wf-mouse` | haiku | low | Read, Glob, Grep |
| 5 | ⚔️ warrior | camp | `wf-warrior` | sonnet | high | Read, Glob, Grep, Edit, Write, Bash — no web, no Agent; own worktree |
| 6 | 🏹 archer | camp | `wf-archer` | sonnet | high | Read, Glob, Grep, Edit, Write, Bash — no web, no Agent; own worktree |
| 7 | 🙏 priest | camp | `wf-priest` | haiku | low | **none** — the combined diff arrives inline in its prompt |
| 8 | 👤 shadow | stalking | `wf-shadow` | sonnet | low | **none** |
| 9 | 🎻 bard | plaza | `wf-bard` | sonnet | high | Bash |

Up to nine `agent()` calls per issue: three fixed in forest, one fixed in tavern (plus
between zero and four familiars the mage may spawn), one or two builders in camp depending
on the plan's slices, one fixed priest gate, one fixed shadow, one fixed bard. Two of the
nine roster rows are not agents at all.

### 🎯 hunter — opens the hunt

- **Input**: the issue reference (`args.issue`), optional `args.repo`.
- **Output** (`hunterSchema`): four readiness booleans, `constitutionNotes`, the issue
  number, title and body **verbatim** (downstream nodes cannot fetch it themselves),
  `domain`, `difficulty`, `size`, `outOfScope`. This object is the **triage** — the hunter's
  deliverable.
- **The one decision it owns**: whether the ground is fit to work on, the two tags everything
  downstream reads, and the `domain` the script routes on.
- **It owns the domain because it already holds the context to decide it** — the issue, the
  repo, and tools. A separate router node used to re-read the same issue with *less* context
  to produce the same label; it was deleted, not moved.
- **Its fan-out is mandatory** and lives at script level: falcon and hound always fly,
  because `parallel()` puts them there. The hunter cannot decline to be scouted for.
- **"Posting the task" is not an agent call.** It is a string the script assembles from three
  already-typed results. No judgment is needed, so no call is spent.
- **Tier note**: `low` effort, not `medium` — the paperwork this call does (tag, name a
  domain, read a constitution) does not need more, and forest is meant to be cheap.

### 🦅 falcon — the abort

- **Input**: the issue reference.
- **Output** (`falconSchema`): `severity` ∈ `limpio|hallazgo|emergencia`, `findings`.
- **The one decision it owns**: `emergencia` on a confirmed duplicate ends the run before
  the task is posted. `hallazgo` escalates and the run continues. Severity is about
  duplication, never about danger.

### 🐕 hound — the trail, dual-tier by who calls it

- **Input**: the issue text (forest, question 1) or the changed area (tavern, question 2,
  as the mage's familiar). Same agent, same schema, two questions.
- **Output** (`houndSchema`): `references[{path, lines, chunk, note, confidence}]`.
- **It returns the lines, not a coordinate.** `chunk` carries the code it read, verbatim.
  Its two sibling familiars (owl, mouse) return passages; a hound returning only a path would
  be the odd one out and would cost the mage one read per reference — the read the hound
  already did. Haiku reads, the requester receives text. That is the same economy the mouse
  exists for.
- **The one decision it owns**: which code references are worth surfacing. It owns **no
  gate**. Its confidence ceiling is `medium` by definition — it is a fast scout, not a judge.
  Its unreliability is a deliberate budgeted trade: a wrong chunk costs one read to disprove.
- **Why dual-tier**: as forest scout (#3) the script pins it to `sonnet` — it races falcon
  and the hunter under the same barrier, and a wrong chunk here costs the *hunter* a read
  before the task is even posted. As the mage's familiar (#4c) it runs at its definition's
  own default, `haiku` — cheaper ground, spawned from inside a call that is already paying
  for judgment. The pin lives in the script's forest call site (`opts.model: 'sonnet'`); the
  frontmatter default is what applies when the mage's `Agent` tool spawns it with no
  override.

### 🍺 tavernkeeper — an IF, not an agent

Owner call, 2026-07-17: *"TABERNKEEPER ES un IF."* Correct, and the diagnosis was worse than
the label suggests.

It used to be two `agent()` calls (sonnet) whose entire output was a label interpolated into
a prompt. It routed to no different agent, granted no different tools, and chose no
different model — every job downstream was going to be the mage regardless. **It was not a
router; it was a second, worse read of an issue the hunter had already read with tools in
hand.** Judgment duplicated at lower context is not a gate, it is a cost. That diagnosis
outlived the v1→v2 rewrite unchanged — the tavernkeeper hands its brief to the mage now
instead of the old hero, but the reasoning for *why it is script* did not move.

So the judgment moved to the node already paying for the context (`hunterSchema.domain`), and
what remains is what it always was:

```js
const domain = paperwork.domain;
const domainBrief = DOMAIN[domain] || 'No domain brief. Work from the task alone.';
```

The character stays: an `if` is allowed a voice, and `SAY.tavernkeeper` still speaks at the
routing step. Changing the roster is one edit to `DOMAIN`/`DOMAINS` in the script.

### 🧙 mage — the plan, and the only node with its own `Agent` tool

`wf-mage` — **fable**, `low` effort, `Read`/`Glob`/`Grep`/**`Agent`**. No `Edit`, no `Write`,
no `Bash`, no web.

- **Input**: the task, the `domain` brief, and its **posture** (derived from the tags).
- **Output** (`planSchema`): `approach`, `steps[{file, change}]`, `backendFiles`,
  `frontendFiles`, `risks`, `familiarsConsulted`.
- **The one decision it owns**: what the change should be, split along the seam the two
  builders will work on. It cannot begin making it — a plan written by someone already
  halfway through the change is a rationalisation, not a plan.
- **This is where the familiars belong.** Every lookup skipped here becomes a guess a
  builder inherits and cannot check.
- **Its fan-out is optional**, and when it happens, it happens **all at once**: the mage
  sends whichever familiars it wants in one background message, not one at a time, under a
  **10-minute watchdog**. A familiar that has not returned inside 600 seconds is abandoned —
  not waited on — and recorded as **lost** in `familiarsConsulted`, distinct from one that
  was never sent.
- **Tier is fable, not opus.** The v1 hero-plan ran opus/high for this call. The plan is a
  judgment call about scope and approach, not an execution call — this cast's answer is
  that the cheaper tier plus the familiar fan-out (which is where the real research
  happens) covers it. A plan that turns out too thin is a builder-side `deviations` finding,
  same as any other plan defect; it is not evidence the tier was wrong by itself.
- **`backendFiles` / `frontendFiles` gate the builders directly.** A builder spawns only
  when its list is non-empty — an all-backend issue never wakes the archer, and vice versa.

### The four familiars — spawned by the mage, not by the script

All haiku, all `effort: low`. They differ in **tools and question shape**, which is the
only place a reliability difference can honestly come from.

- **🦉 owl** — `WebSearch`/`WebFetch`. One named library/API → its exact citation. **Every
  search passes `allowed_domains`**, derived from the project's own canonical docs domain;
  a search without it is a defect. Quotes, never paraphrases. Returns empty rather than
  leave first-party ground. Prefers a docs MCP (context7) when present.
- **🐈‍⬛ cat** — `WebSearch`/`WebFetch`, unscoped. Open questions. `confidence` is **`low`
  structurally in its schema** — not because it searches badly, but because an open question
  has no authoritative answer. May use `blocked_domains` against SEO sludge.
- **🐕 hound** — the same agent as forest's #3, second question: where else is the changed
  area used. Returns chunks, like the other two. Runs at its haiku default here, not the
  sonnet pin forest uses — see the hound's own entry above.
- **🐁 mouse** — `Read`/`Glob`/`Grep` over the repo's docs. Cites the rules that **bind**
  this change; the mage never opens the PRD itself.
- **The falcon is not a familiar.** It belongs to the hunter and stays in forest.

### ⚔️ warrior / 🏹 archer — the builders, split by slice, not by moment

One planning node, two builders — the split v1 drew between plan and build (planner cannot
write, builder cannot research) now also runs **between the two builders**: each owns one
slice of the same plan and neither reads the other's files.

`wf-warrior` and `wf-archer` — both sonnet, `high` effort, both
`Read`/`Glob`/`Grep`/`Edit`/`Write`/`Bash`. **Neither has `Agent`, neither has web.** Each
runs in **its own worktree** — the same `isolation: 'worktree'` v1 gave the single builder,
now doubled so the two never step on each other's checkout.

- **Input**: the task and the plan, each reading only its own slice (`backendFiles` for the
  warrior, `frontendFiles` for the archer). Nothing else.
- **Output** (`buildSchema`, same shape for both): `diff`, `filesChanged`, `summary`,
  `testsRun`, `deviations`.
- **The one decision each owns**: whether its half of the plan survives contact with the
  files. A step that cannot be executed as written is a **finding** (`deviations`), never a
  silent improvement — a silent deviation makes the plan a lie and the review worthless.
- **A builder that has nothing to build does not run.** `plan.backendFiles` empty means no
  warrior call, `plan.frontendFiles` empty means no archer call. This is not a fallback path
  — it is the ordinary shape of a backend-only or frontend-only issue.
- **They run in parallel when both spawn.** Path-disjoint slices are what make that safe: the
  plan is the thing guaranteeing they never touch the same file, not a lock at run time.
- **`diff` is load-bearing, for both**: the priest and the shadow have no other way to see
  the code. The bard combines both diffs — when both exist — into the one artifact
  downstream nodes read as "the diff". Omitting or truncating either makes the gate and the
  review meaningless.

### 🙏 priest — the camp gate

`wf-priest` — haiku, `low` effort, **no tools**: the combined diff arrives inline in its
prompt, the same way the shadow receives it later. A secret scanner that goes looking in the
repo itself is a wider blast radius than one that only ever reads the diff string it was
handed — this node needs nothing else to do its job.

- **Input**: the combined diff — warrior's and archer's together, whichever ran.
- **Output** (`priestSchema`): `verdict` ∈ `clean|blocked`, `findings`.
- **The one decision it owns**: whether anything in the diff looks like a secret, key, env
  leak, or hardcoded sensitive value. Nothing else — it is not a code reviewer, that is the
  shadow's job one phase later.
- **`blocked` is terminal.** It ends the run before stalking: the shadow never sees the diff,
  the bard never gets called, nothing publishes. This is the same shape as the falcon's
  `emergencia` and the hunter's `vampiro` — a quick-exit, just gated on the build instead of
  the intake.
- **Its findings never quote the secret value itself.** A finding names the file, the line,
  and the *kind* of leak (`"hardcoded AWS key in settings.py:42"`), never the string that
  triggered it — a report that reproduces the leak to describe it would defeat the point of
  catching it.
- **Why haiku is enough here**: pattern-shaped secret detection (key formats, env-var-looking
  assignments, obvious credential shapes) does not need deep reasoning — the same argument
  that puts falcon and the familiars at haiku.

### 👤 shadow — the blind review, now its own phase

- **Phase**: `stalking` — its own step in the pipeline, not folded into camp or plaza. It
  runs after the priest clears the diff, so it is guaranteed never to review a blocked one.
- **Input**: the combined diff, inline in the prompt. **Not the plan** — judging code
  against its stated intent is the bard's job; the shadow's whole value is that it has no
  intent to judge against.
- **Output** (`shadowSchema`): `verdict` ∈ `holds|needs-work`, `findings`.
- **Tools: genuinely zero — verified empirically.** `tools: []` in an agent definition is
  granted by the runtime as an empty tool list (the registry falls back to `["*"]` only when
  `tools` is *undefined*; an empty array is truthy and survives). A probe agent declared this
  way reports `NO TOOLS AVAILABLE` and makes zero tool calls. Note the agent-type **listing**
  mislabels it as `(Tools: All tools)` — a cosmetic bug in the listing, not in the grant.
- **The one decision it owns**: whether the code stands on its own with nothing else in hand.
  This is a different gate than a guardian's: a guardian checks code against the constitution;
  the shadow checks whether it is self-sufficient **without** it. Code that only makes sense
  with the PRD open fails here regardless of any guardian verdict.
- **Tier note**: `low` effort, not `medium` — reading one diff and judging legibility does
  not need more, and the phase split makes this call cheap to re-run on its own if a plan
  edit is all that changed downstream of it.

### 🎻 bard — the terminal verdict

- **Input**: the plan, both builders' reports (whichever ran), and the shadow's report,
  together. It is the only node that sees intent and result side by side — which is what
  lets it arbitrate.
- **Output** (`bardSchema`): `hunted`, `action` ∈ `publish-pr|comment-on-issue|open-new-issue`,
  `url`, `title`, `reasoning`.
- **The one decision it owns**: hunted or not — weighing witnesses who saw different things.
  The builders' account of what they *ran* is first-hand; their account of whether the code
  is *clear* is worthless, since the author cannot un-know the intent. The shadow is the
  better witness on legibility and guessing on anything else.
- **Two-builder merge, when both ran**: the bard merges the archer's branch into the
  warrior's (their slices are path-disjoint by construction, from the mage's plan) and
  pushes once, opening **one** PR — never two PRs for one issue. A real merge conflict
  despite the disjoint plan is **not hunted**: the bard reports it honestly rather than force
  a resolution it was not asked to make.
- **Three outcomes, not two.** A failed hunt defaults to **`comment-on-issue`**: the run
  started at that issue, and that is where the next person already looks. `open-new-issue` is
  only for a finding that is a genuinely *different subject*. A new issue that merely says
  "we tried #42 and failed" orphans the knowledge from #42 — that was a defect in the first
  cut of this workflow, caught by the owner's diagram, 2026-07-17.
- **Not hunted is not failure.** What it writes is a first-class deliverable: findings, what
  almost worked and where it broke, the valuable snippets, the shadow's words verbatim. A
  one-line "did not work" is a wasted run.
- **Tier note**: `high` effort now, not `medium` — arbitrating two builders plus a shadow
  verdict, and owning the only merge/push/PR action in the whole run, is worth the higher
  tier the v1 bard did not carry.
- The only node that mutates anything outside the working tree.

## Resolved (formerly open in this file)

1. **Who spawns the familiars** — *both, differently, and the difference is the point.*
   The **hunter's fan-out is script-level** (`parallel()`): mandatory, auditable, guaranteed.
   The **mage's fan-out is mage-internal** (the `Agent` tool): optional, and when used, sent
   as one background message under a 10-minute watchdog rather than one call at a time. That
   asymmetry is not an inconsistency — it is exactly the mandatory/optional distinction the
   owner specified, expressed in the only two places the runtime offers.

2. **Splitting build by moment vs. splitting build by slice** — v1 split the hero into a
   planner and a builder (plan cannot write, build cannot research). v2 keeps that seam and
   adds a second one: the builder itself splits into warrior and archer, one per slice of
   the plan, running in parallel worktrees. The mage's `backendFiles`/`frontendFiles` fields
   are what make the split safe — path-disjoint by construction, not by a runtime lock.

3. **Why the mage runs fable/low instead of the old hero-plan's opus/high** — *because the
   research load moved to the familiars, not because planning got easier to fake.* A plan is
   a judgment call about scope and approach; on `hard`/`large` work the mage is expected to
   lean on its familiars rather than compensate with a bigger model. A thin plan is a
   builder-side `deviations` finding like any other, not proof the tier was wrong on its own.

4. **What the tavernkeeper was for** — *nothing the hunter was not already positioned to do.*
   Resolved 2026-07-17 by the owner's diagram, and it survived the hero→mage/warrior/archer
   rewrite untouched: two sonnet calls produced a label that changed a prompt string and
   nothing else — no different agent, no different tools, no different model. The judgment
   moved to `hunterSchema.domain` and the node was deleted. The lesson generalises: **a node
   that re-derives, at lower context, a judgment an upstream node was already holding is not
   a gate — it is a worse copy.**

5. **Where the secret gate belongs** — *its own node, its own phase-gate, before the review
   that has zero tools to catch it with.* The shadow's whole value is having no tools; asking
   it to also flag secrets would either grant it tools (breaking the blind-review guarantee)
   or ask it to catch a shape-based problem with no shape-based method. The priest exists
   because that is a different kind of check than "does this code stand up alone" — pattern
   matching against known leak shapes, cheap enough for haiku, and terminal on `blocked` so
   nothing downstream ever sees a leak.

6. **The tool-scoping gap** — *closed by giving the cast its own agent definitions.*
   `agent()` exposes no `tools` option, but `agentType` resolves against real definition
   files whose `tools:` list the runtime enforces. Every claim this spec makes about what a
   node can and cannot reach is now a grant, not a discipline: the shadow and priest have
   zero tools, the mage has no web, the familiars have exactly their own surface, the two
   builders have no web and no `Agent`.

7. **Why not just reuse the `orch-*` battery** — *because it cannot express these grants,
   and because it cannot express fable at all.* The battery is available machine-wide
   (symlinked into `~/.agents/agents/` since 2026-07-05), so portability is **not** the
   reason; the reason is tool scope plus model choice. `orch-low` carries
   Read+Glob+Grep+WebFetch+WebSearch as one profile, which cannot distinguish owl (web only)
   from mouse (docs only) from hound (code only). No `orch-*` entry is tool-less, so the
   shadow and priest are unbuildable on it, and the machine-wide roster does not offer fable
   as a tier at all. The `wf-*` cast exists to make those grants real, and for no other
   reason.

8. **The v1 model-pinning bug** — *nodes silently inherited the session's model when a call
   site omitted `model`/`effort`, so a scout could fire as opus.* Fixed by making every call
   site in the script pin both explicitly; `validate.mjs` is the mechanical check that a new
   call cannot land without them.

## Still open

- **Whether the shadow's `needs-work` can loop back to a builder for a retry.** Today it does
  not: the bard arbitrates once and publishes. A retry loop would need a hard iteration cap
  (the runtime has an `agent()` call cap that a `budget.remaining()` loop can blow through).
  Unbuilt on purpose, and cheap to add if wanted.
- **Whether the priest's `blocked` verdict can be appealed or overridden.** Today it cannot:
  `blocked` is unconditionally terminal. A false positive means re-running from tavern with a
  plan that avoids the pattern that tripped it, not a bypass flag.
- **The falcon's extra verification round** — still a suggestion, still unsettled.
- **Everything after the bard's publish** — guardian dispatch, a verifier, a human
  smoke-test pause — is out of scope here. The bard is the last node this spec defines.
- **The specialist roster is this template's.** `django-expert | frontend-expert |
  styles-expert | quick-fix-expert | scripts-expert` fits an Astro+DRF repo. A different repo
  edits `DOMAIN` and `DOMAINS` in the script; nothing else moves. Since the tavernkeeper is
  an `if`, the roster is data, not a node's enum — and the hunter's `domain` field reads its
  members from the same array.
