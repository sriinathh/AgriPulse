from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database.session import get_db, get_engine, safe_database_url
from app.database.timescale import hypertable_status
from app.schemas.sensor_reading import SensorReadingOut
from app.schemas.weather import WeatherOut
from app.services import dashboard_service, mqtt_service

router = APIRouter(tags=["system"])


@router.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


@router.get("/health/ready", tags=["meta"])
def ready(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    db_ok = True
    db_error = None
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_ok = False
        db_error = type(exc).__name__
    return {
        "status": "ok" if db_ok else "degraded",
        "database": {"ok": db_ok, "error": db_error, "url": safe_database_url(settings.database_url)},
        "environment": settings.app_env,
        "version": settings.app_version,
    }


@router.get("/system/status")
def system_status(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    ready_info = ready(db, settings)
    ts = hypertable_status(db.get_bind())
    mqtt = mqtt_service.status()
    return {
        "backend": {"ok": True, "version": settings.app_version, "environment": settings.app_env},
        "database": ready_info["database"],
        "timescaledb": {
            "available": ts.get("available"),
            "version": ts.get("version"),
            "hypertables": [h["name"] for h in ts.get("hypertables", [])],
            "reason": ts.get("reason"),
        },
        "weather": {
            "configured": settings.weather_configured,
            "mock_mode": settings.weather_mock,
            "provider": "openweathermap",
        },
        "mqtt": {
            "enabled": mqtt["enabled"],
            "configured": mqtt["enabled"],
            "connected": mqtt["connected"],
            "broker": mqtt["broker"],
            "topic": mqtt["topic"],
            "last_error": mqtt["last_error"],
        },
        "docs": "/docs",
    }


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    data = dashboard_service.summary(db)
    data["latest_readings"] = [SensorReadingOut.model_validate(r).model_dump() for r in data["latest_readings"]]
    data["latest_weather"] = WeatherOut.model_validate(data["latest_weather"]).model_dump() if data["latest_weather"] else None
    return data
