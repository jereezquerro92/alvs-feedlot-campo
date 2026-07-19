export const meta = {
  name: 'triage-and-fix',
  description: 'Takes one issue from triage to a published PR, an issue comment, or a new issue. Deterministic across five phases: three scouts read the ground in parallel (forest); a plan-only mage routes on domain and splits the work into a backend slice and a frontend slice, spawning its own familiars (tavern); two builders build those slices in parallel, each in its own worktree, behind a blocking secret-scan gate (camp); a tool-less reviewer judges the combined diff (stalking); a single bard weighs the witnesses and publishes one artifact (plaza).',
  whenToUse: 'When an issue should be taken end to end by the party: verified and scouted (forest), planned and routed (tavern), built in parallel backend/frontend slices behind a security gate (camp), reviewed blind (stalking), and published (plaza). Pass args {issues, repo} or {issue, repo}.',
  phases: ['forest', 'tavern', 'camp', 'stalking', 'plaza'],
};

// ---------------------------------------------------------------------------
// Shared context. Every agent starts with zero context and the script has no
// filesystem, so the party sheet is inlined here and prepended to every prompt.
// Mirrors team-party.md, which is the SSOT for humans.
// ---------------------------------------------------------------------------

const TEAM_PARTY = `# team-party.md

You are one node in **triage-and-fix**: a deterministic workflow that takes one issue
and ends with a pull request, a comment on that issue, or a new issue. Read your place,
do your part, return your schema. Nothing else.

## The party, in order

1. hunter (target) - reads the issue, checks the ground is fit to work on, tags difficulty x
   size, and names the domain. Its deliverable is the triage. (forest)
2. falcon (bird) - parallel with hunter. GitHub only: duplicate or regression? Owns the abort. (forest)
3. hound (dog) - parallel with hunter. Code only: which files does this touch? Brings the
   actual lines back, not just paths. Candidates, not conclusions. (forest)
-  the task - the script, not an agent, assembles 1+2+3 into one posting. No judgment is
   needed to concatenate typed results, so no agent is spent on it.
-  the tavernkeeper (beer) - an IF in the script, not an agent. It routes on the hunter's
   domain. It used to be a node; it was re-reading the same issue with less context to reach
   a label the hunter already had.
4. mage (wizard) - turns the task into an explicit plan and splits it into a backend slice and
   a frontend slice. Cannot write code. Its familiars are its OWN: it spawns them in one message,
   budgets them ten minutes, and abandons and records any that do not return. The script never
   witnesses them. (tavern)
4a. owl - the mage's familiar. One named API/library -> its exact citation, official docs only.
4b. cat - the mage's familiar. Open question -> whatever it finds, at low trust.
4c. hound - the mage's familiar. The same trade as node 3, asked again: where else is the changed area used?
4d. mouse - the mage's familiar. Reads the project's own docs and cites what binds this change.
5. warrior (crossed-swords) - the BACKEND builder. Wakes only if the plan named backend files.
   Works in its own isolated worktree, commits its slice on its own branch, returns the real diff. (camp)
6. archer (bow) - the FRONTEND builder. Wakes only if the plan named frontend files. Its own
   worktree, its own branch, its own diff, in parallel with the warrior. (camp)
7. priest (pray) - the gate. Scans the combined diff for secrets, keys, leaked env values and
   hardcoded sensitive data. Reports location and kind, never the value. A single find blocks
   the run: nothing downstream runs and nothing is published. (camp)
8. shadow - reviews the combined diff with NO tools at all. Judges one thing: does this code
   stand up with nothing else in hand? (stalking)
9. bard - weighs the builders against the shadow. Hunted -> if two branches exist, merges the
   path-disjoint slices, pushes once, opens ONE PR; one branch -> pushes and opens ONE PR.
   Not hunted -> comments on the issue, or opens a new one when the finding is a different
   subject. Nothing committed -> a PR is impossible, so it comments. All are deliverables. (plaza)

## Two rules that bind every node

1. **Your schema is your only output.** A node's prose is never read by another node.
2. **The flavour is a render, never an input.** Names, animals, prey and the party's spoken
   lines exist so a human can read the run. They are a closed set, written in advance, and
   printed by the script - you are never asked to produce one. No node ever changes what it
   does because of them. If your decision would differ after removing every animal from this
   file, you have a defect.

## The tags

difficulty in (easy | medium | hard), size in (small | medium | large). Hunter sets them
once; downstream reads them as machine values. Their prey names are printed for humans and
never parsed.
`;

