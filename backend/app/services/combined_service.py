from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import WeatherData
from app.schemas.combined import CombinedFieldData, CombinedRecord
from app.services import registry_service as registry
from app.services import sensor_service, weather_service


def combined_field_data(db: Session, field_id: str, limit: int) -> CombinedFieldData:
    field = registry.get_field_or_404(db, field_id)
    readings = sensor_service.list_readings(db, None, field_id, None, None, limit)
    records = []
    for r in readings:
        w: Optional[WeatherData] = db.scalar(
            select(WeatherData)
            .where(WeatherData.field_id == field_id, WeatherData.timestamp <= r.timestamp)
            .order_by(WeatherData.timestamp.desc()).limit(1)
        )
        age = round((r.timestamp - w.timestamp).total_seconds() / 60, 1) if w else None
        records.append(CombinedRecord(
            sensor_id=r.sensor_id, timestamp=r.timestamp, soil_moisture=r.soil_moisture,
            is_simulated=r.is_simulated, weather=w, weather_age_minutes=age))
    latest = weather_service.list_weather(db, field_id, 1)
    return CombinedFieldData(field=field, sensors=field.sensors, latest_weather=latest[0] if latest else None, records=records)
