"""Message append + fetch-since.

Ordering is server-authoritative via `Message.id` (autoincrement). Clients poll
with the highest id they've seen; we never sort by wall-clock. (T3 handles
participant messages only; the moderator writes messages in T5.)
"""
from typing import Sequence

from sqlmodel import Session as DBSession
from sqlmodel import select

from .models import AuthorType, Message


def append_participant_message(
    db: DBSession, session_id: str, user_id: str, content: str
) -> Message:
    msg = Message(
        session_id=session_id,
        author_type=AuthorType.participant,
        author_user_id=user_id,
        content=content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def messages_since(
    db: DBSession, session_id: str, since_id: int = 0
) -> Sequence[Message]:
    return db.exec(
        select(Message)
        .where(Message.session_id == session_id, Message.id > since_id)
        .order_by(Message.id)
    ).all()