// ---------------------------------------------------------------------------
// The voice of the party: a closed set, fixed in advance, printed by the script
// at stage transitions. Nothing here is generated at run time, and no node ever
// reads one. Strip this table and every outcome is byte-identical.
// The tavernkeeper still speaks: it is an IF now, and an IF is allowed a voice.
// The familiars' lines live only in their agent definitions: the mage spawns
// them itself, so the script never witnesses those transitions.
// These lines are the one sanctioned place for Spanish; everything else the
// script emits — logs, comments, prompts — is English.
// ---------------------------------------------------------------------------

const SAY = {
  hunter: ['🎯', 'hunter', 'A ver qué bicho tenemos hoy.'],
  falcon: ['🦅', 'falcon', 'Doy una vuelta sobre el terreno.'],
  hound: ['🐕', 'hound', 'Tengo el rastro.'],
  task: ['📋', 'tablón', 'Queda clavado en el tablón.'],
  tavernkeeper: ['🍺', 'tavernkeeper', 'Para esto tengo a alguien.'],
  mage: ['🧙', 'mage', 'Las runas me dirán el camino.'],
  warrior: ['⚔️', 'warrior', 'El backend es mío.'],
  archer: ['🏹', 'archer', 'Yo cubro el frente.'],
  priest: ['🙏', 'priest', 'Que nada impuro pase.'],
  priestBlock: ['🙏', 'priest', '¡Alto! Esto no debe ver la luz.'],
  shadow: ['👤', 'shadow', 'Mostrámelo. Sin explicarlo.'],
  bardHappy: ['🎻', 'bard', 'Y así, la fiera cayó. Cantemos.'],
  bardSad: ['🎻', 'bard', 'No la cazamos, pero volvemos con el mapa.'],
  vampire: ['🧛', 'the party', 'Este no se queda muerto. No es para nosotros.'],
  duplicate: ['🦅', 'falcon', 'Ya está cazado. Volvemos.'],
  unfit: ['🎯', 'hunter', 'El terreno no está para cazar.'],
  lost: ['💀', 'the party', 'Uno no volvió. Se levanta el campamento.'],
};

function say(key) {
  const line = SAY[key];
  if (line) log(line[0] + ' ' + line[1] + ': "' + line[2] + '"');
}

// ---------------------------------------------------------------------------
// The closed specialist enum, and what the tavernkeeper-IF hands the mage for
// each. Changing the roster is an edit here and nowhere else.
// ---------------------------------------------------------------------------

const DOMAIN = {
  'django-expert': 'Django 6 + DRF. Models, viewsets, serializers, migrations, permissions. Every route answers to the API contract.',
  'frontend-expert': 'Astro SSR + Svelte islands. Components, routing, hydration, HTMX before a Svelte island.',
  'styles-expert': 'Tailwind, design tokens, theming. Every visual value is a token; light and dark always.',
  'quick-fix-expert': 'A small, contained defect. Change the least that fixes the cause.',
  'scripts-expert': 'Tooling, harness, CI, hooks. Python over bash; uv, not pip.',
};

const DOMAINS = ['django-expert', 'frontend-expert', 'styles-expert', 'quick-fix-expert', 'scripts-expert'];

// ---------------------------------------------------------------------------
// Schemas. Each is closed: the agent uses judgment and tools to fill the fields,
// but cannot escape the shape it must answer in. The determinism lives here and
// in the script's branching on the typed result — never in the prose.
// ---------------------------------------------------------------------------

const hunterSchema = {
  type: 'object',
  properties: {
    stackDepsOk: { type: 'boolean', description: 'Toolchain present and the repo is workable right now.' },
    ghConnected: { type: 'boolean', description: 'gh auth status passes and the repo resolves.' },
    issueMatchesTemplate: { type: 'boolean', description: 'True when the repo declares no template.' },
    constitutionOk: { type: 'boolean', description: 'False only when a written rule forbids what the issue asks.' },
    constitutionNotes: { type: 'string', description: 'Cite file and rule. One clause when nothing forbids it.' },
    issueNumber: { type: 'string', description: 'The issue number alone, for the bard to comment on. Empty if the task did not come from a real issue.' },
    issueTitle: { type: 'string' },
    issueBody: { type: 'string', description: 'The issue text as fetched, verbatim, for downstream nodes.' },
    domain: { type: 'string', enum: DOMAINS, description: 'The specialist domain. The script routes on this — there is no router node.' },
    difficulty: { type: 'string', enum: ['easy', 'medium', 'hard'] },
    size: { type: 'string', enum: ['small', 'medium', 'large'] },
    outOfScope: { type: 'string', enum: ['recurring-defect', 'none'], description: 'none unless the evidence shows this exact defect was already fixed and came back.' },
  },
  required: ['stackDepsOk', 'ghConnected', 'issueMatchesTemplate', 'constitutionOk', 'issueNumber', 'issueTitle', 'issueBody', 'domain', 'difficulty', 'size', 'outOfScope'],
  additionalProperties: false,
};

