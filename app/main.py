"""Buoy — FastAPI app (T3: lobby + chat).

Routes:
  GET  /                     landing (topic + "start a new session")
  POST /sessions             create session, seat creator, set cookie -> room
  GET  /s/{sid}              room | join form | full | ended (viewer-dependent)
  POST /s/{sid}/join         claim seat 2 -> room
  POST /s/{sid}/messages     append a participant message (HTMX; live only)
  GET  /s/{sid}/messages     the message list (HTMX poll target)
  GET  /s/{sid}/status       HX-Refresh trigger when status changes
  POST /s/{sid}/end          end the debate (either participant)

Only the in-room chat uses HTMX (message poll + composer + status watcher);
create/join/end are plain form POSTs + redirects. Moderator is not wired yet (T5).
"""
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session as DBSession
from sqlmodel import select

from .db import get_session, init_db
from .identity import create_user, get_session_user, set_session_cookie
from .lobby import (
    ClaimOutcome,
    claim_seat,
    create_session,
    end_session,
    get_participant,
    taken_seats,
)
from .messages import append_participant_message, messages_since
from .moderator.loop import run_cycle
from .models import (
    Moderator,  # noqa: F401  (ensure registered)
    Session as DebateSession,
    SessionParticipant,
    SessionStatus,
    Topic,
    User,
)
from .seed import seed

BASE_DIR = Path(__file__).resolve().parent


async def lifespan(app: FastAPI):
    init_db()
    seed()
    yield


# FastAPI accepts an async generator via contextlib; wrap it.
from contextlib import asynccontextmanager  # noqa: E402

app = FastAPI(title="Buoy", lifespan=asynccontextmanager(lifespan))
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# --- helpers ---------------------------------------------------------------

def _topic_question(db: DBSession) -> str:
    t = db.exec(select(Topic).order_by(Topic.id)).first()
    return t.question if t else "(no topic found in the database)"


def _participant_names(db: DBSession, sid: str) -> dict[int, str]:
    """seat_no -> display_name for the session's participants."""
    rows = db.exec(
        select(SessionParticipant.seat_no, User.display_name)
        .join(User, User.id == SessionParticipant.user_id)
        .where(SessionParticipant.session_id == sid)
    ).all()
    return {seat: name for seat, name in rows}


def _message_rows(db: DBSession, sid: str, me_id: str | None) -> list[dict]:
    """Render-ready rows: label + kind (me/other/buoy/system) + content."""
    # user_id -> "DisplayName (P1)" so each participant can tell which of Buoy's
    # P1/P2 references is them.
    labels = {}
    part = db.exec(
        select(User.id, User.display_name, SessionParticipant.seat_no)
        .join(SessionParticipant, SessionParticipant.user_id == User.id)
        .where(SessionParticipant.session_id == sid)
    ).all()
    for uid, name, seat in part:
        labels[uid] = f"{name} (P{seat})"
    rows = []
    for m in messages_since(db, sid, 0):
        if m.author_type.value == "participant":
            kind = "me" if m.author_user_id == me_id else "other"
            label = labels.get(m.author_user_id, "Participant")
        elif m.author_type.value == "moderator":
            kind, label = "buoy", "Buoy"
        else:
            kind, label = "system", ""
        rows.append({"label": label, "kind": kind, "content": m.content})
    return rows


# --- routes ----------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: DBSession = Depends(get_session)):
    return templates.TemplateResponse(
        "index.html", {"request": request, "topic_question": _topic_question(db)}
    )


@app.post("/sessions")
def start_session(
    request: Request,
    display_name: str = Form(""),
    db: DBSession = Depends(get_session),
):
    name = display_name.strip() or "Participant A"
    user = create_user(db, name)
    ds = create_session(db, user.id)
    resp = RedirectResponse(url=f"/s/{ds.id}", status_code=303)
    set_session_cookie(resp, ds.id, user.id)
    return resp


