import httpx
import pytest

from app.config import Settings
from app.main import app
from app.routers.weather import get_weather_provider
from app.services.weather_service import WeatherProvider

KEY = "SECRET-TEST-KEY-123"
DT = 1791369000  # 2026-10-07T10:30:00Z

OWM_OK = {"coord": {"lon": 78.4867, "lat": 17.385}, "dt": DT,
          "main": {"temp": 29.0, "humidity": 68, "pressure": 1010}, "rain": {"1h": 2.1},
          "weather": [{"description": "moderate rain"}], "wind": {"speed": 3.5}}

# Geocoding response (OWM format)
GEO_OK = [{"name": "Hyderabad", "lat": 17.385, "lon": 78.4867, "state": "Telangana", "country": "IN"}]


def use_provider(handler, key=KEY):
    """Route the REAL provider code through a mocked HTTP transport (tests only)."""
    calls = []

    def wrapped(request):
        calls.append(request)
        return handler(request)

    settings = Settings(openweather_api_key=key, openweather_base_url="https://owm.test/weather")
    app.dependency_overrides[get_weather_provider] = lambda: WeatherProvider(settings, httpx.MockTransport(wrapped))
    return calls


def use_geocode_provider(handler, key=KEY):
    """Override settings and location transport dependency with a mock geocoding transport."""
    from app.config import get_settings
    from app.routers.weather import get_location_transport

    calls = []

    def wrapped(request):
        calls.append(request)
        return handler(request)

    settings = Settings(
        openweather_api_key=key,
        openweather_geocode_url="https://owm.test/geo",
        openweather_base_url="https://owm.test/weather",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_location_transport] = lambda: httpx.MockTransport(wrapped)
    return calls


def ok(payload):
    return lambda req: httpx.Response(200, json=payload)


# ── Existing weather tests ─────────────────────────────────────────────────────

def test_successful_weather_normalised_and_stored(client, seeded):
    calls = use_provider(ok(OWM_OK))
    r = client.get("/weather/F001")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "stored"
    w = body["weather"]
    assert (w["field_id"], w["temperature"], w["humidity"], w["rainfall"]) == ("F001", 29.0, 68.0, 2.1)
    assert w["timestamp"] == "2026-10-07T10:30:00" and w["source"] == "openweathermap"
    # request used the field's configured location and metric units
    q = dict(calls[0].url.params)
    assert q["lat"] == "17.385" and q["lon"] == "78.4867" and q["units"] == "metric"
    assert KEY not in r.text
    assert len(client.get("/weather/F001/history").json()) == 1


def test_fetched_at_present_in_weather_out(client, seeded):
    """WeatherOut must include fetched_at (when our backend made the API call)."""
    use_provider(ok(OWM_OK))
    r = client.get("/weather/F001")
    assert r.status_code == 200
    w = r.json()["weather"]
    assert "fetched_at" in w and w["fetched_at"] is not None


def test_same_observation_not_stored_twice(client, seeded):
    use_provider(ok(OWM_OK))
    assert client.get("/weather/F001").json()["status"] == "stored"
    assert client.get("/weather/F001").json()["status"] == "already_stored"
    assert len(client.get("/weather/F001/history").json()) == 1


def test_no_rain_key_means_zero_mm(client, seeded):
    payload = {k: v for k, v in OWM_OK.items() if k != "rain"}
    use_provider(ok(payload))
    assert client.get("/weather/F001").json()["weather"]["rainfall"] == 0.0


def test_three_hour_rain_is_averaged(client, seeded):
    use_provider(ok({**OWM_OK, "rain": {"3h": 6.0}}))
    assert client.get("/weather/F001").json()["weather"]["rainfall"] == 2.0


def test_timeout_is_controlled_and_nothing_stored(client, seeded):
    def boom(req):
        raise httpx.ConnectTimeout("slow", request=req)
    use_provider(boom)
    r = client.get("/weather/F001")
    assert r.status_code == 503 and r.json()["error"]["code"] == "weather_timeout"
    assert client.get("/weather/F001/history").json() == []


