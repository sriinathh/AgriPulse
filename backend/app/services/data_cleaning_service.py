"""Reusable validation / cleaning rules. Pure functions: no database, no HTTP.

Rules (documented in README / docs/WEEK1.md):
  soil_moisture  required (for moisture sensors), numeric, finite, 0..100 (% volumetric water content)
  timestamp      optional; ISO-8601. Missing -> server receive time is used and flagged.
                 Timezone-aware values are converted to UTC. Not more than N seconds in the future.
  temperature    -50..60 deg C
  humidity       0..100 %
  rainfall       0..500 mm/h
  soil_ph        0..14
  water_level    0..10000 (mm or litres depending on unit)
  flow_rate      0..1000 (L/min)

Nothing is ever imputed or invented: a bad value rejects the record with a list of issues.
Interpolation is not implemented (would be optional, documented, and marked if added later).
"""
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

SOIL_MOISTURE_MIN, SOIL_MOISTURE_MAX = 0.0, 100.0
TEMPERATURE_MIN, TEMPERATURE_MAX = -50.0, 60.0
HUMIDITY_MIN, HUMIDITY_MAX = 0.0, 100.0
RAINFALL_MIN, RAINFALL_MAX = 0.0, 500.0

MEASUREMENT_RANGES: Dict[str, Tuple[float, float, str]] = {
    "soil_moisture": (SOIL_MOISTURE_MIN, SOIL_MOISTURE_MAX, "%"),
    "temperature": (TEMPERATURE_MIN, TEMPERATURE_MAX, " C"),
    "humidity": (HUMIDITY_MIN, HUMIDITY_MAX, "%"),
    "rainfall": (RAINFALL_MIN, RAINFALL_MAX, " mm"),
    "soil_ph": (0.0, 14.0, ""),
    "water_level": (0.0, 10000.0, ""),
    "flow_rate": (0.0, 1000.0, ""),
}

DEFAULT_UNITS = {
    "soil_moisture": "%",
    "temperature": "C",
    "humidity": "%",
    "rainfall": "mm",
    "soil_ph": "pH",
    "water_level": "mm",
    "flow_rate": "L/min",
}

SUPPORTED_MEASUREMENTS = tuple(MEASUREMENT_RANGES.keys())


@dataclass
class ValidationIssue:
    field: str
    code: str
    message: str

    def as_dict(self) -> dict:
        return {"field": self.field, "code": self.code, "message": self.message}


class DataValidationError(Exception):
    def __init__(self, issues: List[ValidationIssue]):
        super().__init__("; ".join(i.message for i in issues))
        self.issues = issues


@dataclass
class CleanedReading:
    timestamp: datetime  # naive UTC
    soil_moisture: Optional[float]
    timestamp_source: str  # "client" | "server"
    notes: List[str] = field(default_factory=list)
    extras: Dict[str, float] = field(default_factory=dict)
    measurement_type: str = "soil_moisture"
    value: Optional[float] = None
    unit: Optional[str] = None
    quality_flags: List[str] = field(default_factory=list)


def _to_number(name: str, raw: Any) -> float:
    """Return a finite float or raise ValueError(code, message)."""
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        raise _Bad("missing_value", f"{name} is missing.")
    if isinstance(raw, bool):
        raise _Bad("not_numeric", f"{name} must be a number, got a boolean.")
    try:
        value = float(raw.strip() if isinstance(raw, str) else raw)
    except (TypeError, ValueError):
        raise _Bad("not_numeric", f"{name} must be a number, got {raw!r}.")
    if not math.isfinite(value):
        raise _Bad("not_finite", f"{name} must be a finite number.")
    return value


class _Bad(Exception):
    def __init__(self, code: str, message: str):
        self.code, self.message = code, message


def _check_range(name: str, value: float, lo: float, hi: float, unit: str) -> None:
    if not lo <= value <= hi:
        raise _Bad("out_of_range", f"{name} {value} is outside the valid range {lo}-{hi}{unit}.")


def parse_timestamp(raw: Any, now: datetime, future_tolerance_seconds: int) -> "tuple[datetime, bool]":
    """Return (naive UTC datetime, was_timezone_aware)."""
    if not isinstance(raw, str):
        raise _Bad("invalid_timestamp", "timestamp must be an ISO-8601 string.")
    try:
        parsed = datetime.fromisoformat(raw.strip())
    except ValueError:
        raise _Bad("invalid_timestamp", f"timestamp {raw!r} is not valid ISO-8601.")
    aware = parsed.tzinfo is not None
    if aware:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    if parsed > now + timedelta(seconds=future_tolerance_seconds):
        raise _Bad("future_timestamp", f"timestamp {raw} is in the future.")
    return parsed, aware


def clean_numeric_field(name: str, raw: Any) -> float:
    if name not in MEASUREMENT_RANGES:
        raise DataValidationError([ValidationIssue(name, "unsupported_measurement", f"Unsupported measurement '{name}'.")])
    lo, hi, unit = MEASUREMENT_RANGES[name]
    try:
        value = _to_number(name, raw)
        _check_range(name, value, lo, hi, unit)
        return round(value, 2)
    except _Bad as e:
        raise DataValidationError([ValidationIssue(name, e.code, e.message)])


