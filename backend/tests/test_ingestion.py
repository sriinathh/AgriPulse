VALID = {"sensor_id": "SM001", "field_id": "F001", "timestamp": "2026-10-07T10:30:00", "soil_moisture": 35.6}


def test_valid_reading_stored(client, seeded):
    r = client.post("/sensor/readings", json=VALID)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "stored"
    assert body["reading"]["soil_moisture"] == 35.6 and body["reading"]["field_id"] == "F001"
    assert body["reading"]["is_simulated"] is False
    assert body["cleaning"]["timestamp_source"] == "client"
    listed = client.get("/sensor/readings", params={"sensor_id": "SM001"}).json()
    assert len(listed) == 1 and listed[0]["timestamp"] == "2026-10-07T10:30:00"


def test_field_id_is_optional_and_inferred_from_sensor(client, seeded):
    r = client.post("/sensor/readings", json={"sensor_id": "SM001", "timestamp": "2026-10-07T10:30:00", "soil_moisture": 30})
    assert r.status_code == 201 and r.json()["reading"]["field_id"] == "F001"


def test_simulated_flag_is_stored(client, seeded):
    client.post("/sensor/readings", json={**VALID, "is_simulated": True})
    assert client.get("/sensor/readings").json()[0]["is_simulated"] is True


def test_missing_soil_moisture_rejected_and_not_stored(client, seeded):
    for payload in ({**VALID, "soil_moisture": None}, {k: v for k, v in VALID.items() if k != "soil_moisture"}):
        r = client.post("/sensor/readings", json=payload)
        assert r.status_code == 422
        err = r.json()["error"]
        assert err["code"] == "validation_failed"
        assert err["details"][0]["field"] == "soil_moisture" and err["details"][0]["code"] == "missing_value"
    assert client.get("/sensor/readings").json() == []


def test_invalid_soil_moisture_rejected(client, seeded):
    for bad in (-5, 101, 250, "wet", True):
        r = client.post("/sensor/readings", json={**VALID, "soil_moisture": bad})
        assert r.status_code == 422, bad
    assert client.get("/sensor/readings").json() == []


def test_out_of_range_error_message_is_meaningful(client, seeded):
    r = client.post("/sensor/readings", json={**VALID, "soil_moisture": 250})
    d = r.json()["error"]["details"][0]
    assert d["code"] == "out_of_range" and "0.0-100.0" in d["message"]


def test_unknown_sensor_rejected(client, seeded):
    r = client.post("/sensor/readings", json={**VALID, "sensor_id": "SM999"})
    assert r.status_code == 404 and r.json()["error"]["code"] == "sensor_not_found"


def test_field_mismatch_rejected(client, seeded):
    client.post("/farmers", json={"farmer_id": "FR002", "name": "Other"})
    client.post("/fields", json={"field_id": "F002", "farmer_id": "FR002", "name": "B", "crop_type": "Maize"})
    r = client.post("/sensor/readings", json={**VALID, "field_id": "F002"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "field_mismatch"


def test_missing_timestamp_uses_server_time(client, seeded):
    r = client.post("/sensor/readings", json={"sensor_id": "SM001", "soil_moisture": 33})
    assert r.status_code == 201
    assert r.json()["cleaning"]["timestamp_source"] == "server"
    assert any("timestamp missing" in n for n in r.json()["cleaning"]["notes"])


def test_bad_and_future_timestamps_rejected(client, seeded):
    assert client.post("/sensor/readings", json={**VALID, "timestamp": "not-a-date"}).status_code == 422
    assert client.post("/sensor/readings", json={**VALID, "timestamp": "2999-01-01T00:00:00"}).status_code == 422


def test_duplicate_reading_conflict(client, seeded):
    assert client.post("/sensor/readings", json=VALID).status_code == 201
    r = client.post("/sensor/readings", json=VALID)
    assert r.status_code == 409 and r.json()["error"]["code"] == "duplicate_reading"
    assert len(client.get("/sensor/readings").json()) == 1


def test_inactive_sensor_rejected(client, seeded):
    client.put("/sensors/SM001/status", json={"status": "inactive"})
    r = client.post("/sensor/readings", json=VALID)
    assert r.status_code == 409 and r.json()["error"]["code"] == "sensor_inactive"


def test_malformed_body_gives_uniform_error(client, seeded):
    r = client.post("/sensor/readings", json={"soil_moisture": 30})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_request"


def test_readings_filter_and_order(client, seeded):
    for t, v in (("2026-10-07T08:00:00", 40), ("2026-10-07T09:00:00", 39), ("2026-10-07T10:00:00", 38)):
        client.post("/sensor/readings", json={**VALID, "timestamp": t, "soil_moisture": v})
    allr = client.get("/sensor/readings", params={"field_id": "F001"}).json()
    assert [r["soil_moisture"] for r in allr] == [38, 39, 40]  # newest first
    window = client.get("/sensor/readings", params={"start": "2026-10-07T08:30:00", "end": "2026-10-07T09:30:00"}).json()
    assert [r["soil_moisture"] for r in window] == [39]
    assert len(client.get("/sensor/readings", params={"limit": 2}).json()) == 2
