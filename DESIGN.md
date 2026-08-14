# Buoy — Design Notes

Living design doc. Captures Cooper's thinking; **seeds Part 3's required written
rationale.** Claude's additions/proposals are marked `[C:]` so authorship stays
clear and nothing is silently injected.

---

## Premise

AI-mediated deliberation between **two participants who genuinely disagree** (maybe
not on everything — on some part of an issue). The bet: AI might improve civic
discourse by helping people reason *with each other*, not by giving each person a
private assistant to "optimize" a task.

## Topic choice: why one topic, and why congestion pricing

**Why a single fixed topic** (not multi-topic):
- The assignment explicitly values **depth over breadth** (<1 day).
- A fixed topic is what makes **Part 4 tractable**: counterfactual/symmetry testing
  (swap positions, vary confidence) is clean when the subject is held constant.
- It collapses the product to a single screen and lets us curate a **bounded,
  auditable dossier** (vs. open-ended retrieval) — a smaller bias surface.

**Why congestion pricing specifically:**
- **Genuine reasonable-person disagreement** — no obvious right answer (the
  assignment requires this; bias-eval is meaningless on a topic with a clear
  answer).
- **Rich empirical record** (London, Stockholm, Singapore, Milan, and NYC live
  since early 2025) → there's *ground truth* for the "furnish info with sourcing"
  capability, so asymmetry in sourcing becomes **measurable**, not vibes.
- **Surfaces the hard sub-problems** despite looking "banal" next to, say, climate
  change: it cleanly separates an **empirical** axis (does it cut congestion /
  raise transit funds?) from a **value** axis (distributional fairness to
  outer-borough drivers vs. efficiency/emissions). That empirical-vs-value split is
  exactly the crux-classification and neutrality challenge we care about — focused
  but rich.
- **Good-faith, non-extremist** — fits the assignment's assumed setting.

## The core tension

The moderator has power simply by deciding **what deserves attention**: what to
respond to / interject on, what gets skepticism, what context is supplied, when to
intervene, how to characterize disagreements. The intervention policy must make
disagreement *more productive* without the moderator becoming a third participant.

- Honest caveat: the moderator **is** a participant to some degree — unavoidable —
  but one with **clear rules** limited to supporting productive disagreement
  between the two humans. `[C:]` Cleanest framing: a participant with a *fixed,
  transparent, contestable* role confined to **process**.
- Why neutrality is subtle: a moderator can be perfectly polite, never say "Bob is
  right," and still steer — e.g. challenge Bob's factual claims while letting
  Alice's assumptions pass; summarize Alice more sympathetically; find stronger
  evidence for Bob; tell Alice she hasn't answered Bob's objection while
  overlooking the same for Bob. These operate **in concert**.

---

## Organizing principle: process vs. substance

Be strongly directive about the **process** of reasoning while deliberately
non-directional about the **substantive** outcome. This divide feels core to the
whole assignment. Grounded in two thinkers:

### Berlin — value pluralism

Reasonable people face **genuine value conflicts not reducible to a common metric**
(liberty, equality, security, fairness, autonomy, community, efficiency, democratic
accountability…). No new fact necessarily dissolves the disagreement.

- ⇒ **Clarified persistent disagreement is itself success. Convergence is NOT the
  goal.**
- Congestion-pricing example of a *good* ending: *"We agree about the likely
  economic effects; we disagree because one of us regards distributional fairness
  as overriding the efficiency gain in these circumstances, and the other does
  not."* Buoy helped reach that clarity without adjudicating it.
- **Monism disguised as neutrality** (anti-pattern): quietly assuming every dispute
  has a uniquely rational resolution and framing the conversation around getting
  everyone there. Looks unbiased; is biased.

### Habermas — legitimacy of discourse

Buoy is not an oracle that resolves the dispute. Its job is to improve the
**conditions under which participants give and respond to reasons**. Attend to:

