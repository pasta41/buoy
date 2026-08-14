"""Moderator decision cycle (T5).

Runs as a **sync** background task (FastAPI threadpool) after a participant
message, so the blocking Claude call never freezes the single worker's event
loop. The cycle:
  - reads the P1/P2-labelled transcript (name-blinded),
  - decides (via an **injectable `decide_fn`** — stubbable in tests, no API),
  - **always** logs a `ModeratorAction` (no-ops and failures too, distinguishably),
  - posts a moderator `Message` only when it intervenes.

Idempotent per participant message via `UNIQUE(session_id, after_message_id)` on
`ModeratorAction`. Sequencing + rationale live in DESIGN.md.
"""
from typing import Callable, Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session as DBSession
from sqlmodel import select

from ..db import engine
from ..models import (
    AuthorType,
    DecisionKind,
    Message,
    Moderator,
    ModeratorAction,
    Session as DebateSession,
    SessionParticipant,
    SessionStatus,
)
from .client import decide as real_decide
from .constitution import get_constitution
from .schema import Decision

# (system, transcript, state) -> Decision. Injected so tests can stub it.
DecideFn = Callable[[str, str, Optional[str]], Decision]


def _seat_labels(db: DBSession, session_id: str) -> dict[str, str]:
    """user_id -> 'P1'/'P2' for this session's seats."""
    rows = db.exec(
        select(SessionParticipant.user_id, SessionParticipant.seat_no).where(
            SessionParticipant.session_id == session_id
        )
    ).all()
    return {uid: f"P{seat}" for uid, seat in rows}


def label_to_user_id(
    db: DBSession, session_id: str, label: Optional[str]
) -> Optional[str]:
    """'P1'/'P2' -> the seat's real user_id — the one label→id translation step."""
    if label not in ("P1", "P2"):
        return None
    seat = 1 if label == "P1" else 2
    return db.exec(
        select(SessionParticipant.user_id).where(
            SessionParticipant.session_id == session_id,
            SessionParticipant.seat_no == seat,
        )
    ).first()


def build_transcript(db: DBSession, session_id: str) -> str:
    """Render messages as a neutral P1/P2-labelled transcript (name-blinded)."""
    labels = _seat_labels(db, session_id)
    lines: list[str] = []
    for m in db.exec(
        select(Message).where(Message.session_id == session_id).order_by(Message.id)
    ).all():
        if m.author_type == AuthorType.participant:
            lines.append(f"{labels.get(m.author_user_id, 'P?')}: {m.content}")
        elif m.author_type == AuthorType.moderator:
            lines.append(f"Buoy (moderator): {m.content}")
        # system messages are omitted from the moderator's view
    return "\n".join(lines)


def run_cycle(
    session_id: str,
    after_message_id: int,
    decide_fn: DecideFn = real_decide,
) -> None:
    """One moderator decision cycle. Sync; opens its own DB session."""
    with DBSession(engine) as db:
        # Fast-path idempotency: avoids a wasted decide() on a re-fire.
        if db.exec(
            select(ModeratorAction).where(
                ModeratorAction.session_id == session_id,
                ModeratorAction.after_message_id == after_message_id,
            )
        ).first() is not None:
            return

        ds = db.get(DebateSession, session_id)
        if ds is None or ds.status != SessionStatus.live:
            return  # only moderate live sessions

        trigger = db.get(Message, after_message_id)
        if trigger is None or trigger.author_type != AuthorType.participant:
            return  # fire only on participant messages — no self-trigger

        # Resolve the constitution from THIS session's moderator config (A/B-ready):
        # attribution flows session -> moderator -> config.constitution_version.
        moderator = db.get(Moderator, ds.moderator_id)
        system_prompt = get_constitution(
            (moderator.config or {}).get("constitution_version") if moderator else None
        )

        transcript = build_transcript(db, session_id)
        state = None  # raw mode: no structured state input

        # --- decide (may fail; never crash the request path) ---
        try:
            decision: Optional[Decision] = decide_fn(system_prompt, transcript, state)
            err: Optional[Exception] = None
        except Exception as exc:  # noqa: BLE001 — a flaky call must not 500 anything
            decision, err = None, exc
            print(
                f"[moderator] decide failed session={session_id} "
                f"after={after_message_id} request_id={getattr(exc, 'request_id', None)} "
                f"error={type(exc).__name__}: {exc}"
            )

        text = (decision.intervention_text or "").strip() if decision else ""
        will_post = decision is not None and decision.intervene and bool(text)

        # --- build the ModeratorAction (message_id backfilled iff we post) ---
        if err is not None:
            action = ModeratorAction(
                session_id=session_id, after_message_id=after_message_id,
                decision=DecisionKind.noop, intervention_type=None, crux_type=None,
                target_user_id=None,
                rationale=f"[error] decide failed: {type(err).__name__}",
                # distinguishable from a deliberate no-op in the eval:
                state_snapshot={"error": {
                    "type": type(err).__name__, "message": str(err),
                    "request_id": getattr(err, "request_id", None),
                }},
            )
        elif will_post:
            action = ModeratorAction(
                session_id=session_id, after_message_id=after_message_id,
                decision=DecisionKind.intervene,
                intervention_type=decision.intervention_type,
                crux_type=decision.crux_type,
                target_user_id=label_to_user_id(db, session_id, decision.target_participant),
                rationale=decision.rationale,
            )
        else:
            # genuine no-op, or an "intervene but empty text" anomaly (logged distinctly)
            anomaly = decision is not None and decision.intervene
            action = ModeratorAction(
                session_id=session_id, after_message_id=after_message_id,
                decision=DecisionKind.noop, intervention_type="none", crux_type=None,
                target_user_id=None, rationale=decision.rationale,
                state_snapshot=({"anomaly": "intervene_without_text",
                                 "intended_type": decision.intervention_type}
                                if anomaly else None),
            )

        # --- claim the per-message slot (UNIQUE backstop). Lost race -> bail. ---
        try:
            db.add(action)
            db.commit()
            db.refresh(action)
        except IntegrityError:
            db.rollback()
            return  # another cycle already handled this message

        # --- only now, for a real intervention, post the Message + link it ---
        if will_post:
            msg = Message(
                session_id=session_id, author_type=AuthorType.moderator,
                author_user_id=None, content=text,
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)
            action.message_id = msg.id
            db.add(action)
            db.commit()

        # update SessionState — no-op in raw mode