const falconSchema = {
  type: 'object',
  properties: {
    severity: { type: 'string', enum: ['limpio', 'hallazgo', 'emergencia'] },
    findings: { type: 'array', items: { type: 'string' }, description: 'One line each, with the issue/PR number. May be empty.' },
  },
  required: ['severity', 'findings'],
  additionalProperties: false,
};

// The hound returns the lines, not just a coordinate. Its two sibling familiars
// (owl, mouse) return passages; a pointer would make it the odd one out and cost
// the mage a read per reference — the read the hound already did.
const houndSchema = {
  type: 'object',
  properties: {
    references: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          path: { type: 'string' },
          lines: { type: 'string', description: 'The line range you read, e.g. 40-72.' },
          chunk: { type: 'string', description: 'The actual lines, verbatim. Enough that the code stands on its own.' },
          note: { type: 'string', description: 'What this is and why you brought it. Say if it is a comment, a fixture, or vendored.' },
          confidence: { type: 'string', enum: ['low', 'medium'] },
        },
        required: ['path', 'lines', 'chunk', 'note', 'confidence'],
        additionalProperties: false,
      },
    },
  },
  required: ['references'],
  additionalProperties: false,
};

// The plan splits the work by construction: backendFiles and frontendFiles are
// the two slices the camp reads to decide which builder wakes. Either may be
// empty; both empty means there is nothing to build and the run ends at the camp.
const planSchema = {
  type: 'object',
  properties: {
    approach: { type: 'string', description: 'What the change is and why this way. Name the familiar whose answer decided it — a builder cannot ask.' },
    steps: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          file: { type: 'string' },
          change: { type: 'string', description: 'What changes here, concretely enough to execute without rediscovery.' },
        },
        required: ['file', 'change'],
        additionalProperties: false,
      },
    },
    backendFiles: { type: 'array', items: { type: 'string' }, description: 'Exact, verified paths under backend/ (or a repo-level backend concern). Empty is valid. A non-empty list wakes the warrior.' },
    frontendFiles: { type: 'array', items: { type: 'string' }, description: 'Exact, verified paths under frontend/. Empty is valid. A non-empty list wakes the archer.' },
    risks: { type: 'string', description: 'What could break that the diff will not show. The shadow never sees this; the bard leans on it.' },
    familiarsConsulted: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          familiar: { type: 'string', enum: ['owl', 'cat', 'hound', 'mouse'] },
          used: { type: 'boolean', description: 'Whether its answer changed the plan.' },
          note: { type: 'string', description: 'What it returned. Record a familiar you abandoned as \'lost: 10-minute budget exceeded\'.' },
        },
        required: ['familiar', 'used'],
        additionalProperties: false,
      },
      description: 'Empty is valid and often correct: no familiar is owed a call.',
    },
  },
  required: ['approach', 'steps', 'backendFiles', 'frontendFiles', 'risks', 'familiarsConsulted'],
  additionalProperties: false,
};

// One build schema, reused by both builders. A builder fills it from inside its
// own worktree; nothing here assumes which slice it built.
const buildSchema = {
  type: 'object',
  properties: {
    diff: { type: 'string', description: 'The real, complete change. The shadow has no tools; this string is the only way the code is ever seen.' },
    filesChanged: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string', description: 'What changed and why. Report failing tests honestly.' },
    testsRun: { type: 'string', description: 'What was actually run and its outcome. Empty when nothing was run.' },
    deviations: { type: 'string', description: 'Where you departed from the plan and why. Empty when you built it as written.' },
    // Reported by the builder itself, read from its own cwd — never assumed from the
    // runtime. isolation:'worktree' is documented to return the path and branch, but
    // that is unverified alongside a schema-forced return, and the bard cannot push a
    // branch it cannot name. Asking the one node that is standing in the worktree is
    // the answer that does not depend on plumbing we have not tested.
    worktreePath: { type: 'string', description: 'Absolute path of the worktree you worked in (your cwd). Empty if you are not in one.' },
    branch: { type: 'string', description: 'The branch your commit is on. Empty if you did not commit.' },
    committed: { type: 'boolean', description: 'True only if your change is committed on that branch. The bard can publish nothing otherwise.' },
  },
  required: ['diff', 'filesChanged', 'summary', 'testsRun', 'deviations', 'worktreePath', 'branch', 'committed'],
  additionalProperties: false,
};

