import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.session import get_engine
from app.database.timescale import hypertable_status
from sqlalchemy import inspect, text

def main():
    engine = get_engine()
    print("=== 1. PostgreSQL Connection ===")
    with engine.connect() as conn:
        res = conn.execute(text("SELECT current_database(), inet_server_port(), current_user, version()")).first()
        print(f"Connected to DB='{res[0]}' on port={res[1]} as user='{res[2]}'")
        print(f"PostgreSQL version: {res[3]}\n")

    print("=== 2. Relational Schema & 3. Foreign Keys ===")
    insp = inspect(engine)
    tables = ["farmers", "fields", "crops", "sensors", "sensor_readings", "weather_data"]
    for t in tables:
        pk = insp.get_pk_constraint(t)["constrained_columns"]
        fks = [(fk["constrained_columns"], fk["referred_table"], fk["referred_columns"]) for fk in insp.get_foreign_keys(t)]
        cols = [c["name"] for c in insp.get_columns(t)]
        idxs = [(ix["name"], ix["column_names"]) for ix in insp.get_indexes(t)]
        print(f"Table: {t}")
        print(f"  Primary Key: {pk}")
        print(f"  Foreign Keys: {fks}")
        print(f"  Indexes: {idxs}")
        print(f"  Columns ({len(cols)}): {cols}\n")

    print("=== 4. TimescaleDB Extension & 5, 6. Hypertables ===")
    with engine.connect() as conn:
        ext = conn.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb'")).first()
        print(f"TimescaleDB extension: {ext[0]} (version {ext[1]})" if ext else "Not found")

        hyps = conn.execute(text(
            "SELECT hypertable_schema, hypertable_name, num_dimensions FROM timescaledb_information.hypertables ORDER BY hypertable_name"
        )).all()
        print("Hypertables registered in TimescaleDB catalog:")
        for h in hyps:
            print(f"  - {h[0]}.{h[1]} (dimensions: {h[2]})")

    status = hypertable_status(engine)
    print(f"\nHypertable helper status: {status}\n")

if __name__ == "__main__":
    main()
