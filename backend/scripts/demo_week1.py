"""Week 1 end-to-end demo against a RUNNING server (Step 10).

  uvicorn app.main:app &            # in another terminal
  python scripts/demo_week1.py [--base-url http://127.0.0.1:8000]

Sensor values are SIMULATED (is_simulated=true). Weather is fetched LIVE from OpenWeatherMap;
if OPENWEATHER_API_KEY is missing or the API is unreachable the demo shows the controlled error and carries on.
"""
import argparse
import json
import random
from datetime import datetime, timedelta, timezone

import httpx


def show(title, r):
    print(f"\n== {title}\n   {r.request.method} {r.request.url.path} -> {r.status_code}")
    print("   " + json.dumps(r.json(), indent=2).replace("\n", "\n   ")[:1400])
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    a = ap.parse_args()
    c = httpx.Client(base_url=a.base_url, timeout=15)
    random.seed(7)

    show("1. Register farmer", c.post("/farmers", json={"farmer_id": "FR001", "name": "Harini", "phone": "9999900000"}))
    show("2-3. Register field with crop (Rice)", c.post("/fields", json={
        "field_id": "F001", "farmer_id": "FR001", "name": "North Paddy", "location_name": "Hyderabad, Telangana",
        "latitude": 17.385, "longitude": 78.4867, "crop_type": "Rice", "area_hectares": 1.5}))
    show("4. Register soil-moisture sensor", c.post("/sensors", json={"sensor_id": "SM001", "field_id": "F001"}))

    print("\n*** Steps 5-7: SIMULATED sensor readings (no real hardware) ***")
    now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    value = 38.0
    for i in range(4, 0, -1):
        value = round(value - random.uniform(0.3, 1.0), 2)
        ts = (now - timedelta(minutes=30 * i)).isoformat()
        r = c.post("/sensor/readings", json={"sensor_id": "SM001", "field_id": "F001", "timestamp": ts,
                                             "soil_moisture": value, "is_simulated": True})
        print(f"   valid   {ts} {value:>6} -> {r.status_code} {r.json().get('status', r.json().get('error', {}).get('code'))}")
    for label, payload in (("null moisture", {"soil_moisture": None}), ("out of range (250)", {"soil_moisture": 250}),
                           ("unknown sensor", {"sensor_id": "SM404", "soil_moisture": 30})):
        r = c.post("/sensor/readings", json={"sensor_id": "SM001", "is_simulated": True, **payload})
        print(f"   invalid {label:<20} -> {r.status_code} {r.json()['error']['code']}")

    show("8-10. Fetch live weather for the field, normalise, store", c.get("/weather/F001"))
    show("11. Combined sensor + weather view", c.get("/fields/F001/combined", params={"limit": 5}))


if __name__ == "__main__":
    main()
