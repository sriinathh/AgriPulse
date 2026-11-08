import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.init_db import init_db
from app.database.session import get_engine
from app.errors import register_error_handlers
from app.routers import crops, data_quality, demo, farmers, fields, recommendations, sensors, system, weather, prediction, auth, farmer_dashboard, irrigation_schedules
from app.services.mqtt_service import start_mqtt_background

log = logging.getLogger("irrigation")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# Load settings once
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events.

    - Initialise database engine (handle fallback for tests)
    - Initialise TimescaleDB hypertables
    - Start background MQTT service
    """
    # Initialise the database engine – fail fast in development/production, allow SQLite fallback only for tests.
    try:
        engine = get_engine()
    except RuntimeError as e:
        if settings.app_env.lower() != "test" and not getattr(settings, "allow_sqlite_fallback", False):
            raise e
        log.warning("Database engine initialization fell back to in‑memory SQLite for testing: %s", e)
        from sqlalchemy import create_engine
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    # Initialise tables / hypertables
    try:
        hypertables = init_db(engine)
        log.info("Database ready (TimescaleDB hypertables: %s)", hypertables)
    except RuntimeError as e:
        log.warning("Database initialization skipped: %s", e)

    # Start background MQTT service
    start_mqtt_background(settings)

    yield

# Create FastAPI app with loaded settings and lifespan
app = FastAPI(
    title="Smart Irrigation - Milestone 1",
    version=settings.app_version,
    lifespan=lifespan,
)

# Register global error handlers
register_error_handlers(app)

# Configure CORS middleware using settings.cors_origin_list (supports legacy env var via validator)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers in deterministic order
app.include_router(system.router)
app.include_router(farmers.router)
app.include_router(fields.router)
app.include_router(crops.router)
app.include_router(sensors.router)
app.include_router(weather.router)
app.include_router(data_quality.router)
app.include_router(demo.router)
app.include_router(recommendations.router)
app.include_router(auth.router)
app.include_router(farmer_dashboard.router)
app.include_router(irrigation_schedules.router)
app.include_router(prediction.router)
