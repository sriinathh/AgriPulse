"""Explainable irrigation recommendation engine.

Based on FAO-56 Irrigation Water Management agronomic principles.
Never claims rule-based logic is an AI model; clearly reports data sources,
sensor freshness, soil moisture deficits, and weather considerations.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Crop, Field, SensorReading, WeatherData

# Agronomic moisture requirements (volumetric water content %) by crop
# format: (min_threshold_pct, optimal_target_pct)
CROP_MOISTURE_PROFILES: Dict[str, tuple[float, float]] = {
    "rice": (45.0, 65.0),
    "maize": (25.0, 42.0),
    "wheat": (25.0, 40.0),
    "cotton": (20.0, 38.0),
    "sugarcane": (40.0, 60.0),
    "banana": (35.0, 55.0),
    "tomato": (28.0, 45.0),
    "potato": (28.0, 45.0),
    "onion": (25.0, 40.0),
    "chickpea": (18.0, 32.0),
    "lentil": (18.0, 32.0),
    "grapes": (20.0, 35.0),
    "apple": (25.0, 45.0),
    "orange": (25.0, 42.0),
    "default": (25.0, 40.0),
}

# Growth stage sensitivity modifiers
STAGE_MODIFIERS: Dict[str, float] = {
    "seedling": 0.8,     # shallow roots, avoid waterlogging
    "vegetative": 1.0,   # baseline canopy expansion
    "flowering": 1.25,   # critical reproductive period: peak water demand
    "fruiting": 1.15,    # fruit filling stage
    "maturity": 0.6,     # drying off before harvest to prevent mold
}


def recommend_irrigation(
    db: Optional[Session] = None,
    field_id: Optional[str] = None,
    crop_type: Optional[str] = None,
    growth_stage: Optional[str] = "vegetative",
    soil_moisture: Optional[float] = None,
    temperature: Optional[float] = None,
    recent_rainfall_mm: Optional[float] = 0.0,
    forecast_rainfall_mm: Optional[float] = 0.0,
) -> Dict[str, Any]:
    sensor_freshness = "manual_input"
    field_name = None
    evaluated_crop = (crop_type or "default").lower().strip()
    evaluated_stage = (growth_stage or "vegetative").lower().strip()
    reading_timestamp = None

    # If field_id is provided and database session is available, resolve from live DB records
    if field_id and db is not None:
        field = db.get(Field, field_id)
        if field:
            field_name = field.name
            if not crop_type and field.crop_type:
                evaluated_crop = field.crop_type.lower().strip()

            # Check crop record for growth stage
            crop_record = db.scalar(select(Crop).where(Crop.field_id == field_id).order_by(Crop.created_at.desc()).limit(1))
            if crop_record:
                if crop_record.crop_type:
                    evaluated_crop = crop_record.crop_type.lower().strip()
                if crop_record.growth_stage:
                    evaluated_stage = crop_record.growth_stage.lower().strip()

            # Check latest sensor reading
            latest_reading = db.scalar(
                select(SensorReading)
                .where(SensorReading.field_id == field_id)
                .order_by(SensorReading.timestamp.desc())
                .limit(1)
            )
            if latest_reading and soil_moisture is None:
                soil_moisture = latest_reading.soil_moisture if latest_reading.soil_moisture is not None else latest_reading.value
                reading_timestamp = latest_reading.timestamp
                now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
                age_hours = (now_utc - latest_reading.timestamp).total_seconds() / 3600.0
                if age_hours > 24:
                    sensor_freshness = f"stale ({age_hours:.1f} hours old)"
                elif age_hours > 6:
                    sensor_freshness = f"aging ({age_hours:.1f} hours old)"
                else:
                    sensor_freshness = f"fresh ({age_hours:.1f} hours old)"

            # Check latest weather
            latest_weather = db.scalar(
                select(WeatherData)
                .where(WeatherData.field_id == field_id)
                .order_by(WeatherData.timestamp.desc())
                .limit(1)
            )
            if latest_weather:
                if temperature is None:
                    temperature = latest_weather.temperature
                if (recent_rainfall_mm is None or recent_rainfall_mm == 0.0) and latest_weather.rainfall is not None:
                    recent_rainfall_mm = latest_weather.rainfall

    # Defaults if completely missing
    evaluated_moisture = soil_moisture if soil_moisture is not None else 30.0
    evaluated_temp = temperature if temperature is not None else 25.0
    evaluated_recent_rain = recent_rainfall_mm or 0.0
    evaluated_forecast_rain = forecast_rainfall_mm or 0.0

    # Look up crop profile
    min_thresh, target_thresh = CROP_MOISTURE_PROFILES.get(evaluated_crop, CROP_MOISTURE_PROFILES["default"])
    stage_factor = STAGE_MODIFIERS.get(evaluated_stage, 1.0)
    adjusted_min = round(min_thresh * stage_factor, 1)
    adjusted_target = round(target_thresh * stage_factor, 1)

    # Core FAO-56 moisture deficit calculation
    deficit = max(0.0, adjusted_target - evaluated_moisture)

    # Decision Matrix
    action = "MAINTAIN_MONITORING"
    urgency = "LOW"
    water_mm = 0.0
    reason_parts = []

    # Weather overrides
    if evaluated_recent_rain >= 12.0:
        action = "DEFER_DUE_TO_RAIN"
        urgency = "NONE"
        water_mm = 0.0
        reason_parts.append(
            f"Significant recent rainfall ({evaluated_recent_rain}mm) recorded. Irrigation is deferred to conserve water and prevent root hypoxia."
        )
    elif evaluated_forecast_rain >= 8.0 and deficit < 10.0:
        action = "DEFER_DUE_TO_RAIN"
        urgency = "LOW"
        water_mm = 0.0
        reason_parts.append(
            f"Upcoming rainfall ({evaluated_forecast_rain}mm) forecasted. Mild moisture deficit ({deficit:.1f}%) will be replenished naturally."
        )
    elif evaluated_moisture < adjusted_min:
        deficit_depth = adjusted_target - evaluated_moisture
        # 1% volumetric moisture ~ 1.0 - 1.5 mm of water depending on active root zone (typical 20-30cm root depth)
        water_mm = round(min(35.0, max(5.0, deficit_depth * 1.2)), 1)
        if evaluated_stage == "flowering":
            urgency = "HIGH"
            action = "IRRIGATE_IMMEDIATELY"
            reason_parts.append(
                f"Critical moisture deficit: {evaluated_moisture}% is below safety threshold ({adjusted_min}%). "
                f"Crop '{evaluated_crop}' is in the sensitive flowering stage where water stress reduces yield by >30%."
            )
        else:
            urgency = "HIGH" if deficit_depth > 10.0 else "MODERATE"
            action = "IRRIGATE_IMMEDIATELY"
            reason_parts.append(
                f"Current soil moisture ({evaluated_moisture}%) has dropped below the threshold ({adjusted_min}%) "
                f"for {evaluated_crop} in {evaluated_stage} stage."
            )
    elif evaluated_moisture < adjusted_target:
        deficit_depth = adjusted_target - evaluated_moisture
        water_mm = round(deficit_depth * 0.8, 1)
        action = "IRRIGATE_LIGHT"
        urgency = "MODERATE"
        reason_parts.append(
            f"Soil moisture ({evaluated_moisture}%) is above critical threshold ({adjusted_min}%) but below optimal target ({adjusted_target}%). "
            f"Light irrigation recommended to maintain transpiration efficiency."
        )
    else:
        action = "MAINTAIN_MONITORING"
        urgency = "NONE"
        water_mm = 0.0
        reason_parts.append(
            f"Soil moisture ({evaluated_moisture}%) is optimal (target: {adjusted_target}%). No irrigation required at this time."
        )

    if evaluated_temp > 34.0 and action != "DEFER_DUE_TO_RAIN":
        reason_parts.append(f"High ambient temperature ({evaluated_temp}°C) elevates evapotranspiration; irrigate during early morning or evening.")

    if "stale" in sensor_freshness:
        reason_parts.append("WARNING: Latest sensor telemetry is older than 24 hours. Physical field inspection recommended.")

    full_reason = " ".join(reason_parts)

    return {
        "action": action,
        "recommended_water_mm": water_mm,
        "urgency": urgency,
        "reason": full_reason,
        "factors_evaluated": {
            "field_id": field_id,
            "field_name": field_name,
            "crop_type": evaluated_crop,
            "growth_stage": evaluated_stage,
            "current_soil_moisture_pct": evaluated_moisture,
            "critical_threshold_pct": adjusted_min,
            "optimal_target_pct": adjusted_target,
            "ambient_temperature_c": evaluated_temp,
            "recent_rainfall_mm": evaluated_recent_rain,
            "forecast_rainfall_mm": evaluated_forecast_rain,
            "reading_timestamp": reading_timestamp.isoformat() if reading_timestamp else None,
        },
        "recommendation_engine": "Rule-based Agronomic Water Deficit Model (FAO-56 Irrigation & Drainage Guidelines)",
        "sensor_freshness": sensor_freshness,
        "limitations": (
            "Advisory recommendation only. Emitter flow rate, soil salinity, and local slope must be verified before automated actuation. "
            "Never connects directly to high-voltage pump relays without confirmed manual hardware fail-safes."
        ),
    }
