---
title: CHATBOT
type: reference
category: backend
use_case: building or changing the router surface
created: 2026-07-14
modified: 2026-08-04
tags: [doc, harness, chatbot, router, ai, security]
---

# CHATBOT

The template's conversational surface and the architecture behind it. Ruled by [[adr-15-chatbot-two-tier]]. This file **owns the content**; the ADR states only the rules and links here.

> [!note] Naming — settled
> `chatui`, `router`, the endpoint segment `route` (`/api/router/route/`), the models `Intent` and `IntentQuery`, the reserved outcomes `NO_MATCH`/`ESCALATE`, the action field `kind`, and the env stem `ROUTER_*` are all registered in [[GLOSSARY]] ([[adr-12-glossary-and-localization]]).

## The one-line split

> [!important]
> **The tier that chooses never generates. The tier that generates never chooses.**
> Choosing carries actuator rights and emits nothing but a member of a closed enum. Generating emits free text and is read-only, forever. The two capabilities are disjoint, permanently — this is the architecture, not a phase.

## What ships in this template (stage 1)

A chat-like UI — `chatui` — where the user types free text into a box and gets a result. **It feels like a chatbot. It is not one.** There is no conversation, no memory, no prose coming back from a model. What sits behind the box is a **router**.

The router:

1. Takes the utterance.
2. Builds the menu **server-side in Django**, filtered by the requesting user's permissions (Django Groups + DRF permission classes, [[adr-10-auth]]) — before the model sees anything.
3. Calls **Amazon Nova Micro on Bedrock** (us-east-1) with a **JSON-Schema-constrained** request whose only free variable is an `enum` field, at **temperature 0**.
4. Gets back exactly one member of that enum. Nothing else is a valid response.
5. Maps that member to a preconfigured link, site action, or `GET` view and executes it.

**Zero free-text generation happens anywhere in stage 1.** No model in this template ever writes a sentence a user reads.

The shipped menu is a **closed, permission-filtered menu** built from a growable registry the owner authors — it is not a fixed, hardcoded list, and no specific option count is part of the design. Two reserved members are always present regardless of registry size: `NO_MATCH` (understood, but nothing on the menu answers it) and `ESCALATE` (below); every other member maps 1:1 to a link/action or an already-declared `GET` endpoint ([[API]]). Menus stay small on purpose, because a small closed menu is what makes the security argument below hold cheaply.

**A response outside the enum is a hard reject** — logged as a fault, never repaired, never defaulted to a nearest match, never retried into one. Silent repair would reintroduce exactly the ambiguity the enum exists to delete. Every decision, including rejects and escalations, persists an audit row (see Retention below).

**The template stops here.** Stage 2 below is *made possible* by this design; it is not built, not designed in detail, and not scheduled here.

### The starter registry — the rows the seed ships

The registry is a table, so an empty table is a legal state and a chatui whose menu holds nothing but the two reserved members is indistinguishable from a broken router. `seed_router_menu` is what makes that state unreachable: it upserts the starter registry — `STARTER_MENU` — as part of the boot chain in every environment, local Compose and the cloud migrate task alike ([[DOCKER]]). It is not demo data and carries no `--if-debug`; the demo seeds do.

- **Twelve rows.** Each names a destination the field foreman already reaches by hand — the registry offers a shorter way to an authorized route, never a new authority ([[adr-15-chatbot-two-tier]]).
- **All but one are gated on `field_managers`**, `/profile` included. A row's group gate is the registry's own copy of a decision Django already made; it narrows the menu, it does not grant anything.
- **The logout row is the only ungated member.** It is ungated because its target lives under `/accounts/*`, which sits outside the Group gate by [[adr-20-authorization-lobby]] rule 1 — so offering it to a session with no role promises nothing that session cannot already do. Every other starter row points at gated surface and is gated to match.
- **A role-less session, and the `lot_owners` portal, therefore see logout plus the two reserved outcomes and nothing else.** That is the correct menu for the lobby ([[adr-20-authorization-lobby]] rule 2), not a degenerate one: the router has nothing to offer a session that has not been granted a role, and inventing something would widen the lobby boundary.
- **The upsert touches only its own rows.** Rows the owner authored by hand survive the seed untouched, and re-running it over a populated registry changes nothing — the boot chain runs it on every `up`.