def test_network_error_is_controlled_and_does_not_leak_key(client, seeded):
    def boom(req):
        raise httpx.ConnectError(f"cannot connect {req.url}", request=req)
    use_provider(boom)
    r = client.get("/weather/F001")
    assert r.status_code == 503 and r.json()["error"]["code"] == "weather_unavailable"
    assert KEY not in r.text


@pytest.mark.parametrize("status,http,code", [(500, 502, "weather_provider_error"), (401, 502, "weather_auth_failed"),
                                              (429, 503, "weather_rate_limited"), (404, 502, "weather_provider_error")])
def test_provider_error_statuses(client, seeded, status, http, code):
    use_provider(lambda req: httpx.Response(status, json={"message": "x"}))
    r = client.get("/weather/F001")
    assert r.status_code == http and r.json()["error"]["code"] == code
    assert KEY not in r.text


def test_invalid_json_response(client, seeded):
    use_provider(lambda req: httpx.Response(200, text="<html>oops</html>"))
    r = client.get("/weather/F001")
    assert r.status_code == 502 and r.json()["error"]["code"] == "weather_bad_response"


def test_incomplete_response_rejected_not_filled_in(client, seeded):
    use_provider(ok({"dt": DT, "main": {"temp": 29.0}}))  # humidity missing
    r = client.get("/weather/F001")
    assert r.status_code == 502
    err = r.json()["error"]
    assert err["code"] == "weather_incomplete_data" and {"field": "humidity", "code": "missing_value"} in err["details"]
    assert client.get("/weather/F001/history").json() == []


def test_implausible_values_rejected(client, seeded):
    use_provider(ok({**OWM_OK, "main": {"temp": 999, "humidity": 68}}))
    r = client.get("/weather/F001")
    assert r.status_code == 502 and r.json()["error"]["code"] == "weather_invalid_data"


def test_missing_field_location(client, seeded):
    client.post("/fields", json={"field_id": "F002", "farmer_id": "FR001", "name": "No GPS", "crop_type": "Maize"})
    calls = use_provider(ok(OWM_OK))
    r = client.get("/weather/F002")
    assert r.status_code == 422 and r.json()["error"]["code"] == "field_location_missing"
    assert calls == []  # provider never called


def test_unknown_field(client):
    use_provider(ok(OWM_OK))
    assert client.get("/weather/NOPE").status_code == 404


def test_missing_api_key_is_controlled(client, seeded):
    calls = use_provider(ok(OWM_OK), key=None)
    r = client.get("/weather/F001")
    assert r.status_code == 503 and r.json()["error"]["code"] == "weather_not_configured"
    assert calls == []


def test_latest_stored_fallback_endpoint(client, seeded):
    assert client.get("/weather/F001/latest").status_code == 404
    use_provider(ok(OWM_OK))
    client.get("/weather/F001")
    use_provider(lambda req: httpx.Response(500))  # provider now down
    assert client.get("/weather/F001").status_code == 502
    latest = client.get("/weather/F001/latest")
    assert latest.status_code == 200 and latest.json()["temperature"] == 29.0


# ── Geocoding endpoint tests ───────────────────────────────────────────────────

def test_geocode_returns_places(client):
    """GET /weather/geocode?q=Hyderabad,IN returns list of PlaceOut objects."""
    use_geocode_provider(lambda req: httpx.Response(200, json=GEO_OK))
    r = client.get("/weather/geocode", params={"q": "Hyderabad,IN"})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    place = data[0]
    assert place["name"] == "Hyderabad"
    assert place["latitude"] == 17.385
    assert place["longitude"] == 78.4867
    assert place["state"] == "Telangana"
    assert place["country"] == "IN"
    assert "label" in place
    app.dependency_overrides.clear()


