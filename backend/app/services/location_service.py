"""Turn a place name into coordinates (OpenWeatherMap geocoding) or guess the user's location from their IP.

IP geolocation is only city-level and can point at the ISP's location, so callers must let the user confirm.
Only used by the terminal tool; the REST API still takes coordinates from the registered field.
"""
from dataclasses import dataclass
from typing import List, Optional

import httpx

from app.config import Settings
from app.errors import AppError

IP_LOOKUP_URLS = ["https://ipinfo.io/json", "https://ipapi.co/json/"]


@dataclass
class Place:
    name: str
    latitude: float
    longitude: float
    state: Optional[str] = None
    country: Optional[str] = None

    def label(self) -> str:
        return ", ".join(p for p in (self.name, self.state, self.country) if p)


def _get(settings: Settings, url: str, params: Optional[dict], transport: Optional[httpx.BaseTransport], what: str) -> httpx.Response:
    try:
        with httpx.Client(timeout=settings.weather_timeout_seconds, transport=transport) as client:
            return client.get(url, params=params, headers={"Accept": "application/json"})
    except httpx.TimeoutException:
        raise AppError(503, "location_timeout", f"The {what} service did not respond in time.")
    except httpx.RequestError as exc:  # message omitted: it may contain the request URL (and key)
        raise AppError(503, "location_unavailable", f"Could not reach the {what} service ({type(exc).__name__}). Check your internet connection.")


def geocode(settings: Settings, query: str, transport: Optional[httpx.BaseTransport] = None, limit: int = 5) -> List[Place]:
    query = ",".join(part.strip() for part in query.split(",") if part.strip())
    if not query:
        raise AppError(422, "location_empty", "Please enter a location.")
    if not settings.openweather_api_key:
        raise AppError(503, "weather_not_configured", "OPENWEATHER_API_KEY is not set.")
    resp = _get(settings, settings.openweather_geocode_url,
                {"q": query, "limit": limit, "appid": settings.openweather_api_key}, transport, "location search")
    if resp.status_code in (401, 403):
        raise AppError(502, "weather_auth_failed",
                       f"The location service refused the request (HTTP {resp.status_code}). Check OPENWEATHER_API_KEY "
                       "(new keys can take a while to activate) and that the host is not blocked by a firewall/proxy.")
    if resp.status_code == 429:
        raise AppError(503, "weather_rate_limited", "Rate limit reached. Try again later.")
    if resp.status_code >= 400:
        raise AppError(502, "location_service_error", f"The location service returned HTTP {resp.status_code}.")
    try:
        rows = resp.json()
    except ValueError:
        raise AppError(502, "location_bad_response", "The location service returned invalid data.")
    places = []
    for r in rows if isinstance(rows, list) else []:
        try:
            places.append(Place(str(r["name"]), float(r["lat"]), float(r["lon"]), r.get("state"), r.get("country")))
        except (KeyError, TypeError, ValueError):
            continue
    if not places:
        raise AppError(404, "location_not_found", f"No place found for '{query}'. Try a nearby city, or add the country, e.g. 'Hyderabad, IN'.")
    return places


def locate_by_ip(settings: Settings, transport: Optional[httpx.BaseTransport] = None) -> Place:
    last: Optional[AppError] = None
    for url in IP_LOOKUP_URLS:
        try:
            resp = _get(settings, url, None, transport, "IP location")
            if resp.status_code >= 400:
                raise AppError(502, "location_service_error", f"HTTP {resp.status_code}")
            data = resp.json()
            if isinstance(data.get("loc"), str) and "," in data["loc"]:  # ipinfo.io
                lat, lon = (float(x) for x in data["loc"].split(",", 1))
            else:  # ipapi.co
                lat, lon = float(data["latitude"]), float(data["longitude"])
            return Place(data.get("city") or "Current location", lat, lon, data.get("region"), data.get("country") or data.get("country_code"))
        except AppError as exc:
            last = exc
        except (ValueError, KeyError, TypeError, AttributeError):
            last = AppError(502, "location_bad_response", "The IP location service returned unusable data.")
    raise last or AppError(502, "location_unavailable", "Could not determine your location.")
