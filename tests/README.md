# Tests

Lightweight but real tests for the parts most likely to break subtly. Documented
here because the design write-up references them.

Both are **self-contained** — each spins up its own throwaway SQLite DB (and, for
the walkthrough, its own server), so they never touch the dev or production DB.

## `test_seats.py` — atomic seat-claiming under a forced race

```bash
./.venv/bin/python tests/test_seats.py
```

The interesting failure mode is two people clicking "Join" at the same instant and
**both** landing in seat 2. This test provokes exactly that: two threads, held at a
`threading.Barrier`, hit `claim_seat` simultaneously, repeated 25 rounds. Each round
asserts:

- outcomes are exactly one **`seated`** + one **`full`** (never two seated),
- the seats end up `[1, 2]` (never `[1, 2, 2]`),
- status **flips `waiting` → `live`** when the second seat fills,
- a participant revisiting is **`already`** (idempotent),

plus a sequential check that a **third** joiner gets **`full`**.

What it proves: the atomicity we designed — `UNIQUE(session_id, seat_no)` +
IntegrityError handling in `app/lobby.py` — actually holds under contention.

## `walkthrough.sh` — end-to-end lobby + chat, two cookie identities

```bash
bash tests/walkthrough.sh
```

Drives the real HTTP surface with **two independent cookie jars** (Alice, Bob) plus
a third cookieless visitor (Carol):

1. Alice `POST /sessions` → **waiting** room, Seat 1 = Alice
2. Bob (no cookie) `GET /s/{id}` → **join form** (explicit join, not auto-claim)
3. Bob `POST /s/{id}/join` → redirect; session flips **live**
4. Alice's room now shows Seat 2 = Bob and the composer
5. Both `POST /s/{id}/messages` → `204`; `GET` returns them **in order**, with
   correct **me/other** attribution per viewer
6. Carol `GET /s/{id}` → **"session is full"**
7. Alice `POST /s/{id}/end` → room becomes read-only ("This debate has ended")
8. Posting after end → **`409`**

What it proves: identity, seat lifecycle, message ordering, and the end/read-only
transition all work over real requests — not just in unit-level calls.

## Not covered yet

- Moderator behavior (arrives in T5) and the bias-eval harness (T7).
- Front-end polling is exercised manually in the browser (HTMX `every 1.5s`).
