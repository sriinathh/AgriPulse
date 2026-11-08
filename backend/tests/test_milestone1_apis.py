import json
from datetime import datetime, timezone
import pytest
from app.schemas.crop import CropCreate, CropPatch
from app.schemas.farmer import FarmerUpdate
from app.schemas.field import FieldUpdate
from app.schemas.sensor import SensorUpdate
from app.services import mqtt_service


def test_crop_crud(client, seeded):
    # 1. List crops (Field F001 auto-creates an initial crop on field creation)
    crops = client.get("/crops", params={"field_id": "F001"}).json()
    assert len(crops) >= 1
    init_crop_id = crops[0]["crop_id"]

    # 2. Get crop by ID
    c = client.get(f"/crops/{init_crop_id}").json()
    assert c["field_id"] == "F001"
    assert c["crop_type"] == "Rice"

    # 3. Create another crop record
    res = client.post("/crops", json={
        "field_id": "F001",
        "crop_type": "Wheat",
        "variety": "Sharbati",
        "growth_stage": "vegetative",
        "notes": "Second cycle"
    })
    assert res.status_code == 201
    new_crop = res.json()
    assert new_crop["crop_type"] == "Wheat"
    assert new_crop["variety"] == "Sharbati"

    # 4. Update (Patch) crop record
    patch_res = client.put(f"/crops/{new_crop['crop_id']}", json={
        "growth_stage": "flowering",
        "notes": "Updated note"
    })
    assert patch_res.status_code == 200
    assert patch_res.json()["growth_stage"] == "flowering"
    assert patch_res.json()["notes"] == "Updated note"

    # 5. Delete crop
    del_res = client.delete(f"/crops/{new_crop['crop_id']}")
    assert del_res.status_code == 204
    assert client.get(f"/crops/{new_crop['crop_id']}").status_code == 404


def test_farmer_update_and_delete(client):
    # Create farmer
    res = client.post("/farmers", json={"name": "Kiran", "phone": "9876543210", "email": "kiran@example.com"})
    assert res.status_code == 201
    farmer_id = res.json()["farmer_id"]

    # Update farmer
    up_res = client.put(f"/farmers/{farmer_id}", json={"name": "Kiran Kumar", "phone": "9876543211"})
    assert up_res.status_code == 200
    assert up_res.json()["name"] == "Kiran Kumar"
    assert up_res.json()["phone"] == "9876543211"

    # Delete farmer
    del_res = client.delete(f"/farmers/{farmer_id}")
    assert del_res.status_code == 204
    assert client.get(f"/farmers/{farmer_id}").status_code == 404


def test_field_update_and_delete(client, seeded):
    # Update field
    up_res = client.put("/fields/F001", json={"name": "Updated North Paddy", "area_hectares": 2.5})
    assert up_res.status_code == 200
    assert up_res.json()["name"] == "Updated North Paddy"
    assert up_res.json()["area_hectares"] == 2.5

    # Delete field
    del_res = client.delete("/fields/F001")
    assert del_res.status_code == 204
    assert client.get("/fields/F001").status_code == 404


def test_sensor_update_and_delete(client, seeded):
    # Update sensor
    up_res = client.put("/sensors/SM001", json={"sensor_type": "soil_moisture", "unit": "%"})
    assert up_res.status_code == 200
    assert up_res.json()["unit"] == "%"

    # Delete sensor
    del_res = client.delete("/sensors/SM001")
    assert del_res.status_code == 204
    assert client.get("/sensors/SM001").status_code == 404


def test_system_status_and_health(client):
    h = client.get("/health").json()
    assert h["status"] == "ok"

    ready = client.get("/health/ready").json()
    assert ready["status"] == "ok"
    assert ready["database"]["ok"] is True

    sys_status = client.get("/system/status").json()
    assert sys_status["backend"]["ok"] is True
    assert "timescaledb" in sys_status
    assert "weather" in sys_status
    assert "mqtt" in sys_status


def test_data_quality_stats_and_events(client, seeded):
    # Trigger a data quality event by sending out-of-range reading
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    client.post("/sensor/readings", json={
        "sensor_id": "SM001",
        "timestamp": now,
        "soil_moisture": 150.0  # Invalid > 100
    })

    # Query stats
    stats = client.get("/data-quality/stats").json()
    assert "readings_stored" in stats
    assert "invalid_readings" in stats
    assert "out_of_range_count" in stats

    # Query events
    events = client.get("/data-quality/events").json()
    assert isinstance(events, list)


