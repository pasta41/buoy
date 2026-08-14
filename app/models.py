"""SQLModel tables for Buoy.

Design rationale lives in SPEC.md ("Data model") and DESIGN.md. Highlights:
- `Message.id` is the authoritative conversation order (autoincrement int).
- Seat-claiming is made atomic by the two UNIQUE constraints on
  `SessionParticipant`.
- `ModeratorAction` logs *every* moderator decision including no-ops — this is
  one of the "two homes" for tracked debate-state (attention/action history);
  the other is `SessionState.state` (JSON).
"""
import enum
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, Index, UniqueConstraint
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.utcnow()


# --- enums -----------------------------------------------------------------

class SessionStatus(str, enum.Enum):
    waiting = "waiting"   # one seat filled; waiting for the second participant
    live = "live"         # both seats filled; debate active
    ended = "ended"       # concluded; read-only


class AuthorType(str, enum.Enum):
    participant = "participant"
    moderator = "moderator"
    system = "system"     # e.g. "P2 joined", "session ended"


class DecisionKind(str, enum.Enum):
    intervene = "intervene"
    noop = "noop"


# --- tables ----------------------------------------------------------------

class Topic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    question: str


class User(SQLModel, table=True):
    # id is a URL-safe token; it is also the cookie value (minimal identity).
    id: str = Field(primary_key=True)
    display_name: str
    created_at: datetime = Field(default_factory=utcnow)


class Moderator(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model: str
    config: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)


class Session(SQLModel, table=True):
    # id is a URL-safe token = the join URL.
    id: str = Field(primary_key=True)
    topic_id: int = Field(foreign_key="topic.id")
    moderator_id: int = Field(foreign_key="moderator.id")
    status: SessionStatus = Field(default=SessionStatus.waiting)
    ended_by: Optional[str] = None            # a user_id, or "moderator"
    created_at: datetime = Field(default_factory=utcnow)
    ended_at: Optional[datetime] = None


class SessionParticipant(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("session_id", "seat_no", name="uq_session_seat"),
        UniqueConstraint("session_id", "user_id", name="uq_session_user"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="session.id")
    seat_no: int                              # 1 or 2
    user_id: str = Field(foreign_key="user.id")
    joined_at: datetime = Field(default_factory=utcnow)


class Message(SQLModel, table=True):
    __table_args__ = (Index("ix_message_session_order", "session_id", "id"),)
    id: Optional[int] = Field(default=None, primary_key=True)  # authoritative order
    session_id: str = Field(foreign_key="session.id")
    author_type: AuthorType
    author_user_id: Optional[str] = Field(default=None, foreign_key="user.id")
    content: str
    created_at: datetime = Field(default_factory=utcnow)
    meta: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class ModeratorAction(SQLModel, table=True):
    # Exactly one action per participant message → idempotency + a clean
    # message→decision mapping for the eval ("did the moderator process msg X?").
    __table_args__ = (
        UniqueConstraint("session_id", "after_message_id", name="uq_action_per_message"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="session.id")
    after_message_id: int = Field(foreign_key="message.id")
    decision: DecisionKind
    intervention_type: Optional[str] = None   # string for now; cull enum at T5
    crux_type: Optional[str] = None           # empirical|value|mixed (iff identify_crux)
    target_user_id: Optional[str] = Field(default=None, foreign_key="user.id")
    rationale: str
    message_id: Optional[int] = Field(default=None, foreign_key="message.id")  # produced text
    state_snapshot: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON)
    )
    created_at: datetime = Field(default_factory=utcnow)


class SessionState(SQLModel, table=True):
    session_id: str = Field(primary_key=True, foreign_key="session.id")
    state: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=utcnow)