def _clean_optional(name: str, raw: Any, issues: List[ValidationIssue], notes: List[str]) -> Optional[float]:
    if raw is None:
        return None
    if isinstance(raw, str) and not raw.strip():
        return None
    lo, hi, unit = MEASUREMENT_RANGES[name]
    try:
        value = _to_number(name, raw)
        _check_range(name, value, lo, hi, unit)
        rounded = round(value, 2)
        if isinstance(raw, str):
            notes.append(f"{name} converted from string to number")
        if rounded != value:
            notes.append(f"{name} rounded to 2 decimals")
        return rounded
    except _Bad as e:
        issues.append(ValidationIssue(name, e.code, e.message))
        return None


def clean_sensor_reading(
    soil_moisture: Any,
    timestamp: Any = None,
    now: Optional[datetime] = None,
    future_tolerance_seconds: int = 300,
    extras: Optional[Dict[str, Any]] = None,
    measurement_type: Optional[str] = None,
    value: Any = None,
    require_soil_moisture: bool = True,
) -> CleanedReading:
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    issues: List[ValidationIssue] = []
    notes: List[str] = []
    moisture: Optional[float] = None
    ts: Optional[datetime] = None
    source = "client"
    extras = extras or {}
    mtype = (measurement_type or "soil_moisture").strip() or "soil_moisture"
    if mtype not in MEASUREMENT_RANGES:
        issues.append(ValidationIssue("measurement_type", "unsupported_measurement", f"Unsupported measurement '{mtype}'."))

    if soil_moisture is None or (isinstance(soil_moisture, str) and not soil_moisture.strip()):
        if require_soil_moisture and mtype == "soil_moisture" and value is None:
            issues.append(ValidationIssue("soil_moisture", "missing_value", "soil_moisture is missing."))
        elif soil_moisture is not None and isinstance(soil_moisture, str) and not soil_moisture.strip() and require_soil_moisture:
            issues.append(ValidationIssue("soil_moisture", "missing_value", "soil_moisture is missing."))
    else:
        try:
            moisture = _to_number("soil_moisture", soil_moisture)
            _check_range("soil_moisture", moisture, SOIL_MOISTURE_MIN, SOIL_MOISTURE_MAX, "%")
        except _Bad as e:
            issues.append(ValidationIssue("soil_moisture", e.code, e.message))

    cleaned_extras: Dict[str, float] = {}
    for name, raw in extras.items():
        if name not in MEASUREMENT_RANGES:
            issues.append(ValidationIssue(name, "unsupported_measurement", f"Unsupported measurement '{name}'."))
            continue
        got = _clean_optional(name, raw, issues, notes)
        if got is not None:
            cleaned_extras[name] = got

    primary_value = moisture
    if value is not None and not (isinstance(value, str) and not value.strip()):
        if mtype in MEASUREMENT_RANGES:
            got = _clean_optional(mtype, value, issues, notes)
            if got is not None:
                primary_value = got if mtype == "soil_moisture" else primary_value
                cleaned_extras.setdefault(mtype, got)
                if mtype == "soil_moisture":
                    moisture = got

    if moisture is None and mtype != "soil_moisture" and mtype in cleaned_extras:
        pass  # other measurement only — soil_moisture stays missing (not invented)
    elif moisture is None and require_soil_moisture and mtype == "soil_moisture" and not any(i.field == "soil_moisture" for i in issues):
        issues.append(ValidationIssue("soil_moisture", "missing_value", "soil_moisture is missing."))

    if timestamp is None or (isinstance(timestamp, str) and not timestamp.strip()):
        ts, source = now, "server"
        notes.append("timestamp missing: server receive time (UTC) was used")
    else:
        try:
            ts, aware = parse_timestamp(timestamp, now, future_tolerance_seconds)
            if aware:
                notes.append("timezone-aware timestamp converted to UTC")
        except _Bad as e:
            issues.append(ValidationIssue("timestamp", e.code, e.message))

    if issues:
        raise DataValidationError(issues)

    rounded = round(moisture, 2) if moisture is not None else None
    if moisture is not None and rounded != moisture:
        notes.append("soil_moisture rounded to 2 decimals")
    if isinstance(soil_moisture, str) and moisture is not None:
        notes.append("soil_moisture converted from string to number")
    stored_value = rounded if mtype == "soil_moisture" else cleaned_extras.get(mtype, rounded)
    return CleanedReading(
        timestamp=ts.replace(microsecond=0) if source == "server" else ts,
        soil_moisture=rounded,
        timestamp_source=source,
        notes=notes,
        extras=cleaned_extras,
        measurement_type=mtype,
        value=stored_value,
        unit=DEFAULT_UNITS.get(mtype),
    )


@dataclass
class CleanedWeather:
    temperature: float
    humidity: float
    rainfall: float


def clean_weather(temperature: Any, humidity: Any, rainfall: Any) -> CleanedWeather:
    """Validate already-extracted provider values. Raises DataValidationError if implausible/missing."""
    issues: List[ValidationIssue] = []
    out = {}
    for name, raw, lo, hi, unit in (
        ("temperature", temperature, TEMPERATURE_MIN, TEMPERATURE_MAX, " C"),
        ("humidity", humidity, HUMIDITY_MIN, HUMIDITY_MAX, "%"),
        ("rainfall", rainfall, RAINFALL_MIN, RAINFALL_MAX, " mm"),
    ):
        try:
            value = _to_number(name, raw)
            _check_range(name, value, lo, hi, unit)
            out[name] = round(value, 2)
        except _Bad as e:
            issues.append(ValidationIssue(name, e.code, e.message))
    if issues:
        raise DataValidationError(issues)
    return CleanedWeather(**out)
