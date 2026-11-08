"""AgriPulse AI - Full System Integration & Verification Script.

Executes a complete 12-step end-to-end verification against the live system:
- Database connectivity & TimescaleDB hypertables
- Relational entities (Farmer -> Field -> Crop -> Sensor)
- Sensor reading ingestion & Data Quality boundary validation
- Historical queries (ASC / DESC) & CSV export
- OpenWeatherMap integration & persistence
- Agricultural Intelligence ML Crop Recommendation (Dataset validation, inference)
- Explainable Irrigation Water Deficit Advisory (FAO-56)
- Dashboard top-level KPI metrics verification
"""
import sys
from datetime import datetime, timezone

import httpx

BASE_URL = "http://127.0.0.1:8010"


def run_checks():
    print("=" * 65)
    print("AGRIPULSE AI - FULL SYSTEM VERIFICATION & INTEGRATION SUITE")
    print("=" * 65)

    with httpx.Client(base_url=BASE_URL, timeout=15) as client:
        # 1. Health
        print("\n1. Health Check (GET /health):")
        r = client.get("/health")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        print(f"   Status: {r.status_code} -> {r.json()}")

        # 2. Database readiness
        print("\n2. Database Readiness Check (GET /health/ready):")
        r = client.get("/health/ready")
        assert r.status_code == 200
        data = r.json()
        print(f"   Database OK: {data['database']['ok']}, URL: {data['database']['url']}")

        # 3. System status & TimescaleDB
        print("\n3. System Status (GET /system/status):")
        r = client.get("/system/status")
        assert r.status_code == 200
        status_data = r.json()
        ts = status_data["timescaledb"]
        print(f"   TimescaleDB Available: {ts['available']}, Version: {ts.get('version')}")
        print(f"   Registered Hypertables: {ts.get('hypertables')}")
        assert "sensor_readings" in ts.get("hypertables", [])
        assert "weather_data" in ts.get("hypertables", [])

        # 4. Farmers & Fields
        print("\n4. Relational Entity Verification (GET /farmers, GET /fields):")
        rf = client.get("/farmers")
        rfields = client.get("/fields")
        assert rf.status_code == 200 and rfields.status_code == 200
        farmers = rf.json()
        fields = rfields.json()
        print(f"   Farmers count: {len(farmers)}, Fields count: {len(fields)}")
        field_id = fields[0]["field_id"] if fields else "F001"

        # 5. Sensor registration
        test_sensor = "SM_SYS_VERIFY_99"
        print(f"\n5. Sensor Registration (POST /sensors, ID='{test_sensor}'):")
        reg_res = client.post("/sensors", json={
            "sensor_id": test_sensor,
            "field_id": field_id,
            "sensor_type": "soil_moisture",
            "unit": "%",
            "status": "active",
            "is_simulated": True,
        })
        assert reg_res.status_code in (201, 409)
        print(f"   Sensor status: {reg_res.status_code}")

        # 6. Sensor reading ingestion
        now_iso = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None).isoformat()
        print(f"\n6. Sensor Reading Ingestion (POST /sensor/readings at {now_iso}):")
        ingest_res = client.post("/sensor/readings", json={
            "sensor_id": test_sensor,
            "field_id": field_id,
            "timestamp": now_iso,
            "soil_moisture": 32.5,
            "temperature": 27.8,
            "is_simulated": True,
        })
        assert ingest_res.status_code in (201, 409)
        print(f"   Ingestion response: {ingest_res.status_code}")

        # 7. Data Quality Boundary Rejection (Out-of-range value)
        print("\n7. Data Quality Boundary Enforcement (Invalid moisture = 250%):")
        dq_res = client.post("/sensor/readings", json={
            "sensor_id": test_sensor,
            "field_id": field_id,
            "timestamp": now_iso,
            "soil_moisture": 250.0,
            "is_simulated": True,
        })
        assert dq_res.status_code == 422
        print(f"   Rejected correctly with HTTP 422: {dq_res.json()['error']['code']}")

        # 8. Historical readings & CSV export
        print("\n8. Historical Query & CSV Export (GET /sensor/readings, GET /sensor/readings/export.csv):")
        hist_res = client.get("/sensor/readings", params={"sensor_id": test_sensor, "order": "desc"})
        assert hist_res.status_code == 200
        readings = hist_res.json()
        print(f"   Retrieved {len(readings)} reading(s). Latest moisture: {readings[0].get('soil_moisture')}%")
        csv_res = client.get("/sensor/readings/export.csv", params={"sensor_id": test_sensor})
        assert csv_res.status_code == 200
        assert "text/csv" in csv_res.headers["content-type"]
        print("   CSV Export verified successfully.")

        # 9. OpenWeatherMap integration
        print(f"\n9. Weather Service Observation (GET /weather/{field_id}):")
        w_res = client.get(f"/weather/{field_id}")
        assert w_res.status_code == 200
        w_data = w_res.json()
        print(f"   Weather status: {w_data.get('status')}, Temp: {w_data.get('weather', {}).get('temperature')}°C")

        # 10. Agricultural Intelligence - Crop Recommendation Model
        print("\n10. ML Crop Recommendation (POST /recommendations/crop):")
        crop_res = client.post("/recommendations/crop", json={
            "N": 90,
            "P": 42,
            "K": 43,
            "temperature": 23.5,
            "humidity": 80.0,
            "ph": 6.5,
            "rainfall": 205.0,
        })
        assert crop_res.status_code == 200
        crop_data = crop_res.json()
        print(f"    Recommended Crop: {crop_data['recommended_crop'].upper()} (Confidence: {crop_data['confidence']*100:.1f}%)")
        print(f"    Top Candidates: {[c['crop'] for c in crop_data['top_candidates']]}")
        print(f"    Agronomic Rationale: {crop_data['agronomic_explanation']}")

        # Model metrics
        metric_res = client.get("/recommendations/crop/metrics")
        assert metric_res.status_code == 200
        m = metric_res.json()
        print(f"    Model Accuracy: {m['test_accuracy']*100:.2f}%, Macro F1: {m['macro_f1']*100:.2f}% (Trained on {m['train_samples']} rows)")

        # 11. Explainable Irrigation Advisory
        print(f"\n11. Irrigation Water Deficit Advisory (GET /recommendations/irrigation/{field_id}):")
        irrig_res = client.get(f"/recommendations/irrigation/{field_id}")
        assert irrig_res.status_code == 200
        irrig_data = irrig_res.json()
        print(f"    Action: {irrig_data['action']} ({irrig_data['urgency']} Urgency)")
        print(f"    Recommended Water: {irrig_data['recommended_water_mm']} mm")
        print(f"    Reasoning: {irrig_data['reason']}")
        print(f"    Engine: {irrig_data['recommendation_engine']}")

        # 12. Dashboard summary metrics
        print("\n12. Dashboard Top-Level Metrics (GET /dashboard/summary):")
        dash_res = client.get("/dashboard/summary")
        assert dash_res.status_code == 200
        summary = dash_res.json()
        print(f"    Readings Ingested: {summary.get('readings_stored')}")
        print(f"    Valid Readings: {summary.get('valid_readings')}")
        print(f"    Simulated Readings: {summary.get('simulated_readings')}")
        print(f"    Anomalies Caught: {summary.get('ingestion_failures')}")
        print(f"    TimescaleDB Active: {summary.get('timescale_active')}")

        # Cleanup test sensor
        client.delete(f"/sensors/{test_sensor}")

    print("\n" + "=" * 65)
    print("ALL 12 END-TO-END SYSTEM VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    try:
        run_checks()
    except Exception as e:
        print(f"\nVerification failed with error: {e}", file=sys.stderr)
        sys.exit(1)
