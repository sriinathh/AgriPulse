"""Optional MQTT subscriber. Reuses REST ingestion validation/persistence.

Startup never fails if the broker is down: the loop reconnects in a background thread.
"""
import json
import logging
import threading
from typing import Optional

from app.config import Settings, get_settings
from app.database.session import get_sessionmaker
from app.errors import AppError
from app.schemas.sensor_reading import SensorReadingIn
from app.services import sensor_service

log = logging.getLogger("irrigation.mqtt")

_state = {
    "enabled": False,
    "connected": False,
    "broker": None,
    "topic": None,
    "last_error": None,
    "messages_ok": 0,
    "messages_rejected": 0,
}


def status() -> dict:
    return dict(_state)


def parse_mqtt_payload(raw: bytes) -> SensorReadingIn:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("MQTT payload is not valid UTF-8") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("MQTT payload is not valid JSON") from exc
    if not isinstance(data, dict):
        raise ValueError("MQTT payload must be a JSON object")
    return SensorReadingIn.model_validate(data)


def ingest_mqtt_message(raw: bytes, settings: Optional[Settings] = None) -> None:
    settings = settings or get_settings()
    payload = parse_mqtt_payload(raw)
    db = get_sessionmaker()()
    try:
        sensor_service.ingest_reading(db, payload, settings, source="mqtt")
        _state["messages_ok"] = int(_state["messages_ok"]) + 1
    finally:
        db.close()


def _on_connect(client, userdata, flags, reason_code, properties=None):
    ok = reason_code == 0 or str(reason_code) in ("Success", "0")
    _state["connected"] = bool(ok)
    if ok:
        topic = userdata["topic"]
        client.subscribe(topic)
        _state["last_error"] = None
        log.info("MQTT connected; subscribed to %s", topic)
    else:
        _state["last_error"] = f"connect reason {reason_code}"
        log.warning("MQTT connection refused (reason=%s). Will retry.", reason_code)


def _on_disconnect(client, userdata, flags, reason_code, properties=None):
    _state["connected"] = False
    log.warning("MQTT disconnected (reason=%s); client will reconnect.", reason_code)


def _on_message(client, userdata, msg):
    settings = userdata["settings"]
    try:
        ingest_mqtt_message(msg.payload, settings)
    except AppError as exc:
        _state["messages_rejected"] = int(_state["messages_rejected"]) + 1
        log.warning("MQTT message rejected: %s", exc.code)
    except Exception as exc:
        _state["messages_rejected"] = int(_state["messages_rejected"]) + 1
        log.warning("MQTT message discarded (%s).", type(exc).__name__)


def start_mqtt_background(settings: Settings) -> None:
    _state.update({
        "enabled": bool(settings.mqtt_enabled),
        "broker": f"{settings.mqtt_broker}:{settings.mqtt_port}" if settings.mqtt_enabled else None,
        "topic": settings.mqtt_topic if settings.mqtt_enabled else None,
        "connected": False,
        "last_error": None,
    })
    if not settings.mqtt_enabled:
        log.info("MQTT subscriber disabled (MQTT_ENABLED=false).")
        return
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        _state["last_error"] = "paho-mqtt is not installed"
        log.warning("MQTT enabled but paho-mqtt is not installed; subscriber not started.")
        return

    userdata = {"topic": settings.mqtt_topic, "settings": settings}

    try:
        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=settings.mqtt_client_id,
            userdata=userdata,
        )
    except Exception:
        client = mqtt.Client(client_id=settings.mqtt_client_id, userdata=userdata)

    client.reconnect_delay_set(min_delay=1, max_delay=60)
    client.on_connect = _on_connect
    client.on_disconnect = _on_disconnect
    client.on_message = _on_message
    if settings.mqtt_username:
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

    def _loop():
        try:
            client.connect_async(settings.mqtt_broker, settings.mqtt_port, keepalive=30)
            client.loop_forever(retry_first_connection=True)
        except Exception as exc:
            _state["connected"] = False
            _state["last_error"] = type(exc).__name__
            log.warning("MQTT loop ended (%s). Backend continues without MQTT.", type(exc).__name__)

    thread = threading.Thread(target=_loop, name="mqtt-subscriber", daemon=True)
    thread.start()
    log.info("MQTT subscriber thread started for %s (will retry if broker is down).", _state["broker"])
