from datetime import datetime, timezone
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database.session import get_db
from app.errors import AppError
from app.schemas.weather import PlaceOut, SearchedWeatherOut, WeatherFetchResponse, WeatherOut
from app.services import quality_service, registry_service as registry
from app.services import weather_service
from app.services.location_service import Place, geocode
from app.services.weather_service import ProviderWeather, WeatherProvider

router = APIRouter(prefix="/weather", tags=["weather"])


def get_weather_provider(settings: Settings = Depends(get_settings)) -> WeatherProvider:
    return WeatherProvider(settings)


def get_location_transport() -> Optional[httpx.BaseTransport]:
    return None


# ── Geocoding ─────────────────────────────────────────────────────────────────

@router.get("/geocode", response_model=List[PlaceOut])
def geocode_location(
    q: str = Query(..., min_length=1, description="City name, optionally with country code, e.g. 'Hyderabad, IN'"),
    limit: int = Query(5, ge=1, le=10),
    settings: Settings = Depends(get_settings),
    transport: Optional[httpx.BaseTransport] = Depends(get_location_transport),
):
    """Search for real geographic locations using the OpenWeatherMap Geocoding API.

    Returns up to *limit* candidates with name, state, country, and coordinates.
    No field or sensor is required — purely a search tool for the UI.
    """
    places: List[Place] = geocode(settings, q, transport=transport, limit=limit)
    return [
        PlaceOut(
            name=p.name,
            state=p.state,
            country=p.country,
            latitude=p.latitude,
            longitude=p.longitude,
            label=p.label(),
        )
        for p in places
    ]


@router.get("/live-by-coords", response_model=SearchedWeatherOut)
def live_weather_by_coordinates(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude between -90 and 90"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude between -180 and 180"),
    location_name: Optional[str] = Query(None, description="Optional label for the searched location"),
    provider: WeatherProvider = Depends(get_weather_provider),
):
    """Fetch live weather observation for an arbitrary searched location WITHOUT persisting to any field.

    Preserves the strict boundary between ephemeral search results and monitored field records.
    """
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    # Use deterministic mock only when no transport is injected (i.e., in real runtime).
    if provider._settings.weather_mock and provider._transport is None:
        # Deterministic mock based on requested coordinates – repeatable per lat/lon
        # Temperature: map latitude [-90,90] → 10‑35°C
        temperature = round(((latitude + 90) % 25) + 10, 1)
        # Humidity: map longitude [-180,180] → 30‑80%
        humidity = round(((longitude + 180) % 50) + 30, 1)
        # Rainfall: simple pattern 0‑2 mm based on product of lat/lon
        rainfall = round(((int(latitude * longitude) % 4) * 0.5), 1)
        # Wind speed: 0.5‑5.5 m/s based on sum of absolute coordinates
        wind_speed = round(((abs(latitude) + abs(longitude)) % 5) + 0.5, 1)
        mock = ProviderWeather(
            timestamp=now_utc,
            temperature=temperature,
            humidity=humidity,
            rainfall=rainfall,
            description="simulated deterministic mock",
            feels_like=temperature + 1.0,
            wind_speed=wind_speed,
        )
        return SearchedWeatherOut(
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            timestamp=mock.timestamp,
            fetched_at=now_utc,
            temperature=mock.temperature,
            humidity=mock.humidity,
            rainfall=mock.rainfall,
            wind_speed=mock.wind_speed,
            condition=mock.description,
            source="mock",
            is_mock=True,
        )
        return SearchedWeatherOut(
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            timestamp=mock.timestamp,
            fetched_at=now_utc,
            temperature=mock.temperature,
            humidity=mock.humidity,
            rainfall=mock.rainfall,
            wind_speed=mock.wind_speed,
            condition=mock.description,
            source="mock",
            is_mock=True,
        )

    w = provider.fetch_current(latitude, longitude)
    return SearchedWeatherOut(
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
        timestamp=w.timestamp,
        fetched_at=now_utc,
        temperature=w.temperature,
        humidity=w.humidity,
        rainfall=w.rainfall,
        wind_speed=w.wind_speed,
        condition=w.description,
        source="openweathermap",
        is_mock=False,
        provider_coordinates={"latitude": w.provider_latitude, "longitude": w.provider_longitude} if w.provider_latitude is not None else None,
        provider_location=f"{w.provider_city}, {w.provider_country}" if w.provider_city else None,
    )



# ── Observations ───────────────────────────────────────────────────────────────

@router.get("/observations", response_model=List[WeatherOut])
def list_observations(
    field_id: Optional[str] = None, limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)
):
    if field_id:
        registry.get_field_or_404(db, field_id)
    return weather_service.list_all_weather(db, field_id, limit)


# ── Per-field endpoints ────────────────────────────────────────────────────────

@router.get("/{field_id}", response_model=WeatherFetchResponse)
def fetch_weather(field_id: str, db: Session = Depends(get_db), provider: WeatherProvider = Depends(get_weather_provider)):
    """Fetch live weather for the field's configured location, normalise, store, return."""
    field = registry.get_field_or_404(db, field_id)
    try:
        record, created, pw = weather_service.get_weather_for_field(db, field, provider)
    except AppError as exc:
        if exc.code not in ("field_location_missing", "field_coordinates_invalid"):
            quality_service.record_event(
                db, exc.code, "weather", exc.message, field_id=field_id
            )
        raise
    return WeatherFetchResponse(
        status="stored" if created else "already_stored",
        weather=record,
        mock=bool(record.is_mock),
        requested_coordinates={"latitude": field.latitude, "longitude": field.longitude},
        provider_coordinates={"latitude": pw.provider_latitude, "longitude": pw.provider_longitude} if pw and pw.provider_latitude is not None else None,
        provider_location=f"{pw.provider_city}, {pw.provider_country}" if pw and pw.provider_city else None,
    )


@router.get("/{field_id}/history", response_model=List[WeatherOut])
def weather_history(field_id: str, limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    registry.get_field_or_404(db, field_id)
    return weather_service.list_weather(db, field_id, limit)


@router.get("/{field_id}/latest", response_model=WeatherOut)
def latest_stored_weather(field_id: str, db: Session = Depends(get_db)):
    """Most recent *stored* observation (real data previously fetched). Use when the live call is failing."""
    registry.get_field_or_404(db, field_id)
    rows = weather_service.list_weather(db, field_id, 1)
    if not rows:
        raise AppError(404, "no_weather_data", f"No weather has been stored for field '{field_id}' yet.")
    return rows[0]