### The menu filter — three branches

`build_menu` keeps every **active** row whose gate clears any one of three branches:

1. the row is **ungated** (`group` is null);
2. the row's group is **one of the requesting user's** Django Groups;
3. the user is in **`admins`** — the standing superset that passes every gate in the project ([[adr-10-auth]]), and therefore this one too rather than by a rule of its own.

`is_active` is not a permission and the superset does not reach it: a deactivated row is hidden from **everyone**, `admins` included. Retiring a row is an editorial act on the registry — the way to take a phrase off the menu without deleting its audit history — and it would be useless if the one group most likely to be testing the menu were the one group still shown the row.

### Recorded decision (2026-08-04) — a Spanish `Intent.phrase` is registry content

`Intent.phrase` holds Spanish, is persisted, and is read by a user, which puts it within sight of [[adr-12-glossary-and-localization]] rule 6's prohibition on user-facing text generated server-side or built into a persisted field. **It is exempt, and the exemption is narrow:** a phrase is hand-authored **registry content** — written by the owner, reviewed as a row, and rendered verbatim — which is the same category as the descriptor's `label` below, not a message some code composed. The prohibition exists because generated prose has no canonical form to register; a row that a human wrote and another human reviewed has one, and the row *is* it.

What stays forbidden is unchanged: **a phrase composed at runtime** — interpolated from data, assembled from fragments, or produced by a model — is exactly the defect rule 6 names, and no amount of storing it in the registry table launders it. This records the scope of an existing rule against this one field; it is content, not a rule change, so it lives here rather than in a new ADR ([[adr-00-discipline]] rule 1).

### Local development calls Bedrock directly

A developer runs the router **from their own machine against Bedrock**, with their own IAM credentials, region us-east-1. That is the local path: no emulator, no local model server, no offline stand-in required to exercise the real pipeline.

> [!note] The VPC interface endpoint is a *cloud* requirement, not a local blocker
> The `com.amazonaws.us-east-1.bedrock-runtime` interface endpoint exists because **Fargate runs in a private subnet with no NAT gateway** ([[INFRASTRUCTURE]]) and therefore cannot otherwise reach Bedrock. That is a deployment concern and belongs to the cloud phase alone. A laptop reaches Bedrock over the public internet like any other AWS API call. Any document or plan that presents the interface endpoint as a prerequisite for building or testing stage 1 is wrong.

### AccessDenied from Bedrock has TWO root causes — triage before touching IAM

An `AccessDeniedException` on the router's Bedrock call reads identically for two unrelated problems:

1. **IAM** — the caller (task role in cloud, your credentials locally) lacks `bedrock:InvokeModel` on the model **and** its inference profile. The grant shape lives in [[INFRASTRUCTURE]] (Bedrock inference grant).
2. **Model access** — the account/region toggle for the model was never enabled in the Bedrock console. No IAM policy fixes this.

Distinguish in one command: `aws bedrock get-foundation-model-availability --model-id amazon.nova-micro-v1:0` — `authorizationStatus: AUTHORIZED` + `entitlementAvailability: AVAILABLE` means model access is fine and the problem is IAM; anything else means enable model access first (Bedrock console → Model access). Also remember the model id is the **inference profile** form `us.amazon.nova-micro-v1:0` ([[VARIABLES]] `ROUTER_BEDROCK_MODEL_ID`) — the bare `amazon.nova-micro-v1:0` id is not on-demand invokable and fails with a `ValidationException`, a third error that is neither of the above.

## Stage 2 — the router becomes a security filter (not built here)

The template only **makes this possible**. Nothing in stage 2 is designed, planned, or shipped by this repo.

In stage 2 a **second, smarter model — deliberately unnamed, TBD** — is added behind the router to do the generating the router refuses to do. The router does not step aside for it. The router becomes the **filter it must pass through**.

**The router never forwards the user's raw text.** It forwards a **reinterpreted prompt**: its own restatement of what the user meant. The smart model never sees attacker-controlled bytes verbatim. This is the whole point of the arrangement, and it only works because of the next section.

### The crux — the reinterpretation is structured, never free prose

The router's restatement is **not** a sentence the router writes. It is a **slot-filled template**:

