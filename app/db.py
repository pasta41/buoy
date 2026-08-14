"""Database engine + session plumbing.

SQLite tuned for our concurrency stance (see TASKS.md / SPEC.md):
- WAL so the ~2s polling reads never block the single writer;
- busy_timeout so a write waits its turn instead of erroring under contention;
- foreign_keys ON (SQLite leaves them off by default);
- synchronous=NORMAL (safe with WAL, faster than FULL).

These pragmas must run on *every* connection, hence the connect listener.
"""
from sqlalchemy import event
from sqlmodel import SQLModel, Session, create_engine

from .config import settings

DATABASE_URL = f"sqlite:///{settings.database_path}"

# check_same_thread=False: FastAPI may touch a connection from a worker thread.
# Safe here because SQLite still serializes writes and we run a single process.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA busy_timeout=5000;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.close()


def init_db() -> None:
    """Create tables, then apply the one-time ModeratorAction uniqueness migration."""
    from . import models  # noqa: F401  (registers tables on SQLModel.metadata)

    SQLModel.metadata.create_all(engine)

    # Migration: older DBs created `moderatoraction` before the
    # UNIQUE(session_id, after_message_id) constraint existed, and create_all won't
    # ALTER an existing table. If the constraint is missing AND the table is empty,
    # drop it so the second create_all recreates it with the constraint. The
    # empty-guard means this can never delete real data; it's a no-op once applied.
    with engine.begin() as conn:
        row = conn.exec_driver_sql(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='moderatoraction'"
        ).first()
        if row and row[0] and "uq_action_per_message" not in row[0]:
            count = conn.exec_driver_sql("SELECT count(*) FROM moderatoraction").scalar()
            if count == 0:
                conn.exec_driver_sql("DROP TABLE moderatoraction")
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency: one DB session per request."""
    with Session(engine) as session:
        yield session
