"""SIMULATED soil-moisture sender. No hardware is involved.

Every reading it posts carries "is_simulated": true so it can always be told apart from real data.

Usage examples:
  # REST simulation:
  python scripts/simulate_sensor.py --sensor-id SM001 --field-id F001 --count 12
  python scripts/simulate_sensor.py --sensor-id SM001 --count 6 --inject-faults   # also sends bad payloads

  # MQTT simulation (optional):
  python scripts/simulate_sensor.py --sensor-id SM001 --field-id F001 --count 5 --mqtt --mqtt-broker localhost
"""
import argparse
import json
import random
import time
from datetime import datetime, timedelta, timezone

import httpx


def generate(start: float, n: int, step_minutes: int, now: datetime):
    """Slow random walk (soil dries ~0.3-1%/step) clamped to 5-60%. Timestamps end at `now`."""
    value = start
    for i in range(n):
        value = max(5.0, min(60.0, value - random.uniform(0.3, 1.0) + random.choice([0, 0, 0, 3.0])))
        ts = now - timedelta(minutes=step_minutes * (n - 1 - i))
        yield ts.replace(microsecond=0, tzinfo=None).isoformat(), round(value, 2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default="http://127.0.0.1:8010")
    ap.add_argument("--sensor-id", required=True)
    ap.add_argument("--field-id")
    ap.add_argument("--count", type=int, default=10)
    ap.add_argument("--step-minutes", type=int, default=30)
    ap.add_argument("--start-moisture", type=float, default=38.0)
    ap.add_argument("--delay", type=float, default=0.0, help="seconds between posts")
    ap.add_argument("--inject-faults", action="store_true", help="also send null/out-of-range readings")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--mqtt", action="store_true", help="send readings via MQTT instead of REST")
    ap.add_argument("--mqtt-broker", default="localhost", help="MQTT broker address")
    ap.add_argument("--mqtt-port", type=int, default=1883, help="MQTT broker port")
    ap.add_argument("--mqtt-topic", default="irrigation/sensors/readings", help="MQTT publish topic")
    a = ap.parse_args()
    random.seed(a.seed)

    print("*** SIMULATED SENSOR DATA - not from real hardware ***")
    now = datetime.now(timezone.utc)
    payloads = [
        {"sensor_id": a.sensor_id, "field_id": a.field_id, "timestamp": ts, "soil_moisture": v, "is_simulated": True}
        for ts, v in generate(a.start_moisture, a.count, a.step_minutes, now)
    ]
    if a.inject_faults:
        payloads += [
            {"sensor_id": a.sensor_id, "field_id": a.field_id, "soil_moisture": None, "is_simulated": True},
            {"sensor_id": a.sensor_id, "field_id": a.field_id, "soil_moisture": 250, "is_simulated": True},
        ]

    if a.mqtt:
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            print("ERROR: paho-mqtt is required for MQTT simulation. Install with: pip install paho-mqtt")
            return

        client = mqtt.Client(client_id="simulated-sensor-sender")
        print(f"Connecting to MQTT broker {a.mqtt_broker}:{a.mqtt_port}...")
        try:
            client.connect(a.mqtt_broker, a.mqtt_port, 60)
            client.loop_start()
            for p in payloads:
                p = {k: v for k, v in p.items() if v is not None or k == "soil_moisture"}
                data = json.dumps(p)
                client.publish(a.mqtt_topic, data)
                print(f"MQTT published to {a.mqtt_topic}: {p.get('timestamp')} -> {p.get('soil_moisture')}%")
                time.sleep(max(a.delay, 0.1))
            client.loop_stop()
            client.disconnect()
            print("MQTT simulation finished.")
        except Exception as exc:
            print(f"MQTT connection failed: {exc}")
        return

    # Default: REST Ingestion
    with httpx.Client(base_url=a.base_url, timeout=10) as client:
        for p in payloads:
            p = {k: v for k, v in p.items() if v is not None or k == "soil_moisture"}
            r = client.post("/sensor/readings", json=p)
            print(r.status_code, p.get("timestamp"), p.get("soil_moisture"), "->",
                  "stored" if r.is_success else r.json().get("error", {}).get("code", "error"))
            time.sleep(a.delay)


if __name__ == "__main__":
    main()
