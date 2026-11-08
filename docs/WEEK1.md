# Week 1 — Sensor Data Ingestion & Weather API Integration

Scope: foundation only. **Not included:** ML scheduling (Weeks 3–4), PWA / notifications / Sarvam AI (Weeks 5–6).

## 1. Architecture

```
Sensor (REST)   -> POST /sensor/readings -> Router -> sensor_service -> data_cleaning_service -> DB (sensor_readings)
Field location  -> GET /weather/{field_id} -> Router -> weather_service -> OpenWeatherMap
                                                      -> normalise + data_cleaning_service -> DB (weather_data)
Both            -> GET /fields/{field_id}/combined -> as-of join (reading + latest weather at/before it)
```

Layers (nothing crosses them): `routers/` (HTTP only) → `services/` (business logic; `WeatherProvider` is the only code that calls the external API) → `models/` (SQLAlchemy). `schemas/` holds the Pydantic contracts. `errors.py` gives every failure the same shape:
`{"error": {"code": "...", "message": "...", "details": [...]}}`.

**Ingestion transport:** REST (no MQTT in Week 1; the service layer is transport-agnostic, so an MQTT subscriber can call `sensor_service.ingest_reading` later).

**Storage decision:** PostgreSQL via SQLAlchemy. `sensor_readings` and `weather_data` are converted to **TimescaleDB hypertables automatically** if the extension exists (`docker-compose.yml` ships a TimescaleDB image). If it doesn't, the app logs a warning and uses plain PostgreSQL tables. SQLite is the zero-setup default for local dev/tests. InfluxDB was not used: a second database adds local-setup friction and Timescale keeps SQL joins between sensor and weather data trivial for Week 3.

## 2. Data contracts (shared with Week 3 ML)

Sensor reading: `{"sensor_id":"SM001","field_id":"F001","timestamp":"2026-10-07T10:30:00","soil_moisture":35.6}`
(extra optional input field: `is_simulated`; `field_id` optional on input, inferred from the sensor)

Weather: `{"field_id":"F001","timestamp":"2026-10-07T10:30:00","temperature":29.0,"humidity":68,"rainfall":2.1}`
Units: soil_moisture % (volumetric), temperature °C, humidity % RH, rainfall mm in the last hour. All timestamps are **UTC**, stored naive.

## 3. Database

| Table | Columns | Notes |
|---|---|---|
| `farmers` | farmer_id (PK), name, phone, email, created_at | |
| `fields` | field_id (PK), farmer_id (FK→farmers), name, location_name, latitude, longitude, crop_type, area_hectares, created_at | crop lives on the field; lat/lon optional at registration but required for weather |
| `sensors` | sensor_id (PK), field_id (FK→fields), sensor_type, status (`active`/`inactive`), created_at | |
| `sensor_readings` | reading_id (PK), sensor_id (FK), field_id (FK), timestamp, soil_moisture, is_simulated, ingested_at | UNIQUE(sensor_id, timestamp); indexes (field_id, timestamp), (sensor_id, timestamp); hypertable on `timestamp` when Timescale is present |
| `weather_data` | weather_id (PK), field_id (FK), timestamp, temperature, humidity, rainfall, source, fetched_at | UNIQUE(field_id, timestamp); index (field_id, timestamp); hypertable when Timescale is present |

Relationships: Farmer 1—* Field 1—* Sensor 1—* SensorReading; Field 1—* WeatherData. Foreign keys are enforced (including on SQLite).
IDs for farmer/field/sensor are client-supplied or auto-generated (`FR001`, `F001`, `SM001`).

## 4. Validation & cleaning rules (`data_cleaning_service.py`)

| Input | Rule | On violation |
|---|---|---|
| soil_moisture | required, numeric (numeric strings accepted), finite, 0–100 %, rounded to 2 dp | 422, **not stored** |
| timestamp | ISO-8601; tz-aware converted to UTC; not > 5 min in the future | invalid/future → 422. **Missing → server receive time used and flagged** (`cleaning.timestamp_source = "server"`) |
| duplicate (sensor, timestamp) | | 409 |
| temperature / humidity / rainfall (provider) | −50…60 °C / 0…100 % / 0…500 mm | 502, discarded |

Nothing is imputed. No value is ever invented for a missing or failed reading.

## 5. API

Base URL `http://127.0.0.1:8000`; interactive docs at `/docs`. Errors always use the shape in §1.