- The **template** is chosen from a **closed, hand-authored set**, one per enum member. The prose is ours, held in code, written by us, reviewed by us. The model picks *which*, never *what*.
- The **slots** are a fixed, declared list per template. Each slot has a **type and a validator**: an enum, an integer, a date, a primary key that must resolve to a row this user is already allowed to read. A slot that fails validation fails the request; it is not coerced.
- What reaches the smart model is therefore **a sentence we wrote, parameterized by values that passed our validators**.

**Why free prose would break it, mechanically.** If the router were allowed to emit a free-text restatement, then:

1. **The router would be *generating*** — and the invariant above (the choosing tier never generates) is violated at the very first extension. The design would have eaten itself.
2. **The channel reopens.** Containment here comes from **channel capacity**, not from a model's good behaviour. An enum of *n* members plus *k* typed slots carries a bounded, enumerable, auditable number of bits — you can list every prompt the smart model can ever receive. A free-prose restatement carries as many bits as the attacker cares to spend. A model told to "restate faithfully" will faithfully carry a payload; faithfulness is precisely the property the attacker is counting on.

The security property is **the re-encoding through a narrow, typed bottleneck**. An injection payload is instructions expressed in bytes; it does not survive being reduced to *"member 3 of 5, with `date=2026-07-14`"* and then re-expanded from a template we authored. Nothing of the attacker's phrasing is left to survive.

This is a claim about the *mechanism*, and it is the only form in which the claim is true. "The router sanitizes the prompt" is not the property; **"the router re-encodes intent through a bottleneck too narrow to carry an instruction"** is.

### The honest limit — this is containment, not a proof

> [!warning] Bound the claim; do not oversell it
> This is a **strong containment**, not a proof of impossibility.

- **Any slot that carries user-derived free text is a residual channel**, in exact proportion to its width. A `search_query` slot typed as an arbitrary string hands the attacker a pipe to the smart model, and calling it a "parameter" changes nothing about that.
- Therefore: **no free-text slot ships without being an explicit, recorded decision in this file.** Where one is genuinely unavoidable, it is length-bounded, character-class-restricted, interpolated strictly as *data* (delimited, and named as data in the downstream instructions), and never placed where the downstream model would read it as instruction.
- Those are **mitigations**. They shrink the channel; they do not close it. A doc that promises a closed channel while shipping a free-text slot is worse than no doc at all.
- The routing model itself is still a model: it can be *confused* into picking the wrong menu member. What it **cannot** do is pick something that is not on the menu, and the menu was already filtered to what this user could have done by hand. **The worst outcome of a successful injection against the router is that the user gets an action they were already authorized to perform.** That is a bounded blast radius, and it is bounded by Django's authorization, not by the model's judgment.

## The permanent invariant

This is the spine of [[adr-15-chatbot-two-tier]] and the reason the enum-constrained tier is built first:

| Tier | Emits | Rights |
|---|---|---|
| **Choosing** (the router) | Exactly one member of a closed, permission-filtered enum. Never text. | **Actuator rights** — its output can flip a switch, navigate, trigger an action. |
| **Generating** (stage 2, TBD) | Free-form natural language. | **Read-only, forever.** Never flips a switch. |

If the generating tier wants an action, it does not take one. It **re-enters through the router** with a closed menu and is subject to the same filtering, the same enum, the same hard reject, and the same audit row as a human utterance. There is no privileged back door for the model that talks.

**Disjoint capabilities, permanently.** Not a transitional arrangement, not a stage-1 shortcut to be relaxed once the smart model proves trustworthy. A component that generates text must never hold actuator rights; a component that holds actuator rights must never emit unconstrained text. Every future extension is measured against this line.

### The four outcomes — Action, Answer, Escalate, NO_MATCH

Every routed utterance resolves to exactly one of four outcome kinds — **`NO_MATCH` is a distinct fourth outcome, never collapsed into `ESCALATE` or treated as an edge case of the others**:

1. **Action** — a concrete site action or navigation target is triggered.
2. **Answer** — the utterance is really a question an already-declared `GET` endpoint answers.
3. **Escalate** — the utterance needs real reasoning the closed menu cannot serve; the reserved `ESCALATE` member is selected.
4. **NO_MATCH** — the utterance was understood, but no registry entry answers it; the reserved `NO_MATCH` member is selected. This is a real, distinct answer ("nothing exists for that"), not a failure mode of `ESCALATE` ("this needs reasoning we don't have yet").

