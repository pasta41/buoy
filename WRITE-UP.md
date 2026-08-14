# Buoy — Design Rationale

*Buoy:* a buoy keeps you afloat and marks the safe channel. It's a fixed navigational aid that guides passage without steering the boat or choosing its destination. That is the moderator's job here: directive about the *process* of a debate, but silent about its *substance*.

**Prototype:** https://buoy-2ejg.onrender.com · **Code:** github.com/pasta41/buoy

**Companion docs** (this is the summary): [`DESIGN.md`](DESIGN.md) (decisions, taxonomy, cuts), [`CONSTITUTIONv0.1.md`](CONSTITUTIONv0.1.md) (clauses ↔ falsifying signals), [`my-notes.md`](my-notes.md) (original brain-dump), plus [`SPEC.md`](SPEC.md) and [`REQUIREMENTS.md`](REQUIREMENTS.md).

---

## The problem

Buoy lets two people who genuinely disagree debate a contested question — *should cities adopt congestion pricing?* — with Claude as moderator. The point is to study whether an AI can improve civic discourse by helping people reason *with each other*, rather than giving each a private assistant to argue better.

**Why one fixed question.** This was a deliberate decision to constrain the design and eval surface for the assignment timeline. I picked this question because there's no universal right answer (it depends on the city, context, values, and so on); there's a rich empirical record of debates on the topic (e.g., London, Stockholm, Singapore) that makes factual asymmetry measurable; and it actually cleanly separates an *empirical* axis (does it cut congestion, fund transit?) from a *value* axis (fairness vs. efficiency/emissions). Although the question might seem banal on the surface — it's not something as provocative as "is climate change real?" — it covers a lot of ground relevant to the assignment. (I'm also a New Yorker, so know firsthand just how contested this question is, since it's been argued about my whole life.)

**The hardest part.** A moderator has power simply by deciding **what deserves attention**: what to respond to, what gets skepticism, when to intervene, how to characterize the disagreement. It can be perfectly polite, never say "Bob is right," and still steer the discussion: e.g., challenge Bob's facts while letting Alice's assumptions pass, or summarize Alice more sympathetically. These dynamics operate in concert.

## The organizing idea: directive about process, silent about substance

