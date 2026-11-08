"""Weather integration (OpenWeatherMap current-weather API).

Layers kept separate:
  WeatherProvider  - the only code that talks to the external API; returns normalised values or raises AppError
  store_weather    - persistence
  get_weather_for_field - orchestration used by the router

Nothing is ever made up: on any failure an AppError is raised and nothing is stored.
The API key is read from settings (env var) and is never logged or returned.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Tuple

import httpx
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.errors import AppError
from app.models import Field, WeatherData
from app.services.data_cleaning_service import DataValidationError, clean_weather


@dataclass
class ProviderWeather:
    timestamp: datetime  # naive UTC observation time
    temperature: float
    humidity: float
    rainfall: float
    # Display-only extras (not stored, not part of the Week-1 contract)
    description: Optional[str] = None
    feels_like: Optional[float] = None
    wind_speed: Optional[float] = None  # m/s
    provider_latitude: Optional[float] = None
    provider_longitude: Optional[float] = None
    provider_city: Optional[str] = None
    provider_country: Optional[str] = None


class WeatherProvider:
    def __init__(self, settings: Settings, transport: Optional[httpx.BaseTransport] = None):
        self._settings = settings
        self._transport = transport  # injected by automated tests only
        self.last_payload: Optional[dict] = None  # raw provider JSON of the latest call (for --debug; never contains the key)

    def fetch_current(self, latitude: float, longitude: float) -> ProviderWeather:
        if latitude is None or longitude is None:
            raise AppError(422, "coordinates_missing", "Latitude and longitude must both be provided.")
        if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
            raise AppError(422, "coordinates_invalid",
                           f"Coordinates ({latitude}, {longitude}) are invalid. Latitude must be in [-90, 90] and longitude in [-180, 180].")
        s = self._settings
        if not s.openweather_api_key:
            raise AppError(503, "weather_not_configured",
                           "OPENWEATHER_API_KEY is not set; weather cannot be fetched.")
        params = {"lat": latitude, "lon": longitude, "units": "metric", "appid": s.openweather_api_key}
        try:
            with httpx.Client(timeout=s.weather_timeout_seconds, transport=self._transport) as client:
                resp = client.get(s.openweather_base_url, params=params)
        except httpx.TimeoutException:
            raise AppError(503, "weather_timeout", "Weather provider did not respond in time. Try again later.")
        except httpx.RequestError as exc:  # message intentionally omitted: it can contain the request URL (and key)
            raise AppError(503, "weather_unavailable", f"Weather provider unreachable ({type(exc).__name__}).")

        if resp.status_code in (401, 403):
            raise AppError(502, "weather_auth_failed",
                           f"Weather provider refused the request (HTTP {resp.status_code}). "
                           "Check OPENWEATHER_API_KEY (new keys can take a while to activate) and that the host is not blocked by a firewall/proxy.")
        if resp.status_code == 429:
            raise AppError(503, "weather_rate_limited", "Weather provider rate limit reached. Try again later.")
        if resp.status_code >= 400:
            raise AppError(502, "weather_provider_error", f"Weather provider returned HTTP {resp.status_code}.")
        try:
            self.last_payload = resp.json()
        except ValueError:
            self.last_payload = None
        return self.parse(resp)

    @staticmethod
    def parse(resp: httpx.Response) -> ProviderWeather:
        try:
            data = resp.json()
        except ValueError:
            raise AppError(502, "weather_bad_response", "Weather provider returned invalid JSON.")
        if not isinstance(data, dict):
            raise AppError(502, "weather_bad_response", "Weather provider returned an unexpected payload.")

        main = data.get("main") if isinstance(data.get("main"), dict) else {}
        temperature, humidity, dt = main.get("temp"), main.get("humidity"), data.get("dt")
        missing: List[str] = [n for n, v in (("temperature", temperature), ("humidity", humidity), ("timestamp", dt)) if v is None]

        # OpenWeatherMap omits the "rain" object when there is no precipitation, so absence = 0 mm.
        # If it is present, "1h" (mm in last hour) is used; a lone "3h" is averaged to mm/h.
        rain = data.get("rain")
        if rain is None:
            rainfall = 0.0
        elif isinstance(rain, dict) and rain.get("1h") is not None:
            rainfall = rain["1h"]
        elif isinstance(rain, dict) and rain.get("3h") is not None:
            try:
                rainfall = float(rain["3h"]) / 3
            except (TypeError, ValueError):
                rainfall = None
        else:
            rainfall = None
        if rainfall is None:
            missing.append("rainfall")

        if missing:
            raise AppError(502, "weather_incomplete_data", "Weather provider response is missing required values.",
                           [{"field": m, "code": "missing_value"} for m in missing])
        try:
            cleaned = clean_weather(temperature, humidity, rainfall)
            observed = datetime.fromtimestamp(float(dt), tz=timezone.utc).replace(tzinfo=None)
        except DataValidationError as exc:
            raise AppError(502, "weather_invalid_data", "Weather provider returned implausible values; discarded.",
                           [i.as_dict() for i in exc.issues])
        except (TypeError, ValueError, OverflowError, OSError):
            raise AppError(502, "weather_invalid_data", "Weather provider returned an invalid observation time.")
        weather_list = data.get("weather")
        description = weather_list[0].get("description") if isinstance(weather_list, list) and weather_list and isinstance(weather_list[0], dict) else None
        wind = data.get("wind") if isinstance(data.get("wind"), dict) else {}
        coord = data.get("coord") if isinstance(data.get("coord"), dict) else {}
        sys_dict = data.get("sys") if isinstance(data.get("sys"), dict) else {}

        def _num(v):
            return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None

        return ProviderWeather(
            observed, cleaned.temperature, cleaned.humidity, cleaned.rainfall,
            description=description, feels_like=_num(main.get("feels_like")), wind_speed=_num(wind.get("speed")),
            provider_latitude=_num(coord.get("lat")),
            provider_longitude=_num(coord.get("lon")),
            provider_city=str(data["name"]) if data.get("name") else None,
            provider_country=str(sys_dict["country"]) if sys_dict.get("country") else None,
        )


def store_weather(db: Session, field_id: str, w: ProviderWeather, source: str = "openweathermap", is_mock: bool = False) -> Tuple[WeatherData, bool]:
    """Insert; if we already hold this (field, observation time) return the existing row and update fetched_at."""
    # First, check if this observation already exists to avoid unnecessary IntegrityError rollbacks
    existing = db.scalar(
        select(WeatherData).where(WeatherData.field_id == field_id, WeatherData.timestamp == w.timestamp)
    )
    if existing is not None:
        existing.fetched_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        return existing, False

    record = WeatherData(
        field_id=field_id, timestamp=w.timestamp, temperature=w.temperature,
        humidity=w.humidity, rainfall=w.rainfall, source=source, is_mock=is_mock,
        wind_speed=w.wind_speed, condition=w.description,
    )
    db.add(record)
    try:
        db.commit()
        return record, True
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(WeatherData).where(WeatherData.field_id == field_id, WeatherData.timestamp == w.timestamp))
        if existing is None:
            raise
        existing.fetched_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        return existing, False


def mock_observation(field: Field) -> ProviderWeather:
    """Deterministic synthetic weather for UI/demo only.
    The values are derived from the field's latitude/longitude so that
    different coordinates produce different (but repeatable) results.
    The function never makes network calls and always marks the observation
    as a mock.
    """
    # Simple deterministic algorithm based on coordinates
    # Ensure latitude/longitude are not None (caller checks)
    lat = field.latitude or 0.0
    lon = field.longitude or 0.0
    # Temperature: map latitude range [-90,90] to a realistic 10‑35°C
    temperature = round(((lat + 90) % 25) + 10, 1)
    # Humidity: map longitude range [-180,180] to 30‑80%
    humidity = round(((lon + 180) % 50) + 30, 1)
    # Rainfall: simple periodic pattern, 0‑2 mm
    rainfall = round(((int(lat * lon) % 4) * 0.5), 1)
    # Wind speed: 0.5‑5.5 m/s based on absolute sum of coordinates
    wind_speed = round(((abs(lat) + abs(lon)) % 5) + 0.5, 1)
    now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    return ProviderWeather(
        timestamp=now,
        temperature=temperature,
        humidity=humidity,
        rainfall=rainfall,
        description="simulated deterministic mock",
        feels_like=temperature + 1.0,
        wind_speed=wind_speed,
        provider_latitude=lat,
        provider_longitude=lon,
        provider_city=None,
        provider_country=None,
    )
    """Clearly labelled synthetic weather for UI/demo only. Never presented as live API data."""
    now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    return ProviderWeather(
        timestamp=now,
        temperature=28.0,
        humidity=62.0,
        rainfall=0.0,
        description="simulated clear sky (mock)",
        feels_like=29.0,
        wind_speed=2.5,
    )


def get_weather_for_field(db: Session, field: Field, provider: WeatherProvider) -> Tuple[WeatherData, bool, ProviderWeather]:
    if field.latitude is None or field.longitude is None:
        raise AppError(422, "field_location_missing",
                       f"Field '{field.field_id}' has no latitude/longitude configured; weather cannot be requested.")
    if not (-90.0 <= field.latitude <= 90.0 and -180.0 <= field.longitude <= 180.0):
        raise AppError(422, "field_coordinates_invalid",
                       f"Field '{field.field_id}' has invalid coordinates ({field.latitude}, {field.longitude}). Latitude must be in [-90, 90] and longitude in [-180, 180].")
    # Use deterministic mock only when the provider is in real‑mode (no injected transport).
    # In tests we inject a MockTransport, so we must fetch via the provider even if WEATHER_MOCK=true.
    if provider._settings.weather_mock and provider._transport is None:
        pw = mock_observation(field)
        rec, created = store_weather(db, field.field_id, pw, source="mock", is_mock=True)
        return rec, created, pw
    pw = provider.fetch_current(field.latitude, field.longitude)
    rec, created = store_weather(db, field.field_id, pw)
    return rec, created, pw


def list_all_weather(db: Session, field_id: Optional[str], limit: int) -> List[WeatherData]:
    stmt = select(WeatherData).order_by(WeatherData.timestamp.desc()).limit(limit)
    if field_id:
        stmt = stmt.where(WeatherData.field_id == field_id)
    return list(db.scalars(stmt))


def list_weather(db: Session, field_id: str, limit: int) -> List[WeatherData]:
    stmt = select(WeatherData).where(WeatherData.field_id == field_id).order_by(WeatherData.timestamp.desc()).limit(limit)
    return list(db.scalars(stmt))
