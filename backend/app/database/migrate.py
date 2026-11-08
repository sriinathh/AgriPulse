"""Additive schema updates for databases created before new columns/tables existed.

create_all() creates missing tables but does not add columns to existing tables.
This module applies safe ALTER TABLE ... ADD COLUMN statements only. It never
drops columns, tables, or data.
"""
import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

log = logging.getLogger(__name__)

# (table, column, SQL type, optional DEFAULT clause including the DEFAULT keyword)
_COLUMNS = [
    ("farmers", "updated_at", "TIMESTAMP", None),
    ("farmers", "is_demo", "BOOLEAN", "DEFAULT FALSE"),
    ("fields", "field_name", "VARCHAR(120)", None),
    ("fields", "location", "VARCHAR(200)", None),
    ("fields", "updated_at", "TIMESTAMP", None),
    ("fields", "is_demo", "BOOLEAN", "DEFAULT FALSE"),
    ("sensors", "measurement_type", "VARCHAR(40)", "DEFAULT 'soil_moisture'"),
    ("sensors", "connectivity_mode", "VARCHAR(32)", "DEFAULT 'cellular'"),
    ("sensors", "unit", "VARCHAR(32)", None),
    ("sensors", "last_seen_at", "TIMESTAMP", None),
    ("sensors", "is_simulated", "BOOLEAN", "DEFAULT FALSE"),
    ("sensors", "updated_at", "TIMESTAMP", None),
    ("sensors", "is_demo", "BOOLEAN", "DEFAULT FALSE"),
    ("sensor_readings", "measurement_type", "VARCHAR(40)", None),
    ("sensor_readings", "value", "FLOAT", None),
    ("sensor_readings", "unit", "VARCHAR(32)", None),
    ("sensor_readings", "quality_status", "VARCHAR(32)", "DEFAULT 'valid'"),
    ("sensor_readings", "quality_flags", "VARCHAR(500)", None),
    ("sensor_readings", "temperature", "FLOAT", None),
    ("sensor_readings", "humidity", "FLOAT", None),
    ("sensor_readings", "soil_ph", "FLOAT", None),
    ("sensor_readings", "rainfall", "FLOAT", None),
    ("sensor_readings", "water_level", "FLOAT", None),
    ("sensor_readings", "flow_rate", "FLOAT", None),
    ("weather_data", "wind_speed", "FLOAT", None),
    ("weather_data", "condition", "VARCHAR(120)", None),
    ("weather_data", "is_mock", "BOOLEAN", "DEFAULT FALSE"),
    # Milestone 2 — full location metadata on fields
    ("fields", "city", "VARCHAR(100)", None),
    ("fields", "state", "VARCHAR(100)", None),
    ("fields", "country", "VARCHAR(100)", None),
]


def apply_additive_migrations(engine: Engine) -> None:
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    with engine.begin() as conn:
        for table, column, coltype, default in _COLUMNS:
            if table not in tables:
                continue
            existing = {c["name"] for c in inspect(conn).get_columns(table)}
            if column in existing:
                continue
            ddl = f"ALTER TABLE {table} ADD COLUMN {column} {coltype}"
            if default:
                ddl = f"{ddl} {default}"
            conn.execute(text(ddl))
            log.info("Added column %s.%s", table, column)

        # Backfill aliases if columns exist
        if "fields" in tables:
            cols = {c["name"] for c in inspect(conn).get_columns("fields")}
            if "field_name" in cols and "name" in cols:
                conn.execute(text("UPDATE fields SET field_name = name WHERE field_name IS NULL AND name IS NOT NULL"))
            if "location" in cols and "location_name" in cols:
                conn.execute(text("UPDATE fields SET location = location_name WHERE location IS NULL AND location_name IS NOT NULL"))

            # Correct distinct geographic coordinates for verified real locations
            # Prevents incorrectly copying Hyderabad coordinates to other cities
            if "latitude" in cols and "longitude" in cols:
                conn.execute(text("UPDATE fields SET latitude = 18.6725, longitude = 78.0941, city = 'Nizamabad', state = 'Telangana', country = 'IN' WHERE LOWER(location_name) LIKE '%nizamabad%' OR (city IS NOT NULL AND LOWER(city) LIKE '%nizamabad%')"))
                conn.execute(text("UPDATE fields SET latitude = 17.2473, longitude = 80.1514, city = 'Khammam', state = 'Telangana', country = 'IN' WHERE LOWER(location_name) LIKE '%khammam%' OR (city IS NOT NULL AND LOWER(city) LIKE '%khammam%')"))
                conn.execute(text("UPDATE fields SET latitude = 17.6868, longitude = 83.2185, city = 'Visakhapatnam', state = 'Andhra Pradesh', country = 'IN' WHERE LOWER(location_name) LIKE '%vizag%' OR LOWER(location_name) LIKE '%visakhapatnam%' OR (city IS NOT NULL AND LOWER(city) LIKE '%visakhapatnam%')"))
                conn.execute(text("UPDATE fields SET latitude = 17.9689, longitude = 79.5941, city = 'Warangal', state = 'Telangana', country = 'IN' WHERE LOWER(location_name) LIKE '%warangal%' OR (city IS NOT NULL AND LOWER(city) LIKE '%warangal%')"))
                conn.execute(text("UPDATE fields SET latitude = 17.3850, longitude = 78.4867, city = 'Hyderabad', state = 'Telangana', country = 'IN' WHERE (LOWER(location_name) LIKE '%hyderabad%' OR (city IS NOT NULL AND LOWER(city) LIKE '%hyderabad%')) AND latitude IS NOT NULL"))

        if "sensors" in tables:
            cols = {c["name"] for c in inspect(conn).get_columns("sensors")}
            if "measurement_type" in cols and "sensor_type" in cols:
                conn.execute(text("UPDATE sensors SET measurement_type = sensor_type WHERE measurement_type IS NULL AND sensor_type IS NOT NULL"))
            if "connectivity_mode" in cols:
                conn.execute(text("UPDATE sensors SET connectivity_mode = 'cellular' WHERE connectivity_mode IS NULL"))

        # Ensure index presence for historical time-series queries
        indexes = [
            ("sensor_readings", "ix_reading_sensor_id", "CREATE INDEX IF NOT EXISTS ix_reading_sensor_id ON sensor_readings (sensor_id)"),
            ("sensor_readings", "ix_reading_field_id", "CREATE INDEX IF NOT EXISTS ix_reading_field_id ON sensor_readings (field_id)"),
            ("sensor_readings", "ix_reading_timestamp", "CREATE INDEX IF NOT EXISTS ix_reading_timestamp ON sensor_readings (timestamp)"),
            ("weather_data", "ix_weather_field_id", "CREATE INDEX IF NOT EXISTS ix_weather_field_id ON weather_data (field_id)"),
            ("weather_data", "ix_weather_timestamp", "CREATE INDEX IF NOT EXISTS ix_weather_timestamp ON weather_data (timestamp)"),
        ]
        for tbl, idx_name, ddl in indexes:
            if tbl in tables:
                existing_idxs = {i["name"] for i in inspect(conn).get_indexes(tbl)}
                if idx_name not in existing_idxs:
                    try:
                        conn.execute(text(ddl))
                        log.info("Created index %s on %s", idx_name, tbl)
                    except Exception as exc:
                        log.warning("Index creation notice on %s (%s): %s", tbl, idx_name, exc)
