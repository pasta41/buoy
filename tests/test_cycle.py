"""Moderator decision cycle — deterministic, API-free (stubbed decider).

Exercises the whole cycle with injected `decide_fn` stubs, so nothing here hits
the Claude API. Verifies: log-always, no-op, intervene (+ label→id + linked
Message), per-message idempotency, no self-trigger, and that a failed call is
logged as a *distinguishable* no-op.

    ./.venv/bin/python tests/test_cycle.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DATABASE_PATH"] = tempfile.mktemp(suffix=".db")

from sqlmodel import Session, select  # noqa: E402

from app.db import engine, init_db  # noqa: E402
from app.seed import seed  # noqa: E402
from app.identity import create_user  # noqa: E402
from app.lobby import create_session, claim_seat  # noqa: E402
from app.messages import append_participant_message  # noqa: E402
from app.moderator.loop import run_cycle  # noqa: E402
from app.moderator.schema import Decision  # noqa: E402
from app.models import (  # noqa: E402
    AuthorType, DecisionKind, Message, ModeratorAction,
    Session as DebateSession,
)


# --- stub deciders (never touch the API) ------------------------------------
def stub_noop(system, transcript, state):
    return Decision(intervention_type="none", target_participant=None,
                    crux_type=None, rationale="stub: too early", intervention_text=None)


def stub_intervene(system, transcript, state):
    return Decision(intervention_type="surface_neglected_claim", target_participant="P1",
                    crux_type=None, rationale="stub: P1 left a point unaddressed",
                    intervention_text="P1, P2 raised a point you haven't addressed yet.")


def stub_error(system, transcript, state):
    raise RuntimeError("simulated API failure")


def main() -> None:
    init_db()
    seed()

    with Session(engine) as db:
        aid = create_user(db, "Alice").id
        sid = create_session(db, aid).id
        bid = create_user(db, "Bob").id
        claim_seat(db, db.get(DebateSession, sid), bid)  # -> live
        m1 = append_participant_message(db, sid, aid, "Congestion pricing is regressive.").id

    # no-op, then a re-fire for the SAME message (idempotency)
    run_cycle(sid, m1, decide_fn=stub_noop)
    run_cycle(sid, m1, decide_fn=stub_noop)
    with Session(engine) as db:
        acts = db.exec(select(ModeratorAction).where(ModeratorAction.after_message_id == m1)).all()
        assert len(acts) == 1, f"idempotency: expected 1 action, got {len(acts)}"
        assert acts[0].decision == DecisionKind.noop and acts[0].message_id is None
        assert (acts[0].state_snapshot or {}).get("error") is None  # genuine no-op
        mod = db.exec(select(Message).where(
            Message.session_id == sid, Message.author_type == AuthorType.moderator)).all()
        assert len(mod) == 0, "no-op must post no moderator message"
    print("PASS: no-op logged + idempotent + no message")

    # intervene: logs action, posts a moderator message, maps P1 -> Alice
    with Session(engine) as db:
        m2 = append_participant_message(db, sid, bid, "It funds transit, so it helps.").id
    run_cycle(sid, m2, decide_fn=stub_intervene)
    with Session(engine) as db:
        act = db.exec(select(ModeratorAction).where(ModeratorAction.after_message_id == m2)).first()
        assert act.decision == DecisionKind.intervene and act.intervention_type == "surface_neglected_claim"
        assert act.target_user_id == aid, "P1 must map to seat-1 user (Alice)"
        msg = db.get(Message, act.message_id)
        assert msg and msg.author_type == AuthorType.moderator and "haven't addressed" in msg.content
        mod_msg_id = act.message_id
    print("PASS: intervene logged + P1->user_id + linked moderator message")

    # no self-trigger: running the cycle on the moderator's own message does nothing
    run_cycle(sid, mod_msg_id, decide_fn=stub_intervene)
    with Session(engine) as db:
        a = db.exec(select(ModeratorAction).where(ModeratorAction.after_message_id == mod_msg_id)).all()
        assert len(a) == 0, "moderator must not act on its own message"
    print("PASS: no self-trigger")

    # failure -> distinguishable no-op (carries an error marker)
    with Session(engine) as db:
        m3 = append_participant_message(db, sid, aid, "But it's a tax on the poor.").id
    run_cycle(sid, m3, decide_fn=stub_error)
    with Session(engine) as db:
        act = db.exec(select(ModeratorAction).where(ModeratorAction.after_message_id == m3)).first()
        assert act.decision == DecisionKind.noop
        err = (act.state_snapshot or {}).get("error")
        assert err and err["type"] == "RuntimeError", f"error marker missing: {act.state_snapshot}"
    print("PASS: failed call -> distinguishable no-op (error marker set)")

    print("ALL PASS")


if __name__ == "__main__":
    main()
