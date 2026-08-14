"""Session lifecycle + atomic seat-claiming.

Two seats per session, enforced atomically by the DB: the
`UNIQUE(session_id, seat_no)` and `UNIQUE(session_id, user_id)` constraints on
`SessionParticipant` mean concurrent joiners can't both grab seat 2 — the loser's
INSERT raises IntegrityError, which we translate into a clean "full"/"already"
outcome. See DESIGN/SPEC/TASKS for the concurrency stance.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session as DBSession
from sqlmodel import select

from .identity import new_token
from .models import (
    Moderator,
    Session as DebateSession,
    SessionParticipant,
    SessionState,
    SessionStatus,
    Topic,
)


class ClaimOutcome(str, Enum):
    seated = "seated"      # newly took a seat
    already = "already"    # already a participant (idempotent revisit)
    full = "full"          # both seats taken by others
    ended = "ended"        # session already ended


@dataclass
class ClaimResult:
    outcome: ClaimOutcome
    seat_no: Optional[int] = None


def _first_topic_id(db: DBSession) -> int:
    return db.exec(select(Topic.id).order_by(Topic.id)).first()


def _first_moderator_id(db: DBSession) -> int:
    return db.exec(select(Moderator.id).order_by(Moderator.id)).first()


def get_participant(
    db: DBSession, session_id: str, user_id: str
) -> Optional[SessionParticipant]:
    return db.exec(
        select(SessionParticipant).where(
            SessionParticipant.session_id == session_id,
            SessionParticipant.user_id == user_id,
        )
    ).first()


def taken_seats(db: DBSession, session_id: str) -> set[int]:
    return set(
        db.exec(
            select(SessionParticipant.seat_no).where(
                SessionParticipant.session_id == session_id
            )
        ).all()
    )


def create_session(db: DBSession, creator_user_id: str) -> DebateSession:
    """Create a waiting session, its empty state row, and seat the creator (1)."""
    ds = DebateSession(
        id=new_token(),
        topic_id=_first_topic_id(db),
        moderator_id=_first_moderator_id(db),
        status=SessionStatus.waiting,
    )
    db.add(ds)
    db.add(SessionState(session_id=ds.id, state={}))
    db.flush()  # persist session before the participant FK references it
    db.add(SessionParticipant(session_id=ds.id, seat_no=1, user_id=creator_user_id))
    db.commit()
    db.refresh(ds)
    return ds


def claim_seat(db: DBSession, ds: DebateSession, user_id: str) -> ClaimResult:
    """Seat `user_id` in session `ds`. Atomic against concurrent joiners."""
    existing = get_participant(db, ds.id, user_id)
    if existing:
        return ClaimResult(ClaimOutcome.already, existing.seat_no)
    if ds.status == SessionStatus.ended:
        return ClaimResult(ClaimOutcome.ended)

    taken = taken_seats(db, ds.id)
    if len(taken) >= 2:
        return ClaimResult(ClaimOutcome.full)

    seat = 1 if 1 not in taken else 2
    try:
        db.add(SessionParticipant(session_id=ds.id, seat_no=seat, user_id=user_id))
        db.commit()
    except IntegrityError:
        # Lost a race (seat taken) or double-submit (user already seated).
        db.rollback()
        existing = get_participant(db, ds.id, user_id)
        if existing:
            return ClaimResult(ClaimOutcome.already, existing.seat_no)
        return ClaimResult(ClaimOutcome.full)

    # Second seat filled -> the debate goes live.
    if len(taken_seats(db, ds.id)) >= 2 and ds.status == SessionStatus.waiting:
        ds.status = SessionStatus.live
        db.add(ds)
        db.commit()
    return ClaimResult(ClaimOutcome.seated, seat)


def end_session(db: DBSession, ds: DebateSession, ended_by: str) -> None:
    """Mark ended. `ended_by` is a user_id or the string 'moderator'."""
    if ds.status == SessionStatus.ended:
        return
    from datetime import datetime

    ds.status = SessionStatus.ended
    ds.ended_by = ended_by
    ds.ended_at = datetime.utcnow()
    db.add(ds)
    db.commit()
