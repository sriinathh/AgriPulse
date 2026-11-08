from sqlalchemy.engine import Engine

from app import models  # noqa: F401  (registers tables on Base.metadata)
from app.database.base import Base
from app.database.migrate import apply_additive_migrations
from app.database.timescale import setup_timescale


def init_db(engine: Engine) -> bool:
    """Create tables; add missing columns; convert time-series tables to hypertables when TimescaleDB exists.
    Returns True if hypertables are active."""
    Base.metadata.create_all(engine)
    apply_additive_migrations(engine)
    return setup_timescale(engine)
