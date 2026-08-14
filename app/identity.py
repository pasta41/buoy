"""Per-session ephemeral identity (no accounts).

A name is entered per debate; the cookie `buoy_{session_id}` ties this browser to
its seat in *that* session. The cookie value is the `User.id`. See DESIGN.md
("Identity model + known limitations") for the "closes the window" behavior.
"""
import secrets
from typing import Optional

from fastapi import Request, Response
from sqlmodel import Session as DBSession

from .models import User

COOKIE_MAX_AGE = 60 * 60 * 24  # 1 day — long enough to rejoin during a debate


def new_token(nbytes: int = 16) -> str:
    return secrets.token_urlsafe(nbytes)


def cookie_name(session_id: str) -> str:
    return f"buoy_{session_id}"


def get_session_user(
    request: Request, db: DBSession, session_id: str
) -> Optional[User]:
    """The user this browser is playing *in this session*, or None."""
    uid = request.cookies.get(cookie_name(session_id))
    return db.get(User, uid) if uid else None


def create_user(db: DBSession, display_name: str) -> User:
    user = User(id=new_token(), display_name=display_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def set_session_cookie(response: Response, session_id: str, user_id: str) -> None:
    response.set_cookie(
        cookie_name(session_id),
        user_id,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
    )
