"""Full End-to-End Verification of Milestone 1 against running server on port 8010."""
import sys
from datetime import datetime, timezone
from pathlib import Path
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.session import get_engine
from sqlalchemy import text

def run_e2e():
    base_url = "http://127.0.0.1:8010"
    client = httpx.Client(base_url=base_url, timeout=15)
    print("=" * 60)
    print("AGRIPULSE AI — MILESTONE 1 END-TO-END VERIFICATION")
    print("=" * 60)

    # 1. Health & readiness endpoints
    print("\n1. Health Check (GET /health):")
    r = client.get("/health")
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    print(f"   Status: {r.status_code} -> {r.json()}")

    print("\n2. Readiness & DB Connection (GET /health/ready):")
    r = client.get("/health/ready")
    assert r.status_code == 200, f"Readiness check failed: {r.status_code}"
    ready_data = r.json()
    print(f"   Database OK: {ready_data['database']['ok']}, URL: {ready_data['database']['url']}")

    print("\n3. System Status (GET /system/status):")
    r = client.get("/system/status")
    assert r.status_code == 200
    st = r.json()
    print(f"   Backend version: {st['backend']['version']}, env: {st['backend']['environment']}")
    print(f"   TimescaleDB version: {st['timescaledb']['version']}, Hypertables: {st['timescaledb']['hypertables']}")
    print(f"   Weather configured: {st['weather']['configured']}, MQTT enabled: {st['mqtt']['enabled']}")

    # 4. List farmers
    print("\n4. List Farmers (GET /farmers):")
    r = client.get("/farmers")
    assert r.status_code == 200
    farmers = r.json()
    print(f"   Farmers count: {len(farmers)}, First: {farmers[0]['farmer_id']} ({farmers[0]['name']})")

    # 5. List fields
    print("\n5. List Fields (GET /fields):")
    r = client.get("/fields")
    assert r.status_code == 200
    fields = r.json()
    assert len(fields) > 0, "No fields found!"
    target_field = fields[0]["field_id"]
    print(f"   Fields count: {len(fields)}, Using Field ID: '{target_field}'")

    # 6. Register a test sensor against the field
    test_sensor_id = "SM_M1_VERIFY_E2E"
    print(f"\n6. Register Sensor (POST /sensors) with ID='{test_sensor_id}':")
    # Clean up if existing
    client.delete(f"/sensors/{test_sensor_id}")
    r = client.post("/sensors", json={
        "sensor_id": test_sensor_id,
        "field_id": target_field,
        "sensor_type": "soil_moisture",
        "measurement_type": "soil_moisture",
        "unit": "%",
        "status": "active",
        "connectivity_mode": "cellular",
        "is_simulated": True,
    })
    assert r.status_code == 201, f"Sensor creation failed: {r.status_code} {r.text}"
    sensor_res = r.json()
    print(f"   Sensor Registered: {sensor_res['sensor_id']} in Field: {sensor_res['field_id']}")

    # 7. Ingest a sensor reading
    test_ts = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0).isoformat()
    print(f"\n7. Submit Sensor Reading (POST /sensor/readings) at ts={test_ts}:")
    r = client.post("/sensor/readings", json={
        "sensor_id": test_sensor_id,
        "field_id": target_field,
        "timestamp": test_ts,
        "soil_moisture": 36.8,
        "measurement_type": "soil_moisture",
        "value": 36.8,
        "unit": "%",
        "is_simulated": True,
    })
    assert r.status_code == 201, f"Ingestion failed: {r.status_code} {r.text}"
    ingest_res = r.json()
    reading_id = ingest_res["reading"]["reading_id"]
    print(f"   Ingested: reading_id={reading_id}, status={ingest_res['status']}")

    # 8. Direct PostgreSQL verification
    print("\n8. Direct PostgreSQL Verification for reading_id:")
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT reading_id, sensor_id, field_id, timestamp, soil_moisture, quality_status, is_simulated "
            "FROM sensor_readings WHERE reading_id = :rid"
        ), {"rid": reading_id}).first()
        assert row is not None, "Reading not found in PostgreSQL!"
        print(f"   PostgreSQL Row: reading_id={row[0]}, sensor={row[1]}, field={row[2]}, moisture={row[4]}%, quality={row[5]}")

    # 9. Historical readings API retrieval
    print("\n9. Historical Readings API Query (GET /sensor/readings):")
    r = client.get("/sensor/readings", params={"sensor_id": test_sensor_id, "order": "desc"})
    assert r.status_code == 200
    readings = r.json()
    assert len(readings) >= 1
    print(f"   Retrieved {len(readings)} reading(s). First reading: id={readings[0]['reading_id']}, moisture={readings[0]['soil_moisture']}%")

    # 10. Weather retrieval
    print("\n10. Weather API Check (GET /weather/{field_id}):")
    r = client.get(f"/weather/{target_field}")
    assert r.status_code in (200, 422), f"Unexpected weather response: {r.status_code}"
    print(f"   Weather status: {r.status_code} -> {r.json().get('status', r.json().get('error', {}).get('code'))}")

    # 11. Data Quality stats
    print("\n11. Data Quality Stats (GET /data-quality/stats):")
    r = client.get("/data-quality/stats")
    assert r.status_code == 200
    dq = r.json()
    print(f"   Readings stored: {dq['readings_stored']}, Valid: {dq['valid_readings']}, Failures caught: {dq['ingestion_failures']}")

    # Clean up test sensor
    client.delete(f"/sensors/{test_sensor_id}")
    print(f"\nCleaned up verification sensor '{test_sensor_id}'.")
    print("\n" + "=" * 60)
    print("ALL END-TO-END VERIFICATION CHECKS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    run_e2e()
