"""Environment-driven settings.

Kept tiny on purpose. `DATABASE_PATH` points at the SQLite file — locally it
defaults to `buoy.db` in the repo (gitignored); on Render it's
`/var/data/buoy.db` on the persistent disk. `BUOY_MODEL` is provisional and gets
confirmed against the claude-api skill at T4.
"""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_path: str = os.environ.get("DATABASE_PATH", "buoy.db")
    anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")
    # Default Opus 5 (quality-critical neutrality judgments); BUOY_MODEL overrides
    # (e.g. claude-sonnet-5). Cost tuning is a later, dedicated conversation.
    model: str = os.environ.get("BUOY_MODEL", "claude-opus-5")


settings = Settings()
