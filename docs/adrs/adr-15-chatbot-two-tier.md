---
title: adr-15-chatbot-two-tier
type: adr
category: backend
use_case: building or changing the chatui router, adding an action to the router enum, wiring model output toward an actuator, passing anything between the choosing and generating tiers
created: 2026-07-14
modified: 2026-08-02
tags: [adr, chatbot, router, ai, security]
---

# ADR-15 — the two-tier chatbot

## CONTEXT

> The tier that chooses never generates, and the tier that generates never acts. That disjunction is permanent — it is the boundary this design exists to hold, not a stage on the way to something else.

## ASSERTIONS

1. Capabilities are disjoint, permanently. The tier that chooses holds actuator rights and MUST NEVER emit free text. The tier that generates free text is read-only, forever, and MUST NEVER flip a switch. No component may hold both. This is a standing boundary, not a transitional arrangement, and no future feature may blur it ([[CHATBOT]] — the permanent invariant).
2. The choosing tier's only valid output is one member of a closed enum, built server-side in Django and filtered by the requesting user's permissions ([[adr-10-auth]]) before the model is invoked. A model output outside that menu is a hard reject: logged as a fault, never repaired, never defaulted, never retried into a nearest match.
3. The model never makes an authorization decision and can never widen privilege. Authorization is decided once, in Django, before inference; the router only narrows within an already-authorized set. A permission decision read from a model's output is a defect, exactly as a permission decision read from a Cognito claim is ([[adr-10-auth]] rule 2).
4. When the generating tier wants an action, it re-enters through the choosing tier with a closed menu, subject to the same filtering, the same enum, the same hard reject, and the same audit row as a human utterance. There is no path from generated text to an actuator that bypasses rule 2.
5. The choosing tier NEVER forwards user-supplied text to the generating tier. What it forwards is a structured reinterpretation: a hand-authored template selected from a closed set, filled with typed, validated slots. A free-prose restatement would make the choosing tier a generator, violating rule 1, and would reopen the channel this design exists to close. Mechanism and its limits: [[CHATBOT]].
6. A free-text slot is a residual channel and requires an explicit, recorded decision in [[CHATBOT]] before it ships. No document, comment, or commit message may state the containment as a closed channel or a proof; it is bounded as [[CHATBOT]] bounds it. Overstating the security property is a defect.
7. Inference is deterministic and structurally constrained: temperature 0, and constrained decoding where the provider supports it, with code-side enum validation enforcing the same closure regardless.
8. This is a capability layer, not a doctrine change ([[adr-13-m365-graph]] precedent). Cognito remains the sole authentication provider ([[adr-10-auth]]); [[CACHE]] gains no cache server ([[adr-06-cache]]); every endpoint enters through [[API]] before code ([[adr-03-api-and-backend]]); every variable a setting reads enters [[VARIABLES]] first; the app, its endpoint segments, and its env stem get their [[GLOSSARY]] rows before first use ([[adr-01-glossary-and-localization]]).
9. The template ships the choosing tier and stops. The generating tier's bounded activations arrived as their own decisions — the advisors ([[adr-27-advisors-generative]]) and the conversational assistant ([[adr-35-conversational-assistant]]) — each read-only, each holding rule 1's disjunction intact. Any further generative surface, and any RAG, enters the same way: through [[adr-07-development-flow]], never by widening a tier this ADR already bounds.

## FORBIDDEN

- **NEVER** give one component both actuator rights and free-text generation (rule 1). A tier that does both reopens exactly the channel the split exists to close.
- **NEVER** repair, default, or nearest-match an out-of-enum model output (rule 2). The only valid outcome is a hard reject logged as a fault; a repaired output is an action nobody chose.
- **NEVER** read an authorization decision from a model's output (rule 3). Authorization is decided in Django before inference; anything else lets inference widen privilege.
- **NEVER** forward user-supplied text from the choosing tier to the generating tier (rule 5). Only the closed-set template with typed, validated slots crosses; free prose crossing makes the chooser a generator.
- **NEVER** describe the containment as closed or proven, in any document, comment, or commit message (rule 6). The security property is bounded, and overstating a control is itself a defect.

## REJECTED

- **The generating tier as out of scope** — rule 9 originally shipped the choosing tier and stopped: the template left only the seam, and no generating surface existed. Spent when the seam was activated as its own decisions — [[docs/adrs/adr-27-advisors-generative]] (bounded one-shot reports) and [[docs/adrs/adr-35-conversational-assistant]] (the conversational tier) — each read-only, each leaving rule 1's disjunction intact. The staging would reopen only for a fresh project spawned from the template, which again starts with the chooser alone.

## RELATED

### related adrs

- [[docs/adrs/adr-10-auth]] — the authorization authority rules 2–3 defer to
- [[docs/adrs/adr-13-m365-graph]] — the capability-layer precedent rule 8 follows
- [[docs/adrs/adr-27-advisors-generative]] — the first bounded activation of the generating tier
- [[docs/adrs/adr-35-conversational-assistant]] — the generating tier's conversational activation, read-only forever
- [[docs/adrs/adr-06-cache]] — no cache server rides in with this layer
- [[docs/adrs/adr-03-api-and-backend]] — every route of this surface enters through [[API]] first
- [[docs/adrs/adr-01-glossary-and-localization]] — names enter [[GLOSSARY]] before first use
- [[docs/adrs/adr-07-development-flow]] — the path any new generative surface enters through

### related files

- [[docs/CHATBOT]] — the mechanism, the closed menu, and the bounds of the containment
- [[docs/API]] — the declared routes of the chat surface
- [[docs/VARIABLES]] — the env stem and every variable the surface reads