// The gate. Its verdict alone decides whether anything reaches the shadow, so
// its shape is deliberately minimal: a binary verdict and located, kind-tagged
// findings that never carry the sensitive value itself.
const priestSchema = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['clean', 'blocked'], description: 'clean lets the run continue; blocked ends it — nothing is published.' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          where: { type: 'string', description: 'Where it is: path and hunk locator only. NEVER the sensitive value itself.' },
          kind: { type: 'string', enum: ['secret-key', 'credential', 'env-leak', 'hardcoded-config', 'sensitive-data', 'other'] },
          note: { type: 'string', description: 'Why it must not ship, in the abstract. Do not reproduce the value.' },
        },
        required: ['where', 'kind', 'note'],
        additionalProperties: false,
      },
      description: 'Empty when clean. One entry is enough to block.',
    },
  },
  required: ['verdict', 'findings'],
  additionalProperties: false,
};

const shadowSchema = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['holds', 'needs-work'] },
    findings: { type: 'array', items: { type: 'string' }, description: 'Specific, quoting the line each is about.' },
  },
  required: ['verdict', 'findings'],
  additionalProperties: false,
};

const bardSchema = {
  type: 'object',
  properties: {
    hunted: { type: 'boolean' },
    action: { type: 'string', enum: ['publish-pr', 'comment-on-issue', 'open-new-issue'], description: 'comment-on-issue is the default for a failed hunt; a new issue only for a genuinely different subject.' },
    url: { type: 'string', description: 'The URL of what you actually published.' },
    title: { type: 'string' },
    reasoning: { type: 'string', description: 'Why hunted or not, weighing both witnesses.' },
  },
  required: ['hunted', 'action', 'url', 'title', 'reasoning'],
  additionalProperties: false,
};

// ---------------------------------------------------------------------------
// Render helpers. Everything here is printed for humans and read by no node.
// The prey name is derived from the tags AFTER every decision is made, and
// never travels back into a prompt or a schema.
// ---------------------------------------------------------------------------

const PREY = {
  'easy:small': 'hierbas',
  'easy:medium': 'ratas gigantes',
  'easy:large': 'goblins',
  'medium:small': 'puma',
  'medium:medium': 'huargos',
  'medium:large': 'orcos',
  'hard:small': 'jabalies',
  'hard:medium': 'skaven asesino',
  'hard:large': 'waaaagh!',
};

function preyName(difficulty, size) {
  return PREY[difficulty + ':' + size] || 'bicho sin nombre';
}

function briefing(role) {
  return TEAM_PARTY + '\n\n---\n\nYou are **' + role + '**. Everything you need is below; you have no memory of any other run.\n\n';
}

// Renders the plan. With a `files` slice it renders only the steps that touch
// those files and lists only that slice — this is how each builder sees ITS half
// and nothing more. Called with no slice, it renders the whole plan (both slices
// combined) for the bard, who weighs the change as a whole.
function renderPlan(plan, files) {
  const allFiles = files || plan.backendFiles.concat(plan.frontendFiles);
  const steps = files ? plan.steps.filter((s) => files.includes(s.file)) : plan.steps;
  return '### Approach\n\n' + plan.approach + '\n\n### Steps\n\n' +
    (steps.length ? steps.map((s, i) => (i + 1) + '. `' + s.file + '` — ' + s.change).join('\n') : '_no steps for this slice_') +
    '\n\n### Files\n\n' + (allFiles.length ? allFiles.map((f) => '- `' + f + '`').join('\n') : '_none_') +
    '\n\n### Risks\n\n' + plan.risks + '\n';
}

// One builder's account, for the bard. Read by no other node.
function renderBuilderAccount(role, slice, r) {
  return '### ' + role + ' (' + slice + ')\n\n' + r.summary +
    '\n\nTests run: ' + (r.testsRun || 'none reported') +
    '\n\nDeviations: ' + (r.deviations || 'none') +
    '\n\nFiles: ' + (r.filesChanged || []).join(', ') + '\n';
}

// The worktree/commit doctrine, identical for both builders. Each works in its
// own isolated worktree — the only nodes granted Edit/Write/Bash — so without it
// a builder would edit whatever checkout the run was launched from, which on this
// machine is a checkout shared with live sessions.
const worktreeDoctrine = '\n\nYou are in an isolated worktree of your own. Commit your change there on its own branch, then report your cwd as `worktreePath`, the branch as `branch`, and set `committed`. Nothing downstream can publish work you left uncommitted.';

// ---------------------------------------------------------------------------
// The run.
// ---------------------------------------------------------------------------

