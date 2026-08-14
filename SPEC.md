# Buoy — Technical Spec

The **what/how to build** (companion to `DESIGN.md`, the *why*). Draft for review;
iterate freely. Scope for today: **T2 schema · T3 lobby/chat · T4 API wiring.**
The moderator's *intelligence* (T5) is tomorrow — this spec defines its
*interfaces* so today's plumbing fits it.

## Decisions folded in

- **Stack:** FastAPI + HTMX + SQLite via **SQLModel** (typed models, plays well
  with FastAPI). Polling for real-time (~2 s). Single uvicorn worker.
- **Moderator:** one structured Claude call → `{intervene?, type, target,
  rationale, text}`. Invoked after each participant message; mostly no-ops.
- **Retrieval:** curated dossier direction, deferred.

## Module layout

```
app/
  main.py             # FastAPI app + route wiring
  config.py           # env: DATABASE_PATH, ANTHROPIC_API_KEY, BUOY_MODEL
  db.py               # engine (WAL pragmas), init_db(), session dependency
  models.py           # SQLModel tables (below)
  identity.py         # cookie-based user token; current-user dependency
  lobby.py            # session lifecycle + atomic seat-claiming
  messages.py         # append + fetch-since (authoritative ordering)
  moderator/
    __init__.py
    schema.py         # Decision pydantic model (structured-output contract)
    client.py         # Anthropic SDK wrapper (T4)
    constitution.py   # system prompt / principles (T5)
    loop.py           # decision cycle orchestration (T5 stub today)
    state.py          # SessionState read/update (T5)
  templates/
    index.html        # landing / lobby
    room.html         # debate room (participant view)
    _messages.html    # HTMX partial: the message list (polled)
    full.html         # "session full" / ended read-only view
```

## Data model (SQLModel tables)

IDs: external-facing tokens (`Session.id`, `User.id`) are URL-safe random strings
(unguessable); `Message.id` is an **INTEGER PRIMARY KEY AUTOINCREMENT** (the
authoritative order).

- **Topic**(`id` int pk, `question` str). Seed one row (congestion pricing).
- **User**(`id` str pk = token, `display_name` str, `created_at` dt). Token is the
  cookie value = minimal identity.
- **Moderator**(`id` int pk, `model` str, `config` JSON, `created_at` dt). Seed one
  default row. `config` = `{input_mode: "raw"|"raw+state", temperature, ...}`.
- **Session**(`id` str pk = token, `topic_id` fk, `moderator_id` fk, `status`
  enum(`waiting`,`live`,`ended`), `ended_by` str? (user_id | "moderator"),
  `created_at`, `ended_at`?).
- **SessionParticipant**(`id` int pk, `session_id` fk, `seat_no` int∈{1,2},
  `user_id` fk, `joined_at`). Constraints: `UNIQUE(session_id, seat_no)`,
  `UNIQUE(session_id, user_id)`. ← atomic seat-claiming.
- **Message**(`id` int pk autoincrement, `session_id` fk, `author_type`
  enum(`participant`,`moderator`), `author_user_id` fk?, `role` str, `content`
  str, `created_at` dt, `metadata` JSON). Index `(session_id, id)`.
- **ModeratorAction**(`id` int pk, `session_id` fk, `after_message_id` fk,
  `decision` enum(`intervene`,`noop`), `intervention_type` str?, `target_user_id`
  fk?, `rationale` str, `message_id` fk?, `state_snapshot` JSON?, `created_at`).
- **SessionState**(`session_id` str pk fk, `state` JSON, `updated_at`). One row
  per session, updated in place; per-action snapshots also live in
  `ModeratorAction.state_snapshot`.

### Structured debate-state — two homes (authoritative; do NOT re-pull from `my-notes.md`)

The tracked debate structure splits across two places we already have:

1. **Moderator attention / action history → the `ModeratorAction` table**
   (first-class, queryable; every decision incl. no-ops). *Not* deferred — built in T2.
2. **Claims · support/rebuttal · open questions · agreements · candidate cruxes ·
   evidence-resolvable questions → `SessionState.state` (JSON), now.** The shape is
   still an open question (T5), so JSON avoids migrations while we iterate. Promote
   sub-structures to real tables at T5 *if/when* we need to query across them
   (access pattern decides). Pointer already exists: `SessionState.session_id` is
   1:1 with `Session`. Nothing here precludes that promotion.

## Session lifecycle / routes