- each participant can make their position **intelligible**;
- claims/reasons receive **responses** rather than being ignored;
- participants respond to **what the other actually said**;
- no one gains advantage **merely through style/confidence/repetition/tone**;
- relevant **factual uncertainty is visible**;
- participants can **challenge each other — and the moderator** (contestability).

Apply the **same criteria** for what needs clarification, evidence, skepticism, or
intervention regardless of who said it or which conclusion it supports.

---

## Three components

**1. Participant experience.** Identify when participants are answering different
questions; surface neglected claims; clarify terms; identify common ground; bring
in outside evidence *only when it would actually resolve something*; periodically
summarize where the conversation has landed. But **don't constantly interrupt** —
that makes it too active a participant and crowds out the humans.

**2. Internal representation of the debate** (touches the data model). Hypothesis:
don't just feed the raw transcript to the API — maintain lightweight structured
state. (Testable: do both and compare.) Candidate state per session:
- positions/claims each participant has actually endorsed;
- support/rebuttal relationships;
- questions awaiting answers;
- propositions they agree on;
- candidate **cruxes** (core points of disagreement);
- factual questions external evidence might resolve;
- a **history of the moderator's actions** (surfaced *and* not) so intervention can
  be balanced — *not* "50/50 Alice/Bob"; a subtler notion.

Moderation as a **cycle / state machine**:

```
transcript state → decision → intervention type → intervention text [or no-op] → state update
```

Instrumentable, and lets Part 4 **attribute bias to a stage**:
- deciding to intervene against one side more often;
- classifying one person's statement as requiring evidence;
- identifying one person's claim as the crux for the whole debate;
- retrieving different information;
- wording substantively equivalent interventions differently / with different tone.

**3. Oversight / evaluation.** Falsifiable bias claims via **counterfactual paired
transcripts**: swap participant identities / which speaker holds which position;
vary confidence/style while keeping the substantive argument. Measure deltas in:
intervention frequency, amount of explanatory text, requests for justification,
strength of skeptical language, factual-verification effort, praise/deference,
framing in summaries.

---

## Productive disagreement (the actual goal)

**Not consensus.** A successful debate might end in *sharper* disagreement:
- *"We agree on X, Y, Z; our remaining difference is that Alice weights value P more,
  Bob weights Q more,"* or
- *"Everything now turns on this uncertain proposition, which needs more empirical
  evidence to resolve."*

The moderator helps participants **see the debate's structure**, prompts engagement
with each other's **strongest** claims, and fills **genuine** informational gaps —
but does **not** synthesize "correct"/"incorrect" conclusions. The participants do
the normative work.

---

## Draft mini-constitution

Maybe the system needs a **mini-constitution**, not just a system prompt:

1. Serve the participants' deliberation, not a preferred conclusion.
2. Be directive about conversational **process**, restrained about **substantive**
   judgments.
3. Treat **clarified disagreement as success**. Don't optimize for consensus.
4. Apply the **same intervention criteria** irrespective of participant or position.
5. Correct factual errors when warranted, but **don't advocate** for either
   participant or position.
6. Use the **minimum intervention** needed (don't distract from the exchange).
7. Interpretations/summaries are **contestable** by the participants.
8. **Track the moderator's allocation of attention** — it too can be biased.

> `[C:]` **The key move that keeps this from being "just a system prompt"** (which
> the assignment explicitly warns against): tie **each clause to a measurable
> signal** in the Part 4 eval. A constitution asserts neutrality; the metric makes
> it *falsifiable*. Draft mapping to develop:
> - #4 (same criteria) ↔ counterfactual swap test on skepticism / evidence-demands
> - #6 (minimum intervention) ↔ intervention-rate / no-op-rate
> - #8 (attention) ↔ attention-allocation metric across participants
> - #5 (correct, don't advocate) ↔ does correction frequency depend on which side a
>   claim supports?
> - #3 (don't push consensus) ↔ does the moderator nudge toward agreement vs.
>   toward clarified disagreement?

> `[C:]` **Full draft promoted to `CONSTITUTION.md` (v0.1)** — adds two clauses
> (symmetry of expression; no reward for style), extends #5 (equal verification
> effort + sourcing), splits model-facing clauses from harness-enforced
> commitments, and completes the clause↔signal mapping.
>
> **Process note for the write-up (honest-findings material):** our first
> constitution draft under-articulated the *expression-level* biases — tone/
> framing symmetry and sycophancy — even though our own notes opened with
> exactly those failure modes ("summarize Alice's take more sympathetically";
> "advantage merely through style/confidence/repetition/tone", my-notes.md
> lines 9, 39, 83). The Part-4 mapping exercise is what caught it: checking each
> bias axis for a clause it could falsify exposed that two measured axes had no
> normative anchor. The fix was promotion, not invention — the ideas were
> already in the notes, just not in the numbered list.

