# Tasks & Notes

Working tracker for the assignment. Working *rules* live in `CLAUDE.md`.

## Assignment

Rule of Law Team take-home (Anthropic Institute, technical role). Build a
**deployed prototype** where two people debate a contested topic with Claude as a
**moderator (not a judge)**. Four deliverables:

1. Deployed prototype (functional, one interaction pattern done well)
2. Code (GitHub repo)
3. Design rationale — self-recorded video (≤8 min) + short written doc
4. Bias-evaluation pipeline (describe, ideally implement against our own transcripts)

**Central challenge:** define *neutrality* concretely enough to build toward and
test for — not "I told Claude to be neutral."

- Source PDF: `/Users/cooper/Downloads/Rule_of_Law_Team_Take_Home_Assignment.pdf`
- **Topic (fixed):** should cities adopt **congestion pricing**? (rich empirical
  record; genuine reasonable-person disagreement; fixed topic makes Part 4 tractable)

## North star

- **"Buoy" = gentle guardrail.** Low-directiveness, bias-toward-silence
  moderation; nudge, don't adjudicate. Less intervention = smaller surface for bias.
- **Two neutralities, kept distinct:** neutrality *between participants*
  (symmetric skepticism / depth / tone) ≠ neutrality *between propositions*
  (don't force false 50/50 balance when evidence leans). Design + bias metric
  must each take a position on this.
- **No pro/con UI tags** — avoid baking in a false binary; also keeps eval
  position-inference honest (infer stance from what people said, not a label).
- AI moderator should do what a plain transcript / search engine / human
  moderator couldn't.

## Decisions locked

- **Stack:** FastAPI + HTMX + SQLite. (Cooper approved.)
- **Real-time:** start with HTMX polling (~2s); upgrade to SSE only if laggy.
- **Deploy:** **Render Starter ($7/mo) + 1 GB persistent disk + SQLite**, single
  instance (`numInstances: 1`; SQLite needs a single writer). DB at
  `/var/data/buoy.db` on the disk. GitHub remote exists: `pasta41/buoy`.
  (Chose paid+disk over free+Postgres to keep the SQLite stack; $7 acceptable.)
- **Sessions:** **lobby model** — "start new session" → get URL → partner joins →
  full; supports parallel sessions (grading + auto-generated Part-4 transcripts).
- **Identity:** minimal, no accounts. Per-browser token/cookie claims a seat;
  first two seats fill, third gets "session full."
- **Ending:** either participant ends → ends for both; moderator may end under
  extreme circumstances (later, moderation-logic concern). Schema carries
  `ended_by` (user | moderator).
- **Concurrency (favor correctness over latency):**
  - SQLite **WAL mode** + `busy_timeout`; single-writer serialization is a feature.
  - Authoritative message order = server-assigned autoincrement id. Clients render
    by id, never by client clock. All clients converge on next poll.
  - **Never hold a DB lock during a Claude API call.** Generate moderator response
    outside any transaction, then fast atomic insert.
  - Seat-claim race: transaction + `UNIQUE(session_id, seat)` → loser gets "full".
- **Moderator architecture:** **single structured Claude call** returns the whole
  decision `{intervene?, type, target, rationale, text}` — decision stays
  separable in the log without a 2nd round-trip. Chosen to narrow scope (document
  this in the final write-up). Invoked after each participant message; mostly no-ops.
- **Model:** default **`claude-opus-5`** (quality-critical neutrality judgments;
  `BUOY_MODEL` overrides, e.g. Sonnet 5). **T4 wiring verified live** (one real
  Opus-5 call → valid Decision). API key in `.env` (gitignored — never commit).
  **Cost levers = separate upcoming conversation (not yet decided).**
- **Retrieval (leaning; deferred, decide before T5):** a small **curated dossier**
  — a few cities' congestion-pricing material as a **bounded document set** the
  moderator retrieves over for empirical/factual info. **No general web lookup**
  (that's the rabbit hole we're avoiding). Upside: auditable + symmetric *by
  construction* (we control the corpus). Not blocking T2–T4.
- **DB layer:** SQLModel (Pydantic + SQLAlchemy) over the SQLite engine (typed
  models, clean with FastAPI). Full technical spec in `SPEC.md`.
- **Naming:** user-chosen `display_name` (fallback "Participant A/B"), stored
  separate from seat. Humans see names; **moderator input uses neutral labels
  P1/P2** (name-blinding by construction; name-injection is a Part-4 arm if time).
- **Intervention taxonomy + crux classification:** settled → see DESIGN.md
  ("Moderator action taxonomy & crux classification"). Crux `type ∈
  {empirical, value, mixed}`, contestable. Final enum *cull* deferred to T5.
- **Deferred micro-decisions (decide in context):** ended-session read-only view
  → at T3; default model id → at T4 (consult `claude-api` skill).

## Data model (Step 1)

**Full technical spec (columns, types, routes, lifecycle) → `SPEC.md`.** Summary:

- **Topic:** id, question. (Single topic for now.)
- **User:** id (token = cookie value), display_name, created_at.
- **Session:** id (urlsafe token = join URL), topic_id, moderator_id, status
  (waiting | live | ended), ended_by, timestamps. Participants tracked in a
  **SessionParticipant** table (session_id, seat_no ∈ {1,2}, user_id) with
  `UNIQUE(session_id, seat_no)` + `UNIQUE(session_id, user_id)` — this is the
  reconciliation of the earlier "two user_id columns" idea, needed for atomic
  seat-claiming. Live-vs-archived id: **DEFERRED**.
- **Moderator:** id, model, config (JSON: input_mode `raw`|`raw+state`, temp,
  constitution version…). model/config split deliberately for Part 4.
- **Message:** id (autoincrement = authoritative order), session_id, author_type
  (participant | moderator), author_user_id?, role, content, created_at,
  metadata (JSON). No "collaborated" messages.
- **ModeratorAction** (NEW — first-class, from the state-machine): id, session_id,
  after_message_id, decision (intervene | noop), intervention_type?, target_user_id?,
  rationale, message_id? (link if it produced text), state_snapshot?, created_at.
  *No-ops produce no Message but are still logged* → powers attention-tracking
  (constitution #8) + stage-level bias attribution (Part 4).
- **SessionState** (NEW — minimal now, not fully deferred): session_id, state
  (JSON: claims, open_challenges, agreements, candidate_cruxes, evidence_questions),
  updated_at. Richer support/rebuttal graph stays deferred.

**Structured debate-state → two homes** (authoritative; don't re-pull from
`my-notes.md`): moderator attention/action history → `ModeratorAction` table (built
in T2); everything else (claims, rebuttals, questions, agreements, cruxes,
evidence-questions) → `SessionState.state` JSON now, promotable to tables at T5.
Full note in `SPEC.md`.

Session status renamed `lobby` → **`waiting`** (waiting-room = one seat filled).

## Open

**Prototype (T1–T5) is done and deployed** (live moderated debate on prod).
Remaining, in priority order for the time left:

- [ ] **P4 — bias-eval pipeline (Deliverable 4, the central challenge).** Minimal
  counterfactual-swap implementation + honest findings. Backbone = the clause↔signal
  mapping (`CONSTITUTIONv0.1.md`). Generate a few paired transcripts (AI stand-in
  participants; swap positions), measure 2–3 signals (intervention rate,
  requests-for-justification by side, tone/length symmetry), report honestly incl.
  bias in our own system. Also yields the debate transcripts for submission.
- [ ] **P3 — design rationale (Deliverable 3).** Short written doc (assemble from
  DESIGN.md + `CONSTITUTIONv0.1.md`) + ≤8-min screenshare video (**Cooper records**).
- [ ] **Submission bundle:** Claude-transcript PDF (`tmp-outputs/` tooling), repo +
  prototype links, debate transcripts + bias output, video + doc.
- [ ] **If time only:** name-injection ablation arm; retrieval via web search; light
  "de-AI-speak" pass on `CONSTITUTIONv0.1.md`; intervention-type enum cull.

Descoped for time (discuss in the write-up) → DESIGN.md "Cut under time pressure".

## Closed

- [x] **T5:** moderator decision cycle + constitution v0.1 + rendering. Closed
  2026-08-13. Async background cycle (threadpool), injectable decider, log-always,
  distinguishable error-noop, per-message idempotency (UNIQUE + safe migration),
  label→id, **config-driven constitution** (A/B-ready). Constitution v0.1 rendered
  (clauses 1–7, 9, 10). Rendering B: collapsible "Buoy's reasoning". **Verified live
  on prod** (real moderated debate). Commits 9afb956, 63e8557, 2fda11b.
- [x] **T4:** Claude API wiring. Closed 2026-08-13. anthropic SDK, structured-output
  `Decision` (`messages.parse`); schema locked (1b + `target_participant` Literal).
  Verified live. Commit 5850249.
- [x] **T3:** lobby + chat end-to-end. Closed 2026-08-13. Per-session ephemeral
  identity; atomic seat-claiming (race-tested, 25 rounds); HTMX chat (message poll +
  status-watcher auto-reload on waiting→live + textarea Enter-to-send); create /
  join / end. Tests in `tests/`. Verified live at https://buoy-2ejg.onrender.com.
  Commit 5a579b5.
- [x] **T2:** data model + schema-on-boot + seed + DB-backed landing page.
  Closed 2026-08-13. 8 tables; atomic seat-claim constraints; WAL/pragmas; idempotent
  seed (topic upsert). Verified live on Render persistent disk (smoke test proved DB
  read; upsert proved clean update with data present). Commits da94f8e, e47d4fa.
- [x] **T1 (Step 0):** minimal FastAPI + HTMX skeleton deployed publicly.
  Closed 2026-08-13. Live: https://buoy-2ejg.onrender.com (`/` + `/healthz`
  verified). Pipeline proven: local → GitHub `pasta41/buoy` → Render Blueprint
  (Starter + 1 GB disk + SQLite). Deployment risk retired.
