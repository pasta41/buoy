"""Atomic seat-claiming under a forced race.

Verifies that two participants racing for the last seat can never both get in:
the DB's UNIQUE(session_id, seat_no) constraint + our IntegrityError handling
yield exactly one `seated` and one `full`. Also checks the waiting->live flip,
idempotent revisit, and the third-joiner path.

Run (self-contained; uses a throwaway temp DB):
    ./.venv/bin/python tests/test_seats.py
"""
import os
import sys
import tempfile
import threading

# Make `app` importable and point the app at a throwaway DB BEFORE importing it.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DATABASE_PATH"] = tempfile.mktemp(suffix=".db")

from sqlmodel import Session, select  # noqa: E402

from app.db import engine, init_db  # noqa: E402
from app.seed import seed  # noqa: E402
from app.identity import create_user  # noqa: E402
from app.lobby import create_session, claim_seat, ClaimOutcome  # noqa: E402
from app.models import (  # noqa: E402
    Session as DebateSession,
    SessionParticipant,
    SessionStatus,
)

ROUNDS = 25


def main() -> None:
    init_db()
    seed()

    for r in range(ROUNDS):
        with Session(engine) as db:
            aid = create_user(db, f"A{r}").id
            bid = create_user(db, f"B{r}").id
            cid = create_user(db, f"C{r}").id
            sid = create_session(db, aid).id

        barrier = threading.Barrier(2)
        results: dict[str, object] = {}

        def racer(uid, key):
            with Session(engine) as db:
                ds = db.get(DebateSession, sid)
                barrier.wait()  # both threads hit claim_seat together
                results[key] = claim_seat(db, ds, uid).outcome

        t1 = threading.Thread(target=racer, args=(bid, "b"))
        t2 = threading.Thread(target=racer, args=(cid, "c"))
        t1.start(); t2.start(); t1.join(); t2.join()

        outcomes = sorted(o.value for o in results.values())
        with Session(engine) as db:
            seats = sorted(
                db.exec(
                    select(SessionParticipant.seat_no).where(
                        SessionParticipant.session_id == sid
                    )
                ).all()
            )
            status = db.get(DebateSession, sid).status
            again = claim_seat(db, db.get(DebateSession, sid), aid).outcome

        assert outcomes == ["full", "seated"], f"round {r}: outcomes={outcomes}"
        assert seats == [1, 2], f"round {r}: seats={seats}"
        assert status == SessionStatus.live, f"round {r}: status={status}"
        assert again == ClaimOutcome.already, f"round {r}: revisit={again}"

    print(f"PASS: {ROUNDS} rounds — seat-claim atomic under race; "
          "live-flip + idempotent revisit OK")

    # Third joiner after full (sequential).
    with Session(engine) as db:
        aid = create_user(db, "solo-A").id
        bid = create_user(db, "solo-B").id
        did = create_user(db, "solo-D").id
        sid = create_session(db, aid).id
        o_b = claim_seat(db, db.get(DebateSession, sid), bid).outcome
        o_d = claim_seat(db, db.get(DebateSession, sid), did).outcome
    assert o_b == ClaimOutcome.seated and o_d == ClaimOutcome.full, (o_b, o_d)
    print("PASS: third joiner gets 'full'")


if __name__ == "__main__":
    main()