// One issue, start to finish. Everything below is per-issue: the early exits are
// returns from THIS function, so a vampiro on issue #42 ends #42 and nothing else.
async function runOne(issueRef, repoHint) {

phase('forest');
log('The party takes an issue: ' + issueRef);
say('hunter');
say('falcon');
say('hound');

// The hunter's fan-out is mandatory and lives here, at script level: falcon and
// hound always fly. The mage's fan-out is optional and lives inside the mage.
const [paperwork, falconR, houndR] = await parallel([
  () => agent(
    briefing('hunter') +
    'Take the hunt for this issue: ' + issueRef + repoHint +
    '\nFetch the issue with gh, then run your four checks against real evidence, name the domain, and tag the work. ' +
    'Return the issue number, title and body verbatim in your schema — the nodes after you cannot fetch it themselves.',
    { label: 'hunter', phase: 'forest', agentType: 'wf-hunter', model: 'sonnet', effort: 'low', schema: hunterSchema },
  ),
  () => agent(
    briefing('falcon') +
    'Fly over this issue: ' + issueRef + repoHint +
    '\nGitHub only. Has this already been dealt with? Open what you find before you call it a match.',
    { label: 'falcon', phase: 'forest', agentType: 'wf-falcon', model: 'haiku', effort: 'low', schema: falconSchema },
  ),
  () => agent(
    briefing('hound') +
    'You are asked the SCOUTING question: this issue is about — ' + issueRef + repoHint +
    '\nWhich code does it touch? Read what you find and bring the lines back in `chunk`. Empty is a valid answer.',
    { label: 'hound', phase: 'forest', agentType: 'wf-hound', model: 'sonnet', effort: 'low', schema: houndSchema },
  ),
]);

if (!paperwork) {
  say('lost');
  return { status: 'aborted', reason: 'hunter-failed' };
}

const prey = preyName(paperwork.difficulty, paperwork.size);
log('Prey: ' + prey + ' (' + paperwork.difficulty + ' × ' + paperwork.size + ')');

if (paperwork.outOfScope === 'recurring-defect') {
  say('vampire');
  return { status: 'quick-exit', reason: 'recurring-defect', prey: 'vampiro', paperwork: paperwork };
}

if (falconR && falconR.severity === 'emergencia') {
  say('duplicate');
  return { status: 'quick-exit', reason: 'duplicate', findings: falconR.findings, paperwork: paperwork };
}

if (!paperwork.stackDepsOk || !paperwork.ghConnected || !paperwork.constitutionOk) {
  say('unfit');
  return { status: 'quick-exit', reason: 'ground-unfit', paperwork: paperwork };
}

// The task is pure script assembly: a string built from three already-typed
// results. No judgment is needed to concatenate them, so no agent call is spent.
const task = '## The issue\n\n**' + paperwork.issueTitle + '**\n\n' + paperwork.issueBody + '\n' +
  '\n## What the hunter found\n\n' +
  '- difficulty: ' + paperwork.difficulty + '\n' +
  '- size: ' + paperwork.size + '\n' +
  '- constitution: ' + (paperwork.constitutionNotes || 'nothing found forbidding it') + '\n' +
  '\n## What the falcon found\n\n' +
  ((falconR && falconR.findings.length) ? falconR.findings.map((f) => '- ' + f).join('\n') : '- nothing') + '\n' +
  '\n## What the hound found\n\n' +
  ((houndR && houndR.references.length)
    ? houndR.references.map((r) =>
        '### `' + r.path + '` lines ' + r.lines + ' (' + r.confidence + ')\n' + r.note +
        '\n\n```\n' + r.chunk + '\n```\n').join('\n')
    : '- no trail') + '\n';

say('task');

phase('tavern');

// The tavernkeeper is an IF, not an agent. It used to be an `agent()` call whose
// entire output was a label interpolated into the mage's prompt — a second, worse
// read of the issue the hunter had already read with tools in hand. The judgment
// stayed; it moved into the node that was already paying for the context.
say('tavernkeeper');
const domain = paperwork.domain;
const domainBrief = DOMAIN[domain] || 'No domain brief. Work from the task alone.';
log('Domain: ' + domain);

// difficulty × size choose the mage's delegation appetite — never its model tier.
// The mage's tier is pinned in its agent() call below; what the tags buy is how
// many familiars it is worth spawning before it commits to an approach.
const posture = (paperwork.difficulty === 'hard' || paperwork.size === 'large')
  ? 'This is ' + paperwork.difficulty + ' × ' + paperwork.size + '. Send familiars before you commit to an approach — guessing here is expensive.'
  : 'This is ' + paperwork.difficulty + ' × ' + paperwork.size + '. You may well not need anyone: if you can already see the fix in the chunks the hound brought, plan it. Send a familiar only where you would otherwise be guessing.';

say('mage');

const plan = await agent(
  briefing('mage, the ' + domain) +
  'You have been named for this work. Your domain: ' + domainBrief + '\n\n' + task +
  '\n## Your posture\n\n' + posture +
  '\n\n## Your familiars\n\nYou cannot write code and you have no web or docs access of your own. Your familiars are yours: spawn them with the Agent tool in one message, budget ten minutes total, and abandon and record any that do not return in time (in `familiarsConsulted`, note \'lost: 10-minute budget exceeded\'). The doctrine lives in your definition; this is the roster:\n' +
  '- `wf-owl` — one named library/API → its exact citation\n' +
  '- `wf-cat` — an open question, low trust\n' +
  '- `wf-hound` — where else the area you will change is used\n' +
  '- `wf-mouse` — which of this project\'s written rules bind this change\n' +
  '\n## Your plan splits the work\n\nName every file you will change under `backendFiles` (exact, verified paths under `backend/` or a repo-level backend concern) or `frontendFiles` (exact, verified paths under `frontend/`). Either array may be empty. The camp reads these to decide who builds: a non-empty `backendFiles` wakes the warrior, a non-empty `frontendFiles` wakes the archer, and both empty ends the hunt. Keep the two slices path-disjoint. The builders get the plan and nothing else — they cannot research, and they cannot ask you.',
  { label: 'mage', phase: 'tavern', agentType: 'wf-mage', model: 'fable', effort: 'low', schema: planSchema },
);

if (!plan) {
  say('lost');
  return { status: 'aborted', reason: 'plan-failed', task: task, prey: prey };
}

const sent = plan.familiarsConsulted || [];
log(sent.length ? 'Familiars sent: ' + sent.map((f) => f.familiar).join(', ') : 'Familiars sent: none');

phase('camp');

// Conditional parallel builders. Each slice of the plan wakes at most one builder;
// a builder that is not needed resolves null through its thunk and costs nothing.
// The slices are path-disjoint by the mage's contract (backend/ vs frontend/), so
// the two worktrees never touch the same file and the bard can merge them cleanly.
const needBackend = plan.backendFiles.length > 0;
const needFrontend = plan.frontendFiles.length > 0;

if (!needBackend && !needFrontend) {
  // Nothing to build. This is not a failure to publish — the mage may have found
  // the issue needs no code — but there is no diff, so the run ends here.
  say('lost');
  return { status: 'aborted', reason: 'empty-plan', task: task, plan: plan, prey: prey };
}

log('Camp: ' + [needBackend ? 'warrior (backend)' : '', needFrontend ? 'archer (frontend)' : ''].filter(Boolean).join(' + '));
if (needBackend) say('warrior');
if (needFrontend) say('archer');

// isolation:'worktree' is not optional for a builder: it is the only kind of node
// with Edit/Write/Bash. The skipped builder's thunk resolves null.
const [warriorR, archerR] = await parallel([
  () => (needBackend
    ? agent(
        briefing('warrior') +
        'The mage planned this; you build the BACKEND slice and nothing else. You do not remember the plan being written, and the frontend is not yours.\n\n' + task +
        '\n## The plan — your slice\n\n' + renderPlan(plan, plan.backendFiles) +
        '\nBuild only the files above. Follow the steps in order; where the plan is wrong, implement what is right and record the departure in `deviations` — never silently improve it. Return the real, complete diff.' +
        worktreeDoctrine,
        { label: 'warrior', phase: 'camp', agentType: 'wf-warrior', model: 'sonnet', effort: 'high', isolation: 'worktree', schema: buildSchema },
      )
    : null),
  () => (needFrontend
    ? agent(
        briefing('archer') +
        'The mage planned this; you build the FRONTEND slice and nothing else. You do not remember the plan being written, and the backend is not yours.\n\n' + task +
        '\n## The plan — your slice\n\n' + renderPlan(plan, plan.frontendFiles) +
        '\nBuild only the files above. Follow the steps in order; where the plan is wrong, implement what is right and record the departure in `deviations` — never silently improve it. Return the real, complete diff.' +
        worktreeDoctrine,
        { label: 'archer', phase: 'camp', agentType: 'wf-archer', model: 'sonnet', effort: 'high', isolation: 'worktree', schema: buildSchema },
      )
    : null),
]);

// A builder that was asked to build and returned nothing is a failed build. A
// builder that was never asked (its slice was empty) is legitimately null.
if (needBackend && !warriorR) {
  say('lost');
  return { status: 'aborted', reason: 'build-failed', which: 'warrior', task: task, plan: plan, prey: prey };
}
if (needFrontend && !archerR) {
  say('lost');
  return { status: 'aborted', reason: 'build-failed', which: 'archer', task: task, plan: plan, prey: prey };
}

if (warriorR && warriorR.deviations) log('Warrior deviations: ' + warriorR.deviations);
if (archerR && archerR.deviations) log('Archer deviations: ' + archerR.deviations);

// The combined diff: labelled concatenation of whichever builders ran. This one
// string is the only thing the priest and the shadow ever see of the code.
const combinedParts = [];
if (warriorR) combinedParts.push('### warrior (backend)\n' + warriorR.diff);
if (archerR) combinedParts.push('### archer (frontend)\n' + archerR.diff);
const combinedDiff = combinedParts.join('\n\n');

// The gate, still inside the camp. It runs before anything is reviewed or
// published; a `blocked` verdict ends the run and nothing reaches the plaza.
say('priest');
const priestR = await agent(
  briefing('priest') +
  'Here is the combined diff of everything the builders produced — a backend slice, a frontend slice, or both, each labelled. Scan it for anything that must never enter version control: secret keys, credentials, tokens, leaked environment values, hardcoded configuration that belongs in a secret store, or other sensitive data.\n\n' +
  'Report location and kind ONLY. NEVER quote or reproduce the sensitive value itself — naming where it sits (`where`) and what kind it is (`kind`) is the whole job, and copying the value would leak it a second time into this record. A clean, located finding is worth more than a copied secret.\n\n' +
  'Find nothing that must be withheld → verdict `clean`. Find even one thing that must not see the light → verdict `blocked`: the run ends at the camp and nothing is published.\n\n```diff\n' + combinedDiff + '\n```\n',
  { label: 'priest', phase: 'camp', agentType: 'wf-priest', model: 'haiku', effort: 'low', schema: priestSchema },
);

if (!priestR) {
  // The gate itself failed. A gate that cannot render a verdict cannot clear the
  // diff, so the safe reading is to stop — nothing unreviewed reaches the plaza.
  say('lost');
  return { status: 'aborted', reason: 'gate-failed', task: task, plan: plan, prey: prey };
}

log('Gate: ' + priestR.verdict);

if (priestR.verdict === 'blocked') {
  say('priestBlock');
  return { status: 'blocked', reason: 'priest-blocked', findings: priestR.findings, prey: prey, paperwork: paperwork };
}

phase('stalking');
say('shadow');

// wf-shadow is declared `tools: []`, which the runtime grants as genuinely zero
// tools. The combined diff below is the only way the code ever reaches it. It
// never sees the plan: judging the code against its intent is the bard's job.
const shadowR = await agent(
  briefing('shadow') +
  'Here is a diff — it may combine a backend slice and a frontend slice, each labelled. You have no tools: you cannot open a file, and you will see nothing else of this project.\n\n' +
  'Answer one question — does this code stand up with nothing else in hand?\n\n```diff\n' + combinedDiff + '\n```\n',
  { label: 'shadow', phase: 'stalking', agentType: 'wf-shadow', model: 'sonnet', effort: 'low', schema: shadowSchema },
);

if (!shadowR) {
  say('lost');
  return { status: 'aborted', reason: 'review-failed', plan: plan, prey: prey };
}

log('Verdict: ' + shadowR.verdict);

phase('plaza');

// Where the committed code actually lives, computed for the bard: zero, one, or
// two branches. Two branches are path-disjoint by construction, so they merge;
// zero committed means a PR is impossible and the bard comments instead.
const committedBuilders = [];
if (warriorR && warriorR.committed) committedBuilders.push({ role: 'warrior', slice: 'backend', branch: warriorR.branch, path: warriorR.worktreePath });
if (archerR && archerR.committed) committedBuilders.push({ role: 'archer', slice: 'frontend', branch: archerR.branch, path: archerR.worktreePath });

let whereTheCode;
if (committedBuilders.length === 0) {
  whereTheCode = 'NOTHING IS COMMITTED. No builder left a commit, so there is no branch to publish. ' +
    'A PR is impossible here regardless of the verdict — say so plainly and record the work as a comment instead.';
} else if (committedBuilders.length === 1) {
  const b = committedBuilders[0];
  whereTheCode = 'One branch: `' + b.branch + '` (' + b.slice + '), committed in the worktree at `' + b.path + '`. ' +
    'To publish you must push that branch from that path first — it exists on neither the remote nor the main checkout. Then open ONE PR from it.';
} else {
  const first = committedBuilders[0];
  const second = committedBuilders[1];
  whereTheCode = 'Two branches, each in its own worktree:\n' +
    '- `' + first.branch + '` (' + first.slice + ') at `' + first.path + '`\n' +
    '- `' + second.branch + '` (' + second.slice + ') at `' + second.path + '`\n' +
    'Their file slices are path-disjoint by construction (backend/ vs frontend/), so they merge without conflict. ' +
    'Merge `' + second.branch + '` into `' + first.branch + '`, push `' + first.branch + '` once, and open exactly ONE PR from it. ' +
    'If a real merge conflict appears, the slices were not disjoint after all — that is not a clean hunt: report it honestly rather than forcing the merge.';
}

const builderAccounts = [
  warriorR ? renderBuilderAccount('warrior', 'backend', warriorR) : '',
  archerR ? renderBuilderAccount('archer', 'frontend', archerR) : '',
].filter(Boolean).join('\n');

const verdict = await agent(
  briefing('bard') +
  'Accounts of the same code — from the builders and from the shadow. Weigh them, decide hunted or not, and publish exactly one artifact.' + repoHint +
  '\n\n## The issue\n\n#' + (paperwork.issueNumber || '?') + ' — ' + paperwork.issueTitle + '\n' +
  '\n## The plan that was made\n\n' + renderPlan(plan) +
  '\n## The builders\' accounts\n\n' + builderAccounts +
  '\n```diff\n' + combinedDiff + '\n```\n' +
  '\n## The shadow\'s account\n\nVerdict: ' + shadowR.verdict + '\n' +
  (shadowR.findings.length ? shadowR.findings.map((f) => '- ' + f).join('\n') : '- no findings') + '\n' +
  '\n## The gate\n\nThe priest returned `' + priestR.verdict + '` — the run reached you, so the diff carried nothing that must be withheld.\n' +
  '\n## Where the code is\n\n' + whereTheCode + '\n' +
  '\nHunted → publish per the branches above and open exactly ONE PR. Not hunted → comment on issue #' + (paperwork.issueNumber || '?') +
  ', unless the attempt found a genuinely different subject, which is a new issue. Make it worth reading.',
  { label: 'bard', phase: 'plaza', agentType: 'wf-bard', model: 'sonnet', effort: 'high', schema: bardSchema },
);

if (!verdict) {
  say('lost');
  return { status: 'aborted', reason: 'publish-failed', plan: plan, shadowR: shadowR, prey: prey };
}

say(verdict.hunted ? 'bardHappy' : 'bardSad');
log(verdict.url);

const filesChanged = [].concat(
  warriorR ? (warriorR.filesChanged || []) : [],
  archerR ? (archerR.filesChanged || []) : [],
);
const deviations = [
  warriorR && warriorR.deviations ? 'warrior: ' + warriorR.deviations : '',
  archerR && archerR.deviations ? 'archer: ' + archerR.deviations : '',
].filter(Boolean).join(' | ');

return {
  status: 'completed',
  hunted: verdict.hunted,
  action: verdict.action,
  url: verdict.url,
  prey: prey,
  difficulty: paperwork.difficulty,
  size: paperwork.size,
  domain: domain,
  shadowVerdict: shadowR.verdict,
  priestVerdict: priestR.verdict,
  familiarsConsulted: sent.map((f) => f.familiar),
  filesChanged: filesChanged,
  deviations: deviations,
  builders: {
    warrior: warriorR ? { branch: warriorR.branch, committed: warriorR.committed } : null,
    archer: archerR ? { branch: archerR.branch, committed: archerR.committed } : null,
  },
  reasoning: verdict.reasoning,
};

}