```
GET  /                       landing: topic + "Start a new session"
POST /sessions               create Session(status=waiting); create creator User
                             (set cookie); claim seat 1; redirect → /s/{id}
GET  /s/{id}                 debate room. Resolve viewer:
                               - participant of this session  → room (their seat)
                               - open seat & status≠ended     → claim seat 2,
                                 set status=live, room
                               - full & not participant       → full.html
                               - status=ended                 → read-only transcript
POST /s/{id}/messages        guard: viewer is participant & status=live →
                             append participant Message (atomic) → kick moderator
                             cycle (T5; no-op stub today) → 204/partial
GET  /s/{id}/messages?since= return Messages with id > since, ordered by id
                             (rendered via _messages.html for HTMX swap)
POST /s/{id}/end             guard: viewer is participant → status=ended,
                             ended_by=user_id, ended_at=now
GET  /healthz                liveness (exists)
```

HTMX: room polls `GET /s/{id}/messages?since={last_id}` every ~2 s and appends new
rows; the composer `POST`s to `/s/{id}/messages`.

### Seat-claiming (atomic)

```
try: INSERT SessionParticipant(session_id, seat_no=N, user_id) inside txn
except IntegrityError (UNIQUE):        # seat taken
     if user already seated here → OK (idempotent rejoin)
     elif other seat open       → retry other seat
     else                       → session full
```

## Message ordering & concurrency

- Engine pragmas at startup: `journal_mode=WAL`, `busy_timeout=5000`,
  `foreign_keys=ON`, `synchronous=NORMAL`.
- Order = `Message.id` (autoincrement). Clients poll `since={max_id_seen}`; never
  sort by client clock.
- **No DB lock during the Claude call:** read transcript/state (quick) → call API
  (slow, no txn) → short txn to insert ModeratorAction (+ Message if intervening)
  + update SessionState.
- Single uvicorn worker (SQLite single writer). Enforced by `numInstances: 1`.

## Moderator loop interface (logic = T5; wiring = T4)

```python
# moderator/schema.py — the structured-output contract
class Decision(BaseModel):   # intervention_type = provisional set; FINAL CULL @ T5
    intervene: bool
    intervention_type: Literal[
        # engagement
        "note_talking_past","surface_neglected_claim","note_unanswered_challenge",
        "note_misread","prompt_engagement_with_strongest",
        # meaning/structure
        "clarify_term","invite_clarification","mark_agreement","summarize_state",
        "identify_crux",
        # epistemic
        "request_justification","supply_evidence","correct_factual_error",
        "flag_uncertainty",
        # conduct
        "check_tone",
        "none",
    ] = "none"
    target_user_id: str | None = None      # None = addressed to both
    crux_type: Literal["empirical","value","mixed"] | None = None  # iff identify_crux
    rationale: str                          # why (logged, not necessarily shown)
    intervention_text: str | None = None    # shown only if intervene

# Moderator INPUT uses neutral labels (P1/P2), NOT display_name — name-blinding by
# construction (DESIGN.md); name-injection is a Part-4 eval arm.

def run_cycle(session_id, after_message_id) -> ModeratorAction:
    # T5: build input (transcript [+ state per config.input_mode]),
    #     call client.decide(...), log action, maybe post Message, update state.
    # TODAY: stub that always returns decision=noop (records nothing / no-op),
    #        so T3 chat works end-to-end without moderator intelligence.
```

## Claude API wiring (T4)

- SDK: `anthropic` (add to requirements). Key via `ANTHROPIC_API_KEY` env (Render
  env var; local `.env`, gitignored).
- Model via `BUOY_MODEL` env → stored on the Moderator row. Default: **Sonnet 5**
  (`claude-sonnet-5`) for latency/cost; Opus 5 as a quality option. *(Confirm
  exact IDs/params against the `claude-api` skill before writing the client.)*
- **Structured output:** force the `Decision` schema via tool-use (single tool the
  model must call), so the moderator's decision is machine-readable and loggable.
- T4 deliverable: `client.decide(system, transcript, state) -> Decision` + a smoke
  test hitting the real API once.

## Config / env

| var                | where            | purpose                          |
|--------------------|------------------|----------------------------------|
| `DATABASE_PATH`    | Render + local   | SQLite file (`/var/data/buoy.db`)|
| `ANTHROPIC_API_KEY`| Render + `.env`  | Claude API auth                  |
| `BUOY_MODEL`       | Render + local   | default moderator model id       |

## Open holes (fill as they surface)

- `display_name`: **DECIDED** — user-chosen on join, fallback "Participant A/B";
  stored separate from the seat. Humans see names; **moderator input uses neutral
  labels P1/P2** (name-blinding by construction).
- Ended-session read-only view: full transcript incl. moderator actions? (lean: yes)
- What of the moderator's rationale/state do participants see? (DESIGN Q9 — T5/T6)
