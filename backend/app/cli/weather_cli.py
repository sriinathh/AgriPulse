"""Terminal weather lookup using the LIVE OpenWeatherMap API (same provider code as the REST API).

  python -m app.cli.weather_cli                       # interactive
  python -m app.cli.weather_cli --location "Pune, IN" # no prompts
  python -m app.cli.weather_cli --current             # use IP-based current location

Nothing is stored; this is a quick lookup. Needs OPENWEATHER_API_KEY in backend/.env.
"""
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Optional

import httpx

from app.config import Settings
from app.errors import AppError
from app.services import location_service
from app.services.location_service import Place
from app.services.weather_service import ProviderWeather, WeatherProvider

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
QUIT = {"q", "quit", "exit"}


class _Done(Exception):
    """User quit or input ended."""


def _yes(answer: str, default: bool) -> bool:
    a = answer.strip().lower()
    return default if not a else a in ("y", "yes")


def _explain(exc: AppError, out: Callable[[str], None]) -> None:
    out(f"  ! {exc.message}")
    if exc.code == "weather_not_configured":
        out("    Get a free key at https://home.openweathermap.org/api_keys and put it in backend/.env as OPENWEATHER_API_KEY=...")


def _choose(places: List[Place], ask: Callable[[str], str], out: Callable[[str], None]) -> Optional[Place]:
    if len(places) == 1:
        return places[0]
    out("  Several matches:")
    for i, p in enumerate(places, 1):
        out(f"    {i}. {p.label()}  ({p.latitude:.3f}, {p.longitude:.3f})")
    while True:
        a = ask(f"  Choose 1-{len(places)} (or Enter to search again): ").strip()
        if not a:
            return None
        if a.isdigit() and 1 <= int(a) <= len(places):
            return places[int(a) - 1]
        out("  Please type one of the numbers shown.")


def pick_place(settings: Settings, ask: Callable[[str], str], out: Callable[[str], None],
               transport: Optional[httpx.BaseTransport]) -> Place:
    def read(prompt: str) -> str:
        try:
            a = ask(prompt)
        except (EOFError, KeyboardInterrupt):
            raise _Done()
        if a.strip().lower() in QUIT:
            raise _Done()
        return a

    if _yes(read("Use your current location? [y/N]: "), default=False):
        out("  Detecting location from your IP address (sent to ipinfo.io / ipapi.co)...")
        try:
            here = location_service.locate_by_ip(settings, transport)
            out(f"  Detected: {here.label()} ({here.latitude:.3f}, {here.longitude:.3f})")
            out("  Note: IP-based location is approximate and may be your ISP's city, not your exact position.")
            if _yes(read("  Use this location? [Y/n]: "), default=True):
                return here
        except AppError as exc:
            _explain(exc, out)
            out("  Falling back to manual entry.")
    while True:
        query = read("Enter location (city, optionally state/country e.g. 'Hyderabad, IN'; q to quit): ")
        try:
            place = _choose(location_service.geocode(settings, query, transport), read, out)
        except AppError as exc:
            _explain(exc, out)
            if exc.code == "weather_not_configured":
                raise _Done()
            continue
        if place:
            return place


