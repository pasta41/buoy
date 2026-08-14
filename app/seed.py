"""Idempotent seed data: the fixed Topic and a default Moderator.

Runs on startup (see main.py lifespan). The single fixed Topic is treated as
*code-controlled*: the DB row is reconciled to `TOPIC_QUESTION` on each boot, so
changing the constant and redeploying updates the live question. (Sessions
reference `topic_id`, never the text, so reconciling the text is safe.)
"""
from sqlmodel import Session, select

from .config import settings
from .db import engine
from .models import Moderator, Topic
from .moderator.constitution import CONSTITUTION_VERSION

# The single fixed topic (see TASKS.md). Open, neutral phrasing — no pro/con framing.
TOPIC_QUESTION = "Should cities adopt congestion pricing?"


def seed() -> None:
    with Session(engine) as session:
        topic = session.exec(select(Topic)).first()
        if topic is None:
            session.add(Topic(question=TOPIC_QUESTION))
        elif topic.question != TOPIC_QUESTION:
            topic.question = TOPIC_QUESTION           # keep the fixed topic in sync
            session.add(topic)
        # One moderator for now. `config.constitution_version` makes every action
        # attributable to the constitution text that governed it (H3); reconcile it
        # so an older seeded row (missing the version) is brought up to date. Model
        # is env-global (settings.model / BUOY_MODEL); constitution is per-moderator.
        want = {"input_mode": "raw", "constitution_version": CONSTITUTION_VERSION}
        mod = session.exec(select(Moderator)).first()
        if mod is None:
            session.add(Moderator(model=settings.model, config=want))
        elif mod.config != want or mod.model != settings.model:
            mod.model = settings.model
            mod.config = want
            session.add(mod)
        session.commit()