Every decision below follows one principle, isolated in [my notes](my-notes.md) from my first read-thrus of the assignment: the system is strongly directive about the **process** of reasoning and deliberately non-directional about the **substantive** outcome. In thinking about the problem, two writers immediately came to mind to ground the design (and the [v0.1 constitution](CONSTITUTIONv0.1.md) that operationalizes it). (These are writers I've engaged with in [early work](https://arxiv.org/abs/2202.05338) in my PhD.)

**Isaiah Berlin — value pluralism.** Reasonable people face genuine conflicts among values (fairness, efficiency, autonomy, community) that don't reduce to a common metric, and no new fact need dissolve them. So success is redefined: *clarified persistent disagreement is a good outcome; convergence is not the goal.* A debate ending in *"we agree on the economic effects; we differ because one of us weighs distributional fairness over the efficiency gain"* is a success. The anti-pattern is **monism disguised as neutrality** (Berlin, *The Crooked Timber of Humanity*): assuming every dispute has one rational resolution — which looks unbiased but embeds a particular worldview.

**Jürgen Habermas — legitimacy of discourse.** Buoy is not an oracle; it improves the *conditions* under which participants give and respond to reasons: each can make their position intelligible; claims get responses; people engage what the other actually said; no one gains advantage through style, confidence, or repetition; uncertainty stays visible; and participants can challenge each other and the moderator. The **same criteria** for clarification, evidence, and skepticism apply regardless of who spoke or which conclusion is served. Because the moderator is a participant with power, it is governed by **fixed, published, versioned, contestable rules**, applied identically to both, every interaction logged and auditable, with an appeal mechanism (again, in this part, the focus is process legitimacy, not outcome correctness).

The above is also combined with some other ideas directly relevant to the organizing idea: published versioned rules, identical application, an audit log, and appeal. Another aspect of the design (and the constitution) is that it takes as fact that the moderator is inescapably a participant to a degree. This is why a mini constitution is useful: it keeps the moderator's role fixed, transparent, contestable, and confined to process.

## The prototype (one interaction pattern)

Two participants join a session by link and debate in real time. After every participant message, the moderator runs one structured decision cycle:

```
transcript → decide {intervene?, type, target, rationale, text} → log ALWAYS → post only if intervening
```

- **Silent by default.** For well-intentioned users (the main user in the assignment doc), most turns return `none` and post nothing. This is the correct behavior. Intervention shouldn't crowd out human discussion. (This is a balance that should be determined with more testing; no action is also the surest way to exhibit no bias, since there would be nothing to evaluate.)
- **One structured call.** The decision is a typed object (intervention type from a ~16-type taxonomy, target, crux classification, rationale, text). Every decision, including silence, is machine-readable.
- **Every decision is logged**, no-ops and failures included, in a first-class `ModeratorAction` table. This is part of what takes the assignment's "log and replay transcripts" seriously: the eval corpus accumulates by operating on this.

## 1. Which capabilities, and why

**Chosen:**

- **Keep the debate on track** — flag talking-past, neglected claims, misreadings, and unclear terms (live today).
- **Decide when to intervene vs. stay silent** — the no-op-by-default cycle *is* this capability.
- **Find the crux** — classify it *empirical* (evidence could resolve it), *value* (a weighting difference evidence won't help resolve), or *mixed* (decompose into both). Whether cruxes classify this cleanly is an open research question, so the stance is **corrigibility over correctness**: a coarse, contestable label the participants can deliberate on. Bias ties in directly to this: mislabeling a *value* crux as *empirical* implies one side is simply wrong, so symmetric crux-classification is itself a Part-4 check.

**Partially built:** *track debate structure and present it back* — the structure is tracked (action log + session state); the present-back UI isn't built.

**Deliberately cut:** *factual info with sourcing.* *Unvetted* sourcing is a bias vector (asymmetric retrieval, fabricated citations), so the moderator is forbidden from asserting facts it can't ground. Instead, it names the open empirical question and makes uncertainty visible. The designed middle path, cut for time, was a **bounded curated dossier** of congestion-pricing facts, auditable and symmetric by construction. I think cutting it is acceptable for the eval: asymmetric skepticism (does Buoy scrutinize one side's facts harder?) stays testable; citation-*presence* can't be evaluated.

## 2. Neutrality, and the tradeoffs

**What neutrality means here — concretely.** Two notions operate: between *participants* (symmetric skepticism, depth, tone) and between *propositions* (no steering toward a conclusion — *not* a forced 50/50 split of Buoy's responses across participants, since interventions depend on what they actually say). The eval is built on two kinds of bias: *decision-level* (whom you intervene on, what you demand evidence for) and *expression-level* (how you word an otherwise-equivalent intervention).

**A two-layer mini-constitution** implements this ([CONSTITUTIONv0.1.md](CONSTITUTIONv0.1.md)):

- **Model-facing clauses (1–10)** — serve deliberation not a conclusion; same criteria regardless of participant/position; minimum intervention; clarified disagreement as success; symmetry of expression; no reward for style/confidence; equal verification effort; contestability with uptake. **Each clause is tied to a measurable Part-4 signal**, so the constitution is *falsifiable*: it asserts neutrality; the metric tests it.
- **Harness-enforced commitments (H1–H3)** — properties the *architecture* guarantees even if the model ignores every instruction: every decision logged including no-ops (H1); **name-blindness by construction** (H2) — the moderator reasons over labels P1/P2 and the output schema literally cannot express a name (`target ∈ {P1, P2, null}`); versioned constitution, so every action is attributable to the rules that governed it (H3).

**Deliberate choices and trade-offs:** the best place to get a sense of this is the chat transcript, but here are a few of the trade-offs: single fixed topic (depth over breadth; tractable eval); minimal ephemeral identity for users (no accounts or auth); raw-transcript input first for evals, structured-state second (a `raw`/`raw+state` knob that doubles as an eval arm; the `raw+state` mode didn't get finished); no pro/con labels in the UI (the eval infers stance from what people *said*, without forcing false binaries). There are also some schema shortcuts to keep things simple, which are clear from the chat transcript. 

**Cut for time** (the architecture could enable this easily): the dossier of available facts for the moderator to rely on as evidence; structured debate-state input (`raw+state` knob exists); structured contestability *uptake* (see §3); the name-injection eval arm; different moderator model tests; ablations on seeing how bias might change if moderator knows the participants' names (and possibly infers demographics).

**The moderator cannot end the debate.** Early sketches had a shutdown for extreme cases, but the assignment assumes two good-faith adults. So, to not over-engineer for extreme edge cases, only participants end their own debate.

## 3. Enhancing, not replacing, the participants

Through the mini constitution, the moderator is barred from doing the participants' normative work: it never says who is right or pushes agreement (success can be the participants seeing their disagreement's *structure*).

The moderator's characterizations are **contestable with uptake** — e.g., "your disagreement is really about X" can be answered "no, it's about Y," which the constitution treats as authoritative (today that uptake is *conversational*; the *structured* version needs the cut state layer).

**What does an AI moderator add over a transcript, a search engine, or a human?** A transcript doesn't notice you're answering different questions; a human moderator has every one of these bias vectors but **no action log**.  A search engine, on its own, doesn't do either of these things. The distinctive thing isn't that Buoy is neutral; it's that its neutrality is instrumented and auditable, down to individual silent decisions.

## 4. Measuring success

A debate succeeds when it reaches a *named* crux — agreement mapped, remaining disagreement classified (empirical → what evidence resolves it; value → the weighting difference named). Intervention rate is also relevant: a moderator that talks constantly fails regardless of quality.

**Bias eval.** This prototype defines bias as a **measurable asymmetry, at any stage of the decision cycle, that tracks participant or position rather than the quality of reasons**. Because every action is logged by stage, it is *attributable*. 

To evaluate this, we look at **counterfactual paired transcripts**: constructed debates with symmetric probes on each side, run in both seat arrangements ("pro"→P1/"anti"→P2 and the swap) so averaging isolates *position* from *seat* bias. The real `decide()` is scored after each turn on linked signals (intervention rate, justification-demands, skeptical language, length). The set runs repeatedly so a delta that **flips sign across runs is exposed as variance or noise, not bias**.

**What v0.1 showed** ([full results](bias-eval-v0.1.md); Sonnet 5, 3 runs, 72 decisions)**:** No systematic *position* bias. The pooled "pro"/"anti" gap flipped sign across runs. Seat treatment was near-symmetric, as name-blinding (H2 in the mini constitution) predicts; a small residual P1>P2 skew is a turn-order artifact (there are no identities in the input in the prototype). 

The clearest finding is that **intervention rate ≈ 0.6**. Buoy can interject too often once a debate is underway, the concrete target for a v0.2 constitution (wired via config, deferred for time). However, there are some important caveats: small N; deterministic signals only (we didn't have time to test an LLM judge or other classifier); and probes aren't calibrated for equal degree-of-falseness, so an apparent lean can actually reflect *correct fact-sensitivity* rather than bias, which I didn't have time to evaluate. 

## 5. Scaling

**Many debates:** This is already enabled with one stateless cycle per message, sessions independent (single-writer SQLite → Postgres + a worker pool is mechanical). It currently isn't implemented in a scalable-systems way, but it is scalable by design. 

**Many topics:** Topic is a table row and the constitution is topic-agnostic; per-topic work is the (human-curated) dossier, but could easily be supported/ extended from the current implementation.

**Larger groups:** labels generalize (P1 ... Pn), as do the metrics and taxonomy. But there are much larger questions of multi-person dynamics, things that have to do with coalitions / taking sides when n>2, which is a subject for richer future work.

**Integration:** one structured API call plus a log schema drops into any Claude surface hosting multi-party conversation.

## Known limitations (deliberate)

Choices scoped down/ made cheaply for the prototype: **in-process background execution** (a FastAPI background task, no durable queue; but a failed call is logged as a *distinguishable* no-op, so "chose silence" ≠ "call failed"); **rapid-fire race** (concurrent cycles see slightly different transcripts; per-message idempotency is enforced, which makes things a bit slower but consistent; cross-message staleness accepted); **ephemeral identity** (a per-session cookie ties a browser to a seat); **abandoned sessions** accumulate.

## How Claude was used

Built with Claude Code under explicit working rules ([CLAUDE.md](CLAUDE.md)). I approved and reviewed everything and wrote much of the code myself (in parallel with Claude on other features), then handed it to Claude to edit, review, and test. Design forks deliberately halted for me to decide rather than letting Claude guess. Provenance is traceable: [my-notes.md](my-notes.md) (brain dump) → [DESIGN.md](DESIGN.md) (decisions) → [CONSTITUTIONv0.1.md](CONSTITUTIONv0.1.md) → code. The complete Claude transcripts are submitted alongside.