def show(place: Place, w: ProviderWeather, out: Callable[[str], None], provider: Optional[WeatherProvider] = None,
         debug: bool = False, now: Optional[datetime] = None) -> None:
    obs_utc = w.timestamp.replace(tzinfo=timezone.utc)
    local = obs_utc.astimezone()
    age_min = ((now or datetime.now(timezone.utc)) - obs_utc).total_seconds() / 60
    out("")
    out(f"Weather for {place.label()}  ({place.latitude:.3f}, {place.longitude:.3f})")
    out(f"  Observed     : {local.strftime('%Y-%m-%d %H:%M %Z')}  ({age_min:.0f} min ago)")
    if age_min > 90:
        out("  ! This observation is old (> 90 min). OpenWeatherMap may be using a distant or slow-updating source for this spot.")
    if w.description:
        out(f"  Conditions   : {w.description.capitalize()}")
    feels = f"  (feels like {w.feels_like:.1f} C)" if w.feels_like is not None else ""
    out(f"  Temperature  : {w.temperature:.1f} C{feels}")
    out(f"  Humidity     : {w.humidity:.0f} %")
    out(f"  Rainfall     : {w.rainfall:.1f} mm in the last hour")
    if w.wind_speed is not None:
        out(f"  Wind         : {w.wind_speed:.1f} m/s")
    out("  Source       : OpenWeatherMap (live)")
    if debug and provider is not None and provider.last_payload:
        d = provider.last_payload
        out("  --- debug (compare these with what you expected) ---")
        out(f"  coordinates sent to API : {place.latitude}, {place.longitude}   <- the place we asked about")
        out(f"  place named by API      : {d.get('name')!r}, country {(d.get('sys') or {}).get('country')!r}   <- where the data really comes from")
        out(f"  coordinates API used    : {d.get('coord')}")
        out(f"  raw main / rain / dt    : {d.get('main')} / {d.get('rain')} / {d.get('dt')}")
    out("")


def run(argv: Optional[List[str]] = None, ask: Callable[[str], str] = input, out: Callable[[str], None] = print,
        transport: Optional[httpx.BaseTransport] = None, settings: Optional[Settings] = None) -> int:
    ap = argparse.ArgumentParser(description="Live weather in your terminal.")
    ap.add_argument("--location", help="place name, e.g. 'Hyderabad, IN' (skips prompts)")
    ap.add_argument("--current", action="store_true", help="use IP-based current location (skips prompts)")
    ap.add_argument("--field-id", help="persist observation for this field ID into PostgreSQL/TimescaleDB hypertable")
    ap.add_argument("--debug", action="store_true", help="also print what the API actually returned (to diagnose wrong values)")
    args = ap.parse_args(argv)
    settings = settings or Settings(_env_file=ENV_FILE)
    provider = WeatherProvider(settings, transport)

    if not settings.openweather_api_key:
        out("OPENWEATHER_API_KEY is not set.")
        out("Get a free key at https://home.openweathermap.org/api_keys and put it in backend/.env as OPENWEATHER_API_KEY=...")
        return 2

    def _maybe_persist(place: Place, w: ProviderWeather) -> None:
        if args.field_id:
            from app.database.session import get_sessionmaker
            from app.services import weather_service
            db = get_sessionmaker()()
            try:
                row, created = weather_service.store_weather(db, args.field_id, w, source="weather_cli", is_mock=False)
                out(f"  Persisted to database: weather_id={row.weather_id}, field_id={args.field_id}, new_observation={created}")
            finally:
                db.close()

    try:
        if args.location or args.current:
            if args.current:
                place = location_service.locate_by_ip(settings, transport)
                out(f"Detected (approximate, IP-based): {place.label()}")
            else:
                matches = location_service.geocode(settings, args.location, transport)
                place = matches[0]
                if len(matches) > 1:
                    out(f"Note: {len(matches)} places match '{args.location}'; using the first: {place.label()}. "
                        "Others: " + "; ".join(m.label() for m in matches[1:]) + ". Add state/country to be specific.")
            w = provider.fetch_current(place.latitude, place.longitude)
            show(place, w, out, provider, args.debug)
            _maybe_persist(place, w)
            return 0
        out("Smart Irrigation - live weather lookup")
        while True:
            place = pick_place(settings, ask, out, transport)
            try:
                w = provider.fetch_current(place.latitude, place.longitude)
                show(place, w, out, provider, args.debug)
                _maybe_persist(place, w)
            except AppError as exc:
                _explain(exc, out)
            try:
                if not _yes(ask("Look up another location? [y/N]: "), default=False):
                    return 0
            except (EOFError, KeyboardInterrupt):
                return 0
    except _Done:
        out("Bye.")
        return 0
    except AppError as exc:
        _explain(exc, out)
        return 1
    except KeyboardInterrupt:
        out("\nBye.")
        return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
