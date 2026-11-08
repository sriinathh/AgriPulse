"""Optional TimescaleDB setup. Plain PostgreSQL and SQLite are fully supported without it:
if the extension is unavailable we log a warning and carry on with ordinary tables."""
import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine

log = logging.getLogger(__name__)

# (table, id column, time column). Hypertables need the time column inside every unique key,
# so the primary key is widened from (id) to (id, time). Unique (sensor_id, timestamp) already
# includes the partition column.
HYPERTABLES = [
    ("sensor_readings", "reading_id", "timestamp"),
    ("weather_data", "weather_id", "timestamp"),
]


def setup_timescale(engine: Engine) -> bool:
    if engine.dialect.name != "postgresql":
        log.info("TimescaleDB skipped: dialect is %s, not postgresql.", engine.dialect.name)
        return False
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
            row = conn.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'")).first()
            log.info("TimescaleDB extension enabled (version %s).", row[0] if row else "unknown")
    except Exception as exc:  # extension not installed / no permission
        log.warning(
            "TimescaleDB not available (%s: %s); using plain PostgreSQL tables.",
            type(exc).__name__,
            exc,
        )
        return False
    for table, id_col, time_col in HYPERTABLES:
        try:
            with engine.begin() as conn:
                already = conn.execute(
                    text("SELECT 1 FROM timescaledb_information.hypertables WHERE hypertable_name = :t"),
                    {"t": table},
                ).first()
                if already:
                    log.info("Hypertable already present: %s", table)
                    continue
                conn.execute(text(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {table}_pkey"))
                conn.execute(text(f"ALTER TABLE {table} ADD PRIMARY KEY ({id_col}, {time_col})"))
                conn.execute(text(f"SELECT create_hypertable('{table}', '{time_col}', migrate_data => true)"))
                log.info("Converted %s to a TimescaleDB hypertable on %s.", table, time_col)
        except Exception as exc:
            log.warning(
                "Could not convert %s to a hypertable (%s: %s). Table remains a regular PostgreSQL table.",
                table,
                type(exc).__name__,
                exc,
            )
            return False
    return True


def hypertable_status(engine: Engine) -> dict:
    """Inspect Timescale metadata. Never claims a plain table is a hypertable."""
    if engine.dialect.name != "postgresql":
        return {"available": False, "reason": f"dialect={engine.dialect.name}", "hypertables": []}
    try:
        with engine.connect() as conn:
            ext = conn.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'")).first()
            if not ext:
                return {"available": False, "reason": "timescaledb extension is not enabled", "hypertables": []}
            rows = conn.execute(
                text(
                    "SELECT hypertable_name, num_dimensions "
                    "FROM timescaledb_information.hypertables "
                    "ORDER BY hypertable_name"
                )
            ).all()
            return {
                "available": True,
                "version": ext[0],
                "hypertables": [{"name": r[0], "num_dimensions": r[1]} for r in rows],
            }
    except Exception as exc:
        return {"available": False, "reason": f"{type(exc).__name__}: {exc}", "hypertables": []}