@app.get("/s/{sid}", response_class=HTMLResponse)
def room(sid: str, request: Request, db: DBSession = Depends(get_session)):
    ds = db.get(DebateSession, sid)
    if ds is None:
        return HTMLResponse("Session not found.", status_code=404)

    user = get_session_user(request, db, sid)
    participant = get_participant(db, sid, user.id) if user else None
    ctx = {
        "request": request,
        "sid": sid,
        "topic_question": _topic_question(db),
        "status": ds.status.value,
        "names": _participant_names(db, sid),
        "me_id": user.id if user else None,
        "is_participant": participant is not None,
        "join_url": str(request.url_for("room", sid=sid)),
    }

    if participant is not None:
        return templates.TemplateResponse("room.html", ctx)
    if ds.status == SessionStatus.ended:
        return templates.TemplateResponse("room.html", ctx)  # read-only spectator
    if len(taken_seats(db, sid)) >= 2:
        return templates.TemplateResponse("full.html", ctx)
    return templates.TemplateResponse("join.html", ctx)


@app.post("/s/{sid}/join")
def join(
    sid: str,
    request: Request,
    display_name: str = Form(""),
    db: DBSession = Depends(get_session),
):
    ds = db.get(DebateSession, sid)
    if ds is None:
        return HTMLResponse("Session not found.", status_code=404)

    # Already in (cookie present)? Just go to the room.
    existing_user = get_session_user(request, db, sid)
    if existing_user and get_participant(db, sid, existing_user.id):
        return RedirectResponse(url=f"/s/{sid}", status_code=303)

    name = display_name.strip() or "Participant B"
    user = create_user(db, name)
    result = claim_seat(db, ds, user.id)
    if result.outcome in (ClaimOutcome.seated, ClaimOutcome.already):
        resp = RedirectResponse(url=f"/s/{sid}", status_code=303)
        set_session_cookie(resp, sid, user.id)
        return resp
    # full or ended
    return RedirectResponse(url=f"/s/{sid}", status_code=303)


@app.post("/s/{sid}/messages")
def post_message(
    sid: str,
    request: Request,
    background: BackgroundTasks,
    content: str = Form(...),
    db: DBSession = Depends(get_session),
):
    ds = db.get(DebateSession, sid)
    user = get_session_user(request, db, sid)
    if ds is None or user is None or not get_participant(db, sid, user.id):
        return Response(status_code=403)
    if ds.status != SessionStatus.live:
        return Response(status_code=409)  # not live
    text = content.strip()
    if text:
        msg = append_participant_message(db, sid, user.id, text)
        # Moderator runs AFTER the response is sent, in a threadpool (sync fn),
        # so the blocking Claude call never blocks the poster or the event loop.
        background.add_task(run_cycle, sid, msg.id)
    return Response(status_code=204)  # composer resets client-side; poll shows it


@app.get("/s/{sid}/messages", response_class=HTMLResponse)
def get_messages(sid: str, request: Request, db: DBSession = Depends(get_session)):
    user = get_session_user(request, db, sid)
    rows = _message_rows(db, sid, user.id if user else None)
    return templates.TemplateResponse(
        "_messages.html", {"request": request, "rows": rows}
    )


@app.get("/s/{sid}/status")
def status_watch(
    sid: str, seen: str = "", db: DBSession = Depends(get_session)
):
    ds = db.get(DebateSession, sid)
    if ds is None:
        return Response(status_code=404)
    if ds.status.value != seen:
        return Response(status_code=200, headers={"HX-Refresh": "true"})
    return Response(status_code=204)


@app.post("/s/{sid}/end")
def end(sid: str, request: Request, db: DBSession = Depends(get_session)):
    ds = db.get(DebateSession, sid)
    user = get_session_user(request, db, sid)
    if ds is not None and user is not None and get_participant(db, sid, user.id):
        end_session(db, ds, ended_by=user.id)
    return RedirectResponse(url=f"/s/{sid}", status_code=303)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