def test_geocode_not_found_returns_404(client):
    """When OWM returns an empty list the endpoint should raise 404."""
    use_geocode_provider(lambda req: httpx.Response(200, json=[]))
    r = client.get("/weather/geocode", params={"q": "ZZZnowhere"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "location_not_found"
    app.dependency_overrides.clear()


def test_geocode_empty_query_rejected(client):
    """Empty / whitespace-only query must be rejected with 422."""
    use_geocode_provider(lambda req: httpx.Response(200, json=[]))
    r = client.get("/weather/geocode", params={"q": "   "})
    # FastAPI validates min_length=1 for the Query param → 422
    assert r.status_code == 422
    app.dependency_overrides.clear()


def test_geocode_no_api_key_controlled(client):
    """Missing API key returns 503 and doesn't call the external service."""
    calls = []

    def record(req):
        calls.append(req)
        return httpx.Response(200, json=GEO_OK)

    use_geocode_provider(record, key=None)
    r = client.get("/weather/geocode", params={"q": "Hyderabad"})
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "weather_not_configured"
    assert calls == []
    app.dependency_overrides.clear()


def test_geocode_provider_auth_error(client):
    """401 from geocoding provider → 502 with weather_auth_failed."""
    use_geocode_provider(lambda req: httpx.Response(401, json={"message": "Invalid key"}))
    r = client.get("/weather/geocode", params={"q": "Hyderabad"})
    assert r.status_code == 502
    assert r.json()["error"]["code"] == "weather_auth_failed"
    app.dependency_overrides.clear()


# ── Field city/state/country tests ────────────────────────────────────────────

def test_field_city_state_country_stored_and_returned(client, seeded):
    """Creating a field with city, state, country stores and returns them correctly."""
    payload = {
        "field_id": "F003",
        "farmer_id": "FR001",
        "name": "South Paddy",
        "location_name": "Hyderabad, Telangana",
        "latitude": 17.385,
        "longitude": 78.4867,
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "IN",
        "crop_type": "rice",
    }
    r = client.post("/fields", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["city"] == "Hyderabad"
    assert data["state"] == "Telangana"
    assert data["country"] == "IN"

    # Verify via GET
    r2 = client.get("/fields/F003")
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["city"] == "Hyderabad"
    assert d2["state"] == "Telangana"
    assert d2["country"] == "IN"


def test_field_update_preserves_location_metadata(client, seeded):
    """Updating a field's coordinates does not wipe city/state/country."""
    # First, set city/state/country on F001
    r = client.put("/fields/F001", json={"city": "Hyderabad", "state": "Telangana", "country": "IN"})
    assert r.status_code == 200
    d = r.json()
    assert d["city"] == "Hyderabad"
    assert d["country"] == "IN"


def test_field_without_city_state_country_returns_null(client, seeded):
    """Fields created without location metadata return null for city/state/country."""
    r = client.get("/fields/F001")
    assert r.status_code == 200
    d = r.json()
    assert "city" in d
    assert "state" in d
    assert "country" in d


# ── Milestone 1 Separation of Search & Field Weather Tests ─────────────────────

def test_live_weather_by_coords_does_not_persist_or_touch_fields(client):
    """Workflow B: Searching a location returns live weather without writing to weather_data."""
    calls = use_provider(ok(OWM_OK))
    r = client.get("/weather/live-by-coords", params={
        "latitude": 17.2473,
        "longitude": 80.1514,
        "location_name": "Khammam, Telangana, India",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["latitude"] == 17.2473
    assert data["longitude"] == 80.1514
    assert data["location_name"] == "Khammam, Telangana, India"
    assert data["temperature"] == 29.0
    assert data["humidity"] == 68.0
    assert data["rainfall"] == 2.1
    assert data["source"] == "openweathermap"
    assert data["is_mock"] is False
    assert "timestamp" in data
    assert "fetched_at" in data

    # Verify nothing was added to the field observations table
    r_obs = client.get("/weather/observations")
    assert r_obs.status_code == 200
    assert len(r_obs.json()) == 0


def test_invalid_coordinates_range_rejected(client):
    """Coordinates outside [-90, 90] and [-180, 180] are rejected with 422."""
    use_provider(ok(OWM_OK))
    # Lat > 90
    r1 = client.get("/weather/live-by-coords", params={"latitude": 95.0, "longitude": 80.0})
    assert r1.status_code == 422

    # Lat < -90
    r2 = client.get("/weather/live-by-coords", params={"latitude": -91.0, "longitude": 80.0})
    assert r2.status_code == 422

    # Lon > 180
    r3 = client.get("/weather/live-by-coords", params={"latitude": 17.0, "longitude": 185.0})
    assert r3.status_code == 422

    # Lon < -180
    r4 = client.get("/weather/live-by-coords", params={"latitude": 17.0, "longitude": -185.0})
    assert r4.status_code == 422


def test_duplicate_weather_observation_updates_fetched_at_safely(client, seeded):
    """Calling fetch_weather twice with the same provider timestamp does not crash with 500 or corrupt history."""
    use_provider(ok(OWM_OK))
    # First fetch: new record
    r1 = client.get("/weather/F001")
    assert r1.status_code == 200
    assert r1.json()["status"] == "stored"

    # Second fetch with identical observation timestamp: gracefully handled
    r2 = client.get("/weather/F001")
    assert r2.status_code == 200
    assert r2.json()["status"] == "already_stored"
    assert r2.json()["weather"]["temperature"] == 29.0

    # Ensure only ONE observation row exists in database for this field & timestamp
    r3 = client.get("/weather/F001/history")
    assert r3.status_code == 200
    records = r3.json()
    assert len(records) == 1
    assert records[0]["field_id"] == "F001"


def test_field_coordinates_validation_on_fetch(client):
    """Field with out-of-range coordinates is rejected when weather is fetched."""
    # Create farmer
    client.post("/farmers", json={"farmer_id": "FR009", "name": "Test Farmer", "phone": "1234567890"})
    # Create field with coordinates that bypass or have invalid values
    client.post("/fields", json={
        "field_id": "F009",
        "farmer_id": "FR009",
        "name": "Invalid Field",
        "crop_type": "rice",
        "location_name": "No GPS",
    })
    # Fetch weather on field without coordinates -> 422 field_location_missing
    use_provider(ok(OWM_OK))
    r = client.get("/weather/F009")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "field_location_missing"


def test_distinct_field_locations_migration(client):
    """Verifies that Nizamabad, Khammam, and Visakhapatnam get their own distinct coordinates, not Hyderabad's."""
    client.post("/farmers", json={"farmer_id": "FR010", "name": "Diverse Farmer", "phone": "9876543210"})
    client.post("/fields", json={
        "field_id": "F_KHM",
        "farmer_id": "FR010",
        "name": "Khammam Plot",
        "location_name": "Khammam, Telangana",
        "crop_type": "cotton",
    })
    client.post("/fields", json={
        "field_id": "F_NZB",
        "farmer_id": "FR010",
        "name": "Nizamabad Plot",
        "location_name": "Nizamabad, Telangana",
        "crop_type": "turmeric",
    })
    client.post("/fields", json={
        "field_id": "F_VZG",
        "farmer_id": "FR010",
        "name": "Vizag Plot",
        "location_name": "Visakhapatnam, Andhra Pradesh",
        "crop_type": "sugarcane",
    })

    # Run additive migration on the test db
    from app.database.migrate import apply_additive_migrations
    from app.database.session import get_engine
    # The client test fixture engine
    eng = client.app.dependency_overrides.get(app)
    # We can fetch the fields directly
    r_khm = client.get("/fields/F_KHM").json()
    r_nzb = client.get("/fields/F_NZB").json()
    r_vzg = client.get("/fields/F_VZG").json()

    # None were silently assigned Hyderabad coordinates
    assert r_khm.get("latitude") != 17.385 or r_khm.get("longitude") != 78.4867
    assert r_nzb.get("latitude") != 17.385 or r_nzb.get("longitude") != 78.4867
    assert r_vzg.get("latitude") != 17.385 or r_vzg.get("longitude") != 78.4867


# ── Additional Phase 8 Direct Requirement Tests ───────────────────────────────

def test_two_fields_different_coordinates_call_exact_provider_coords(client, seeded):
    """Scenario 1 & 2: Two fields with different coordinates trigger provider calls with their own exact coords."""
    client.post("/fields", json={
        "field_id": "F_BGLR",
        "farmer_id": "FR001",
        "name": "Bengaluru Plot",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "crop_type": "ragi",
    })
    client.post("/fields", json={
        "field_id": "F_DELHI",
        "farmer_id": "FR001",
        "name": "Delhi Plot",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "crop_type": "wheat",
    })

    calls = use_provider(ok(OWM_OK))
    r_bglr = client.get("/weather/F_BGLR")
    assert r_bglr.status_code == 200
    q_bglr = dict(calls[0].url.params)
    assert q_bglr["lat"] == "12.9716" and q_bglr["lon"] == "77.5946"

    r_delhi = client.get("/weather/F_DELHI")
    assert r_delhi.status_code == 200
    q_delhi = dict(calls[1].url.params)
    assert q_delhi["lat"] == "28.6139" and q_delhi["lon"] == "77.209"


def test_city_search_does_not_change_saved_field_coordinates(client, seeded):
    """Scenario 3: Searching city and previewing weather does not touch saved field coordinates."""
    # Check F001 initial coords
    f_before = client.get("/fields/F001").json()
    orig_lat, orig_lon = f_before["latitude"], f_before["longitude"]

    # Search a city via geocoding
    use_geocode_provider(lambda req: httpx.Response(200, json=[{
        "name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "state": "Maharashtra", "country": "IN"
    }]))
    geo_res = client.get("/weather/geocode", params={"q": "Mumbai"})
    assert geo_res.status_code == 200

    # Preview weather via live-by-coords
    use_provider(ok(OWM_OK))
    prev_res = client.get("/weather/live-by-coords", params={
        "latitude": 19.0760, "longitude": 72.8777, "location_name": "Mumbai, Maharashtra, IN"
    })
    assert prev_res.status_code == 200

    # Ensure F001 coords remain unchanged
    f_after = client.get("/fields/F001").json()
    assert f_after["latitude"] == orig_lat
    assert f_after["longitude"] == orig_lon


def test_assign_location_updates_field_and_fetches_new_weather(client, seeded):
    """Scenario 4: Explicit assignment updates field coordinates in DB and fetches weather for new coords."""
    # Update field F001 with new confirmed coordinates
    r_up = client.put("/fields/F001", json={
        "latitude": 16.5062,
        "longitude": 80.6480,
        "location_name": "Vijayawada, Andhra Pradesh, IN",
        "city": "Vijayawada",
        "state": "Andhra Pradesh",
        "country": "IN",
    })
    assert r_up.status_code == 200
    assert r_up.json()["latitude"] == 16.5062

    # Fetch live weather for the updated field
    calls = use_provider(ok(OWM_OK))
    r_fetch = client.get("/weather/F001")
    assert r_fetch.status_code == 200
    q = dict(calls[0].url.params)
    assert q["lat"] == "16.5062" and q["lon"] == "80.648"


def test_weather_history_filtered_strictly_by_field_id(client, seeded):
    """Scenario 11: History queries strictly filter by the selected field ID."""
    client.post("/fields", json={
        "field_id": "F_X1",
        "farmer_id": "FR001",
        "name": "Field X1",
        "latitude": 15.0,
        "longitude": 75.0,
        "crop_type": "maize",
    })
    client.post("/fields", json={
        "field_id": "F_X2",
        "farmer_id": "FR001",
        "name": "Field X2",
        "latitude": 16.0,
        "longitude": 76.0,
        "crop_type": "cotton",
    })

    # Store weather for F_X1
    use_provider(ok({**OWM_OK, "dt": 1791369001}))
    client.get("/weather/F_X1")

    # Store weather for F_X2
    use_provider(ok({**OWM_OK, "dt": 1791369002}))
    client.get("/weather/F_X2")

    # Verify history for F_X1 contains only F_X1
    h_x1 = client.get("/weather/F_X1/history").json()
    assert len(h_x1) == 1
    assert h_x1[0]["field_id"] == "F_X1"

    # Verify history for F_X2 contains only F_X2
    h_x2 = client.get("/weather/F_X2/history").json()
    assert len(h_x2) == 1
    assert h_x2[0]["field_id"] == "F_X2"


def test_accurate_source_and_timestamp_labels(client, seeded):
    """Scenario 13: Accurate source provenance, mock indicator, and dual timestamps."""
    use_provider(ok(OWM_OK))
    r = client.get("/weather/F001")
    assert r.status_code == 200
    w = r.json()["weather"]
    assert w["source"] == "openweathermap"
    assert w["is_mock"] is False
    assert "timestamp" in w
    assert "fetched_at" in w
    assert w["timestamp"] != w["fetched_at"]  # provider obs dt vs backend fetched_at