### The escalation seam

`ESCALATE` is the **single, stable handoff point** between the tiers, and it ships in stage 1 — not later. `NO_MATCH` is a sibling reserved member with a different meaning (above) and is never used as a stand-in for it.

- **Stage 1 behavior:** selecting `ESCALATE` returns a fixed "not supported yet" response. Nothing generative runs behind it.
- **Stage 2 behavior:** the generating tier plugs in **exactly here**, receiving the structured reinterpretation described above. The choosing tier's contract does not change to accommodate it.

Shipping the seam dead, from day one, is what keeps stage 2 from becoming a rewrite.

## Retention — the audit row is bounded, not forever (closes #65)

The raw utterance persists in `IntentQuery`, but under a bounded retention policy, not indefinitely:

- **Window** — `ROUTER_AUDIT_RETENTION_DAYS` ([[VARIABLES]], default `30`) bounds a row's lifetime, measured from `created_at`.
- **Purge** — the `purge_router_audit` management command deletes rows past the window; idempotent, `--dry-run` reports without deleting.
- **On-delete** — `IntentQuery.chosen_intent` is `SET_NULL`, not `PROTECT`: deleting an `Intent` registry row never cascade-deletes, and is never blocked by, its audit history (resolves the #105 collision).
- **Admin visibility** — `utterance` / `raw_model_output` are visible in Django admin only to the "Router Auditors" group; every other admin user's views exclude both fields.

## The action descriptor — the backend chooses, the frontend acts

The choosing tier's response is a **typed action descriptor**, never a performed side effect. The router selects; it does not navigate, redirect, or execute on the caller's behalf. This narrows [[adr-15-chatbot-two-tier]] rule 1's "actuator rights" to *emitting a descriptor*, not *performing an action* — content, not a rule change, so it lives here rather than in a new ADR ([[adr-00-discipline]] rule 1).

The descriptor carries typed, validated slots:

- **`kind`** — `navigate` or `confirm`. Reversibility decides which: `navigate` fires immediately and MUST be safe and idempotent (`GET` only); `confirm` returns a proposal the browser must present to the user before executing it as a separate, CSRF-protected request against `target`, subject to that endpoint's own authorization. Every irreversible or state-changing action is `confirm` — logout included.
- **`target`** — the URL or endpoint the frontend acts on.
- **`label`** — the hand-authored, human-facing text for the choice ([[LOCALIZATION]] — registry content, not code).

The response body carries **no prose beyond the registry-authored `label`**: the reserved outcomes (`NO_MATCH`, `ESCALATE`, the kill switch's `disabled`) return their outcome key only, and the frontend owns the corresponding user-facing copy. A router response that mutates state, redirects, or free-text-explains itself is a defect — it would make the choosing tier a generator, eroding the invariant above.

## RAG — facilitated, not designed

The chatbot is the intended **future entry point for a RAG**. The template only *facilitates* it: a free-text surface and a generating tier that is read-only by construction are the two things a retrieval-augmented answer path needs.

**No RAG is designed, planned, or built here** — no store, no embedding strategy, no chunking, no retrieval contract. This paragraph is the entire extent of the commitment.

**pgvector and embeddings are deliberately deferred, not omitted by oversight.** The enum-constrained model call already performs the semantic matching a small, hand-authored registry needs; a vector index next to it would be a second matching mechanism with its own threshold, tie-break rule, and drift, for a menu that fits in a prompt with room to spare. **The trigger to revisit:** the registry grows past what fits comfortably in a single prompt (dozens to low hundreds of entries) or per-call token cost stops being negligible. At that point the fix is a **retrieval pre-filter** in front of the enum — embed the utterance, shortlist the nearest registry entries, hand only those to the enum-constrained call — never a replacement of the enum itself; the security argument above is unaffected because the shortlist is still a subset of an already permission-filtered menu.

## Relationship to the sibling documents

- [[API]] — every endpoint this feature needs enters there first, in its own guarded act, before any code ([[adr-51-api-and-backend]]).
- [[AUTH]] / [[adr-10-auth]] — unchanged. Cognito authenticates; Django authorizes. The router authorizes nothing; it narrows a menu Django already authorized.