---

## Open architecture questions (Cooper)

1. Does the model see every message as it arrives?
2. Is it invoked after every turn, even if it ultimately no-ops?
3. Raw transcript, or transcript + structured debate state?
4. Does one call both **decide** whether to intervene and **write** the
   intervention — or do we separate an observer/controller from the writer?
5. Does the model update a private structured representation after every message?
6. When facts are needed, is retrieval initiated by the moderator or the
   participants?
7. What information about previous moderator actions does the model see?
8. How do we prevent accumulated summaries from silently distorting one
   participant's position?
9. What should the participants see (of the moderator's reasoning/state)?

### `[C:]` Proposed leanings (for review — NOT decided)

- **Q2/Q4:** invoke a **decision step after each participant message** that mostly
  no-ops; use a **single structured call** returning
  `{intervene?, type, target, rationale, text}`. The decision stays **separable in
  the log** (good for eval) without a second round-trip (good for latency/cost).
- **Q3:** make input-mode a **Moderator `config` knob** (`raw` vs `raw+state`) — it
  becomes a ready-made A/B for Part 4, cashing in the earlier model/config split.
- **Q6 (retrieval — deferred, decide before T5).** Leaning **(a): a small curated
  dossier** — a *bounded* document set (a few cities' congestion-pricing material)
  the moderator retrieves over for empirical/factual info. Explicitly **no general
  web lookup** — that unbounded rabbit hole is both a time sink and an
  *asymmetric-retrieval bias vector*. A fixed corpus is auditable and symmetric by
  construction (we control what's retrievable). Fallback/complement **(b)**, very
  Habermas-aligned: **flag** evidence-resolvable questions and make the uncertainty
  visible **without resolving them**. Likely we do (a) with (b) as the default when
  the dossier is silent.

---

## Schema implications for T2 `[C:]`

- The **moderator-action log is a first-class table**, not just `Message.metadata`:
  no-op decisions produce **no Message** but must still be recorded (for
  attention-tracking, principle #8, and stage-level bias attribution). → proposed
  `ModeratorAction` table: `session_id`, `after_message_id`, `decision`
  (intervene|noop), `intervention_type` (enum), `target_participant?`, `rationale`,
  `message_id?` (if it produced text), `state_snapshot`/`delta`.
- **Structured `SessionState`**: build a *minimal* version now (e.g. open claims,
  unanswered challenges, candidate crux) rather than fully deferring — the
  moderator's decision quality and the eval both lean on it. Keep it small.
- **Two homes for the tracked debate-state** (authoritative → `SPEC.md`; do not
  re-pull from `my-notes.md`): moderator attention/action history →
  `ModeratorAction` table (built in T2); claims / rebuttals / open questions /
  agreements / candidate cruxes / evidence-resolvable questions →
  `SessionState.state` JSON now (promotable to tables at T5).

---

## Moderator action taxonomy & crux classification (settled 2026-08-13)

### Intervention types — candidate set

Grouped by the bias vector each guards. **Final cull to a minimal well-separated
set (~10) is deferred to T5** (schema stores `intervention_type` as a string, so
the enum isn't frozen yet). Merge candidates flagged.

- **Engagement:** `note_talking_past` (not engaging the same question) ·
  `surface_neglected_claim` · `note_unanswered_challenge` (an objection *to* you
  left unanswered) · `note_misread` (strawman/distortion) ·
  `prompt_engagement_with_strongest` (steelman nudge)
  - *Merge candidate:* `surface_neglected_claim` vs `note_unanswered_challenge`.
- **Meaning / structure:** `clarify_term` (incl. the equivocation/definitional
  case) · `invite_clarification` (help a participant make their *own* position
  intelligible) · `mark_agreement` · `summarize_state` · `identify_crux`
- **Epistemic:** `request_justification` (asymmetric-skepticism vector) ·
  `supply_evidence` · `correct_factual_error` · `flag_uncertainty`
  (evidence-resolvable, left unresolved)
  - *Merge candidate:* `correct_factual_error` vs `supply_evidence`.
- **Conduct:** `check_tone`
- `none` (no-op).

**Three "failure to connect" modes kept deliberately distinct** (merging them would
blur exactly the asymmetries Part 4 targets): `note_talking_past` (different
question) · `note_misread` (distorted version) · `clarify_term` (same word, different
meanings). `note_talking_past` escalates into `identify_crux` when the real
disagreement is an unstated *underlying* question.

**Types vs. qualities.** The enum captures *what* the moderator does. Bias also
enters via *how* it does any of them — wording/tone of an otherwise-equivalent
intervention, framing in summaries, praise/deference. These are **per-intervention
quality axes measured across every type in Part 4**, NOT enum members.
`track_attention` (constitution #8) is likewise a property measured across actions,
not a type.

### Crux classification

`identify_crux` stays atomic; the crux object carries **`type ∈ {empirical, value,
mixed}`**:
- **empirical** — evidence could in principle resolve it;
- **value** — a value-weighting tradeoff evidence won't resolve (Berlin);
- **mixed** — the common case; the productive move is to **decompose** into the
  empirical sub-question (which may be settleable) and the value sub-question
  (which is legitimately terminal). *(Congestion-pricing example: agree on effects
  [empirical] / differ on fairness-vs-efficiency weighting [value].)*

Design stance (this is a hard open research question — value-incommensurability
lit, Berlin's *Crooked Timber of Humanity*): **corrigibility over correctness.** We
don't claim the moderator classifies cruxes *correctly*; it proposes a coarse,
**contestable** classification the humans can reject/replace (→ updates
`SessionState`). To be flagged in the write-up as a deliberate simplification.
- Dropped: `definitional` as a crux *type* — it's an equivocation *cause* handled
  upstream by `clarify_term`, not where a genuine disagreement lives.
- **Success state:** reaching a named value (or decomposed) crux is the product's
  success — a `SessionState` marker (not an intervention type), so success is
  *instrumentable* (answers Part 3's "how do you measure success").
- **Bias tie-in:** mislabeling a value-crux as empirical implies one side is simply
  wrong → a bias; symmetric crux-classification is a Part-4 check, contestability
  its mitigation.

### Identity model + known limitations (T3 — for the write-up)

**Per-session ephemeral identity.** No accounts. A name is entered per debate;
a per-session cookie (`buoy_{session_id}`) ties a browser to its seat. The same
browser can be distinct identities across different sessions.

**"Closes the window" behavior — deliberately the simplest thing:**
- No disconnect detection; leaving does nothing (session stays live, seat stays held).
- Rejoin by reopening the URL in the same browser (cookie intact).
- **Limitation:** losing the cookie (cleared cookies / other browser / other device)
  means the seat stays held by the prior ephemeral identity — you can't reclaim it
  ("session full"). Acceptable for a prototype; a real product would add a rejoin
  token or release seats after prolonged absence.
- **Not implemented (write-up note):** dead/abandoned sessions accumulate. In
  production a scheduled job (cron) would time out and terminate stale sessions
  after some interval. Out of scope for the assignment; noted for completeness.

### Participant naming (Part B — settled)

- Moderator **reasons over neutral labels (P1/P2)**; humans see real names;
  `display_name` stored separate from the seat.
- Rationale: names are the one identity signal removable **at zero cost to the
  substance** of the debate. Style, confidence, and self-disclosed identity can't
  be stripped without distorting the argument → those are **measured** in Part 4,
  not suppressed. Name-blinding is therefore *partial* neutralization — say so
  plainly.
- Optional (if time): substitute `display_name` back into the moderator's
  *surfaced text* for warmth, while its *reasoning* stayed name-blind.
- **Part 4 candidate (if time):** a **name-injection arm** — feed demographically-
  varied names *into the moderator's input* and test whether they **shift the
  moderator's behavior** (which the bias metrics then detect) vs. the neutral-label
  baseline. I.e. names → moderator behavior → measured bias. Ref: UW iSchool,
  "bears will be boys" (name→demographic inference) — read at eval-design time.

### Decision schema — deliberate simplifications (for the write-up)

- **`target_participant = None` is overloaded.** It means *both* "addressed to
  both participants" (for an intervention) and "no target" (for a no-op),
  disambiguated only by `intervention_type`. A cleaner design (more time) would be
  explicit — e.g. `Literal["P1", "P2", "both"]` — so "who is addressed" doesn't
  ride on Python's `None` (normally "absent/unset") and doesn't share a value with
  the no-op case. **Corner cut deliberately**: fine here because
  `intervention_type` disambiguates and "addressed to both" is the common case.
- **`intervene` is derived, not stored** (`intervention_type != "none"`), and the
  dependent fields are **normalized, not rejected**, on parse — chosen so a minor
  model inconsistency never wastes an API call. (Item 1b.)
- **Retrieval / factual sourcing — deliberately cut under time pressure (write-up).**
  The design calls for a bounded curated dossier the moderator sources from
  (clause 5, "supply evidence *with sourcing*"). We cut it for time; clause 5 is
  rendered as its **flag-uncertainty half** — surface evidence-resolvable
  questions, make uncertainty visible, never assert unsourced facts or fabricate
  citations. This is an *acceptable* place to cut because clause 5's core neutrality
  axis — **asymmetric skepticism / verification-effort** (does Buoy scrutinize one
  side's facts harder?) — stays fully testable in Part 4 without fetching sources;
  only the *citation-presence* sub-signal is dossier-gated. Revisit only if time
  remains (web search likely cheaper than a curated dossier). **Deliberate, not an
  oversight.** (`supply_evidence` is effectively dormant in this build; the enum
  cull may drop it.)

### Moderator cycle — execution model + failure handling (T5)

- **In-process background task**, not a durable job queue. The cycle runs via
  FastAPI `BackgroundTasks` (single worker), so tasks are lost on restart and share
  the process with request handling. Fine for a prototype; production would use a
  dedicated worker/queue (Celery/RQ) for durability, retries, and isolation.
  **Write-up flag.**
- The cycle function is **sync** → FastAPI runs it in a threadpool, so the blocking
  Claude call never freezes the single worker's event loop. (Same reason we
  "never hold a DB lock during the Claude call": read quick → release → call API →
  write quick.)
- **Failed calls are logged as a *distinguishable* no-op** —
  `ModeratorAction(decision=noop)` with `state_snapshot={"error": {type, message,
  request_id}}` — so the bias eval can tell "chose silence" from "the call failed."
  A flaky API error must never look identical to a deliberate no-op.
- **Rapid-fire race** (two participant messages → two concurrent cycles) is
  **accepted for the raw-first cut** (the moderator's no-op bias bounds it); a
  debounce / "only react to the latest" guard is a noted refinement.

**Cycle sequencing (locked):**
`fire (on a participant message) → build input → decide → log ModeratorAction
ALWAYS → if intervene: post moderator Message → update SessionState → poll shows
it.` In **raw mode**, "build input" state is empty and "update SessionState" is a
**no-op** — the skeleton is unchanged when structured state is added later; we just
fill those two slots. Three deliberate design decisions inside it:

1. **Injectable decider.** `run_cycle(..., decide_fn=client.decide)`. The API call
   is the slow/costly/non-deterministic part, so tests inject a *stub* decider
   returning canned `Decision`s — the whole cycle (log-always, maybe-post,
   idempotency, no-self-trigger) is tested **deterministically and API-free**; only
   a couple of real tests hit the API. (Testability + cost.)
2. **Fire only on participant messages; no self-trigger.** The trigger lives only
   in `POST /messages` (the participant path); the moderator's Message is inserted
   *internally by `run_cycle`*, never through that route, so it can't re-trigger a
   cycle — Buoy can't talk to itself. `author_type` is the explicit guard.
3. **One action per participant message** — `UNIQUE(session_id, after_message_id)`
   on `ModeratorAction`. Buys idempotency (a re-fire hits the constraint → skip),
   makes *"did the moderator process message X?"* a lookup, and gives the eval a
   clean message→decision mapping. `run_cycle` checks-before-`decide()` (fast path,
   avoids a wasted call) with the constraint as the correctness backstop. For an
   intervention it **claims the action slot first** (insert, `message_id=None`) and
   only then posts the Message — so a lost race can't orphan a moderator message.
   *(Per-message idempotency; does not eliminate the cross-message stale-transcript
   race, which stays accepted.)*

---

## Cut under time pressure (for the write-up)

Forced cuts, listed honestly. Several are things we designed for and could have
tested with more time — the architecture already supports them; we ran out of hours,
not ideas. This *is* the "how you approached tradeoffs" material.

- **Retrieval / factual sourcing (dossier).** Designed a bounded curated dossier
  (clause 5, "supply evidence with sourcing"); cut for time → clause 5 rendered as
  its flag-uncertainty half. Core axis (asymmetric skepticism/verification) still
  testable; only citation-presence is dossier-gated. Web search likely the cheaper
  revival path.
- **Structured `SessionState` / `raw+state` moderator input** (the debate-structure
  model: claims, cruxes, agreements). Running **raw-transcript first**; state read is
  empty and state update is a no-op. Schema + config knob (`input_mode`) already in
  place — it's a slot to fill, not a redesign. Clause 8's model-facing half is inert
  until this exists (harness H1 still logs, so attention is measurable regardless).
- **"Track structure and present it back" (T6).** We surface interventions + Buoy's
  reasoning; a running summary / crux board isn't built.
- **Contestability *uptake* (clause 7).** Participants can contest Buoy verbally, but
  a structured "correction updates state" mechanism isn't wired (needs SessionState).
- **Name-injection ablation (Part 4).** Designed as a Part-4 arm (feed demographic
  names → measure moderator behavior shift). **Cheap to add if time remains** — the
  harness renders P1/P2, so injecting names is a one-line variant.
- **Per-moderator *model* A/B.** Constitution is per-moderator (config-driven);
  the model is still env-global (`settings.model`). Full per-moderator model A/B is a
  small `decide()`-signature change.
- **Enum cull** (intervention types).
- **Intervention cooldown / rapid-fire debounce — worth revisiting (future tweak).**
  Rejected *during* the build because it would stop Buoy interjecting back-to-back in
  an off-the-rails case. But since moderator-shutdown for those cases is itself
  out-of-scope (good-faith assumption), a cooldown to cap *normal-flow*
  over-intervention becomes reasonable — a future tweak. Current lever is the
  silence-as-default prompt (which fixed the over-intervention we saw in testing).
- **Moderator-initiated end / shutdown** (extreme circumstances) — schema carries
  `ended_by` (and `end_session()` exists), but there is **no Decision action and no
  `run_cycle` logic: Buoy cannot end a debate; only participants can.** This is a
  *principled* cut, not just a time cut: the assignment **assumes good-faith adults
  and non-abusive content**, so moderator shutdown (a tool for egregious/abusive
  cases) is **outside the assumed setting.** The prompt lets Buoy intervene
  back-to-back to restore civility but makes no claim it can end the debate.