| Method | URL | Purpose | Success | Errors |
|---|---|---|---|---|
| POST | `/farmers` | Register farmer `{farmer_id?, name, phone?, email?}` | 201 farmer | 409 duplicate_id, 422 invalid_request |
| GET | `/farmers`, `/farmers/{id}` | List / get (with fields) | 200 | 404 farmer_not_found |
| POST | `/fields` | Register field + crop `{field_id?, farmer_id, name, crop_type, latitude?, longitude?, location_name?, area_hectares?}` | 201 field | 404 farmer_not_found, 409, 422 (bad coords, lat without lon, empty crop) |
| GET | `/fields?farmer_id=`, `/fields/{id}` | List / get (with sensors) | 200 | 404 field_not_found |
| PUT | `/fields/{id}/crop` | Assign crop `{crop_type}` | 200 | 404, 422 |
| GET | `/fields/{id}/sensors` | Sensors of a field | 200 | 404 |
| POST | `/sensors` | Register sensor `{sensor_id?, field_id, sensor_type?, status?}` | 201 | 404 field_not_found, 409 |
| GET | `/sensors?field_id=`, `/sensors/{id}` | List / get | 200 | 404 sensor_not_found |
| PUT | `/sensors/{id}/status` | `{status: active\|inactive}` | 200 | 404, 422 |
| **POST** | **`/sensor/readings`** | Ingest `{sensor_id, field_id?, timestamp?, soil_moisture, is_simulated?}` | 201 `{status:"stored", reading, cleaning:{timestamp_source, notes}}` | 404 sensor_not_found, 422 validation_failed (details per field) / field_mismatch, 409 duplicate_reading / sensor_inactive |
| GET | `/sensor/readings?sensor_id=&field_id=&start=&end=&limit=` | Query readings, newest first | 200 | 422 |
| **GET** | **`/weather/{field_id}`** | Live fetch → normalise → store | 200 `{status:"stored"\|"already_stored", weather}` | 404 field_not_found, 422 field_location_missing, 503 weather_not_configured / weather_timeout / weather_unavailable / weather_rate_limited, 502 weather_auth_failed / weather_provider_error / weather_bad_response / weather_incomplete_data / weather_invalid_data |
| GET | `/weather/{field_id}/history?limit=` | Stored observations | 200 | 404 |
| GET | `/weather/{field_id}/latest` | Last **stored** real observation (explicit fallback when live fetch fails) | 200 | 404 no_weather_data |
| GET | `/fields/{id}/combined?limit=` | Field + sensors + readings each joined to the latest weather at/before it (`weather: null` if none known — never filled in) | 200 | 404 |
| GET | `/health` | Liveness | 200 | |

Weather mapping (OpenWeatherMap `/data/2.5/weather`, `units=metric`): `main.temp`→temperature, `main.humidity`→humidity, `dt`→timestamp, `rain.1h`→rainfall. OpenWeatherMap **omits `rain` when there is no precipitation**, so a missing `rain` object is stored as 0 mm; a lone `rain.3h` is divided by 3. Missing temperature/humidity/dt → 502, nothing stored.

## 6. Setup

Requirements: Python 3.10+ (developed on 3.12). Docker only if you want PostgreSQL/TimescaleDB.

```bash
cd backend
python -m venv ../.venv && source ../.venv/bin/activate        # Windows: ..\.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit .env
uvicorn app.main:app --reload   # http://127.0.0.1:8000/docs
```

Environment variables (`backend/.env`, never committed):

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./irrigation.db` | e.g. `postgresql+psycopg2://irrigation:irrigation@localhost:5432/irrigation` |
| `OPENWEATHER_API_KEY` | *(empty)* | Free key from openweathermap.org. Without it `/weather/*` returns 503 `weather_not_configured` |
| `OPENWEATHER_BASE_URL` | OWM current-weather URL | |
| `WEATHER_TIMEOUT_SECONDS` | 5 | |

PostgreSQL / TimescaleDB: `docker compose up -d db`, then set `DATABASE_URL` as above. Tables (and hypertables) are created on startup.

Tests: `cd backend && pytest` (SQLite in-memory). On PostgreSQL: `TEST_DATABASE_URL=postgresql+psycopg2://... pytest` (**use a throwaway database: tables are dropped**).

Demo: start the server, then `python scripts/demo_week1.py`. Simulated sensor stream: `python scripts/simulate_sensor.py --sensor-id SM001 --field-id F001 --count 12 [--inject-faults]`.

## 7. Limitations (read before presenting)

- **Sensor data is simulated.** No hardware is connected; simulated rows carry `is_simulated = true` and the simulator prints a banner. The REST contract is what real devices/gateways would call.
- **Weather depends on OpenWeatherMap** (key, quota, availability). Tomorrow.io is not implemented. Only *current* conditions are fetched (no forecast yet).
- Live OpenWeatherMap calls were **not verified in the development sandbox** (host was network-blocked); the provider code is verified only against mocked HTTP responses. Do one real call with your key (see README checklist).
- TimescaleDB hypertable conversion was **not verified** (extension unavailable in the sandbox). The fallback to plain PostgreSQL was verified.
- No authentication, no MQTT, no schema migrations (tables via `create_all`; add Alembic before schema changes in production), no weather caching beyond `/latest`.
- **ML irrigation prediction is not implemented.** The `/fields/{id}/combined` endpoint is the intended input for Week 3 feature engineering.

## 8. Terminal weather lookup (CLI)

Quick live-weather check from the terminal, no server needed. Uses the same `WeatherProvider` as `GET /weather/{field_id}` (live OpenWeatherMap) and the same `OPENWEATHER_API_KEY`.

```bash
cd backend
python scripts/weather_cli.py                         # interactive
python scripts/weather_cli.py --location "Pune, IN"   # no prompts
python scripts/weather_cli.py --current               # IP-based current location, no prompts
```

Interactive flow: **"Use your current location? [y/N]"** -> yes: detect, show the place, ask to confirm (no: manual entry) / no: **"Enter location"** -> if several places match you pick one -> weather is printed (conditions, temperature + feels-like, humidity, rainfall in last hour, wind). `q` or Ctrl-D quits.

- Place names are resolved with the OpenWeatherMap geocoding API (same key). Add the country for precision (`Hyderabad, IN`).
- "Current location" is **IP-based**: a terminal has no GPS. It is city-level accurate at best and may show your ISP's city, which is why you must confirm it. Your IP is sent to ipinfo.io (fallback ipapi.co) only if you choose this option.
- Nothing is stored in the database; this is a lookup tool.
- Failures (no key, no internet, unknown place, API error) print a short message, never a traceback.
- Verified with mocked HTTP in `tests/test_cli.py` (12 tests). **Not verified against the live services** from the development sandbox (network-blocked): run it once with your key.
