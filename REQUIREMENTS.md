# Assignment Requirements Checklist

Tracks whether we've satisfied what the **assignment asks for** (distinct from
`TASKS.md`). Status as of final submission prep. Legend: [x] done · [~] partial ·
[ ] not started.

## Deliverables

- [x] **1. Deployed prototype** — publicly usable, two participants, Claude API.
  Live moderator works on prod (on-philosophy interventions). Single interaction
  pattern done well. https://buoy-2ejg.onrender.com
- [x] **2. Code** — GitHub `pasta41/buoy`, committed, tested (unit + e2e + smokes).
- [~] **3. Design rationale** — **written doc + video (≤8 min)**. Written doc DONE
  (`WRITE-UP.md`); **video pending** (record + drop the link in `README.md`). The
  doc covers every required point:
  - [x] which Objective capabilities we chose + **why**
  - [x] neutrality approach + **tradeoffs** (incl. the deliberate cuts)
  - [x] how it **enhances rather than replaces** participants' reasoning
  - [x] **learning / deliberation / rule-of-law** principles (Berlin, Habermas)
  - [x] how we'd **measure success**
  - [x] how it would **scale**
- [x] **4. Bias-evaluation pipeline** — BUILT + honest findings. `eval/` (harness)
  + `bias-eval-v0.1.md` (results).
  - [x] **operational** bias definition — CONSTITUTIONv0.1.md clause↔signal map
  - [x] generate/collect transcripts — constructed counterfactual scenarios
    (`eval/scenarios.py`); real debates also captured under `transcripts/`
  - [x] score/flag — counterfactual paired-transcript deltas, repeat-aggregated so
    sign-flips read as noise (position vs. seat isolated)
  - [x] what to do with results — versioned constitution revisions; v0.2 lever
    (intervention rate) identified
  - [x] **minimal implementation + honest findings** — incl. our own system
    (no systematic position bias at N; seat-neutral; intervention rate ~0.6)
  - [ ] LLM-judge for tone/expression symmetry (clause 9) — designed, not built

## Objective capabilities (engage with at least a few) — ✓ satisfied

- [x] keep the debate on track — **talking-past detection** works live (see
  `transcripts/`)
- [x] find the **crux** — taxonomy + crux-type; exercised in real debates + eval
- [ ] provide factual info **with sourcing** — **deliberately cut** (no dossier;
  clause 5 → flag-uncertainty). Documented in DESIGN.md / WRITE-UP.md.
- [x] decide **when to intervene vs. stay silent** — minimum-intervention / no-op bias
- [~] **track structure + present it back** — we surface interventions + reasoning;
  a running structured summary/crux board is descoped

## What they're evaluating

- [x] technical execution — built + iterated fast, deployed, tested
- [x] neutrality & epistemic integrity — **falsifiable** constitution (clause↔signal);
  Part-4 run with honest findings
- [x] user empathy — process-not-substance, minimum intervention, clarified-disagreement
- [x] clear communication — `WRITE-UP.md` (design rationale); DESIGN.md as the notebook
- [x] creative problem-solving — two-layer constitution; harness-enforced neutrality
- [x] scalability thinking — articulated in WRITE-UP.md §6

## Submission bundle (email)

- [x] GitHub repo link (`pasta41/buoy`)
- [x] working prototype link (https://buoy-2ejg.onrender.com)
- [x] **Claude transcript(s)** — `claude_transcript.md` (the full build session)
- [x] debate transcript(s) + bias write-up / pipeline output — `transcripts/`,
  `bias-eval-v0.1.md`, `eval/`
- [~] explanation artifacts — written doc DONE (`WRITE-UP.md`); **video pending**

## Constraints / assumptions (met)

- [x] Two good-faith adults, real contested topic (congestion pricing), non-extremist.
- [x] < 1 day for the prototype (depth > breadth).
