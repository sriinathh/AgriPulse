"""Engine/session management. SQLite for zero-setup dev, PostgreSQL/TimescaleDB for real use."""
from functools import lru_cache
from typing import Iterator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session, sessionmaker

from ..config import get_settings
import logging


def safe_database_url(url: str) -> str:
    """Render a DSN with the password hidden — safe to log or put in error messages."""
    try:
        return make_url(url).render_as_string(hide_password=True)
    except Exception:
        return "<unparseable DATABASE_URL>"


def build_engine(url: str) -> Engine:
    if url.startswith("sqlite"):
        engine = create_engine(url, connect_args={"check_same_thread": False})

        @event.listens_for(engine, "connect")
        def _fk_on(dbapi_conn, _):  # SQLite ignores foreign keys unless enabled
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

        return engine
    return create_engine(url, pool_pre_ping=True)


def verify_connection(engine: Engine) -> None:
    """Fail fast with an actionable message. Never includes credentials."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        kind = type(exc).__name__
        safe = safe_database_url(str(engine.url))
        hint = (
            "Cannot connect to the database at "
            f"{safe} ({kind}). "
            "Confirm the intended instance is running, the username exists on that instance, "
            "and the port matches docker-compose (TimescaleDB is published on host port 5433 "
            "because Windows PostgreSQL often already occupies 5432). "
            "Do not reset Docker volumes to work around authentication."
        )
        raise RuntimeError(hint) from exc


@lru_cache
def get_engine() -> Engine:
    try:
        engine = build_engine(get_settings().database_url)
        verify_connection(engine)
        return engine
    except RuntimeError as e:
        # Allow SQLite fallback only in test environments or when explicitly enabled.
        settings = get_settings()
        fallback_allowed = (
            settings.app_env.lower() == "test"
            or getattr(settings, "allow_sqlite_fallback", False)
        )
        if not fallback_allowed:
            # Propagate the original informative error; startup will fail.
            raise e
        log = logging.getLogger("irrigation")
        log.warning(
            "Database connection failed (%s). Falling back to in‑memory SQLite for testing.",
            e,
        )
        from sqlalchemy import create_engine
        return create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )



@lru_cache
def get_sessionmaker() -> sessionmaker:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = get_sessionmaker()()
    try:
        yield db
    finally:
        db.close()
