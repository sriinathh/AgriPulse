"""Week 1 end-to-end flow (Step 10), entirely through the HTTP API. Weather HTTP is mocked (tests only)."""
from .test_weather import KEY, OWM_OK, ok, use_provider


def test_full_week1_flow(client):
    # 1-4. register farmer -> field (+crop) -> sensor
    assert client.post("/farmers", json={"farmer_id": "FR001", "name": "Harini"}).status_code == 201
    assert client.post("/fields", json={"field_id": "F001", "farmer_id": "FR001", "name": "North Paddy",
                                        "latitude": 17.385, "longitude": 78.4867, "crop_type": "Rice"}).status_code == 201
    assert client.post("/sensors", json={"sensor_id": "SM001", "field_id": "F001"}).status_code == 201

    # 5-7. simulated readings: good ones stored, bad ones rejected before reaching the DB
    good = [("2026-10-07T09:30:00", 36.4), ("2026-10-07T10:30:00", 35.6), ("2026-10-07T11:30:00", 34.9)]
    for ts, v in good:
        r = client.post("/sensor/readings", json={"sensor_id": "SM001", "field_id": "F001", "timestamp": ts,
                                                  "soil_moisture": v, "is_simulated": True})
        assert r.status_code == 201
    assert client.post("/sensor/readings", json={"sensor_id": "SM001", "soil_moisture": None}).status_code == 422
    assert client.post("/sensor/readings", json={"sensor_id": "SM001", "soil_moisture": 250}).status_code == 422
    assert len(client.get("/sensor/readings", params={"field_id": "F001"}).json()) == 3

    # 8-10. weather for the field (observation time 10:30 UTC) -> normalised -> stored
    use_provider(ok(OWM_OK))
    w = client.get("/weather/F001").json()
    assert w["status"] == "stored"
    assert set(w["weather"]) >= {"field_id", "timestamp", "temperature", "humidity", "rainfall"}

    # 11. combined view
    data = client.get("/fields/F001/combined").json()
    assert data["field"]["crop_type"] == "Rice" and data["sensors"][0]["sensor_id"] == "SM001"
    assert data["latest_weather"]["temperature"] == 29.0
    by_ts = {r["timestamp"]: r for r in data["records"]}
    assert by_ts["2026-10-07T09:30:00"]["weather"] is None  # no weather known yet at that time: not invented
    assert by_ts["2026-10-07T10:30:00"]["weather"]["humidity"] == 68.0
    assert by_ts["2026-10-07T11:30:00"]["weather_age_minutes"] == 60.0
    assert all(r["is_simulated"] for r in data["records"])
    assert KEY not in str(data)


def test_combined_unknown_field(client):
    assert client.get("/fields/NOPE/combined").status_code == 404


def test_combined_empty_field(client, seeded):
    d = client.get("/fields/F001/combined").json()
    assert d["records"] == [] and d["latest_weather"] is None