def test_demo_seed_endpoint(client):
    # Call demo seed
    res = client.post("/demo/seed")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("seeded", "already_seeded")

    # Calling it a second time should return already_seeded and not duplicate
    res2 = client.post("/demo/seed")
    assert res2.status_code == 200
    assert res2.json()["status"] == "already_seeded"


def test_sensor_readings_csv_export(client, seeded):
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    client.post("/sensor/readings", json={
        "sensor_id": "SM001",
        "timestamp": now,
        "soil_moisture": 35.5
    })
    res = client.get("/sensor/readings/export.csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "reading_id,sensor_id,field_id" in res.text
    assert "SM001" in res.text


def test_mqtt_payload_parser():
    # Valid payload
    payload = json.dumps({
        "sensor_id": "SM001",
        "soil_moisture": 42.0,
        "timestamp": "2026-10-14T10:00:00"
    }).encode("utf-8")
    parsed = mqtt_service.parse_mqtt_payload(payload)
    assert parsed.sensor_id == "SM001"
    assert parsed.soil_moisture == 42.0

    # Non utf-8
    with pytest.raises(ValueError, match="UTF-8"):
        mqtt_service.parse_mqtt_payload(b"\xff\xfe\x00")

    # Non json
    with pytest.raises(ValueError, match="JSON"):
        mqtt_service.parse_mqtt_payload(b"not json")

    # Non object json
    with pytest.raises(ValueError, match="JSON object"):
        mqtt_service.parse_mqtt_payload(b"[1, 2, 3]")


def test_crop_recommendation_model_and_api(client):
    # Test with standard Rice soil/weather conditions from dataset
    res = client.post("/recommendations/crop", json={
        "N": 90,
        "P": 42,
        "K": 43,
        "temperature": 20.87,
        "humidity": 82.0,
        "ph": 6.5,
        "rainfall": 202.9,
    })
    assert res.status_code == 200
    data = res.json()
    assert data["recommended_crop"] == "rice"
    assert data["confidence"] > 0.5
    assert len(data["top_candidates"]) == 3
    assert "agronomic_explanation" in data
    assert "limitations" in data


def test_crop_recommendation_metrics_api(client):
    res = client.get("/recommendations/crop/metrics")
    assert res.status_code == 200
    metrics = res.json()
    assert metrics["train_samples"] == 1760
    assert metrics["test_samples"] == 440
    assert metrics["test_accuracy"] > 0.95
    assert metrics["macro_f1"] > 0.95
    assert "feature_importances" in metrics


def test_irrigation_recommendation_service(client, seeded):
    # 1. Deficit condition -> IRRIGATE_IMMEDIATELY
    res = client.post("/recommendations/irrigation", json={
        "crop_type": "Rice",
        "growth_stage": "flowering",
        "soil_moisture": 15.0,
        "temperature": 32.0,
        "recent_rainfall_mm": 0.0,
        "forecast_rainfall_mm": 0.0,
    })
    assert res.status_code == 200
    data = res.json()
    assert data["action"] == "IRRIGATE_IMMEDIATELY"
    assert data["urgency"] == "HIGH"
    assert data["recommended_water_mm"] > 0.0
    assert "flowering" in data["reason"].lower()

    # 2. Rainfall condition -> DEFER_DUE_TO_RAIN
    res_rain = client.post("/recommendations/irrigation", json={
        "crop_type": "Rice",
        "growth_stage": "flowering",
        "soil_moisture": 15.0,
        "temperature": 32.0,
        "recent_rainfall_mm": 25.0,
        "forecast_rainfall_mm": 0.0,
    })
    assert res_rain.status_code == 200
    assert res_rain.json()["action"] == "DEFER_DUE_TO_RAIN"

    # 3. Via field_id
    field_res = client.get("/recommendations/irrigation/F001")
    assert field_res.status_code == 200
    assert "action" in field_res.json()
    assert "factors_evaluated" in field_res.json()


def test_dashboard_summary_top_level_metrics(client, seeded):
    res = client.get("/dashboard/summary")
    assert res.status_code == 200
    summary = res.json()
    assert "readings_stored" in summary
    assert "valid_readings" in summary
    assert "simulated_readings" in summary
    assert "ingestion_failures" in summary
    assert "timescale_active" in summary
    assert isinstance(summary["readings_stored"], int)
    assert isinstance(summary["timescale_active"], bool)
