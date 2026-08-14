"""End-to-end moderator cycle smoke — ONE real Claude call.

Sets up a live 2-participant session with a couple of turns, then runs the real
`run_cycle` (default decider = live API) and confirms it logged a ModeratorAction
without erroring. SKIPs when no key / no SDK.

    set -a; . ./.env; set +a; ./.venv/bin/python tests/smoke_cycle.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DATABASE_PATH"] = tempfile.mktemp(suffix=".db")


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("SKIP: ANTHROPIC_API_KEY not set — this smoke test hits the real API.")
        return 0
    try:
        import anthropic  # noqa: F401
    except ModuleNotFoundError:
        print("SKIP: `anthropic` not installed.")
        return 0

    from sqlmodel import Session, select
    from app.config import settings
    from app.db import engine, init_db
    from app.seed import seed
    from app.identity import create_user
    from app.lobby import create_session, claim_seat
    from app.messages import append_participant_message
    from app.moderator.loop import run_cycle
    from app.models import Message, ModeratorAction, Session as DebateSession

    init_db()
    seed()
    with Session(engine) as db:
        aid = create_user(db, "Alice").id
        sid = create_session(db, aid).id
        bid = create_user(db, "Bob").id
        claim_seat(db, db.get(DebateSession, sid), bid)  # -> live
        append_participant_message(
            db, sid, aid,
            "Congestion pricing is just a tax on working people who have to drive in.")
        m = append_participant_message(
            db, sid, bid,
            "It cuts traffic and funds transit, so it helps commuters overall.").id

    print(f"Running one real cycle ({settings.model})...")
    run_cycle(sid, m)  # real decider

    with Session(engine) as db:
        act = db.exec(
            select(ModeratorAction).where(ModeratorAction.after_message_id == m)
        ).first()
        assert act is not None, "cycle logged no action"
        err = (act.state_snapshot or {}).get("error")
        assert err is None, f"cycle errored: {err}"
        print("PASS — cycle logged a real ModeratorAction:")
        print(f"  decision          = {act.decision.value}")
        print(f"  intervention_type = {act.intervention_type}")
        print(f"  target_user_id    = {act.target_user_id}")
        print(f"  rationale         = {act.rationale}")
        if act.message_id:
            print(f"  posted message    = {db.get(Message, act.message_id).content}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