// ---------------------------------------------------------------------------
// The party takes its issues one at a time.
//
// Sequential on purpose, and pipeline() is deliberately NOT used here. pipeline has
// no barrier between stages, so N issues would have N camps building at once — each
// builder in its own worktree, so it is safe, but the cost lands all at once and an
// abort mid-flight leaves N half-hunts. A plain for-of costs one issue at a time and
// is stoppable at any point. The array is the bound: this loop terminates because the
// list is finite, never because a budget ran out.
//
// The list is the CALLER's. The script has no shell, so it cannot run `gh issue list`
// itself — and it should not: a party that picks its own work is a party with no
// owner. Pass args.issues; args.issue still works for one.
// ---------------------------------------------------------------------------

const issues = (args && args.issues) || [(args && args.issue) || args];
const repoHint = args && args.repo ? '\nRepository: ' + args.repo + '\n' : '';

if (issues.length > 1) log('The party takes ' + issues.length + ' issues, one at a time.');

const runs = [];
for (const issue of issues) {
  if (issues.length > 1) log('──────── issue ' + issue + ' ────────');
  const one = await runOne(issue, repoHint);
  runs.push({ issue: issue, ...one });
}

if (issues.length === 1) return runs[0];

const hunted = runs.filter((r) => r.hunted).length;
log('Hunted: ' + hunted + '/' + runs.length);

return {
  status: 'completed',
  issues: runs.length,
  hunted: hunted,
  runs: runs,
};
