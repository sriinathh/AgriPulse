import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.init_db import init_db
from app.database.session import build_engine, get_db
from app.main import app


@pytest.fixture()
def engine():
    # In-memory SQLite by default; set TEST_DATABASE_URL to run the same tests on PostgreSQL.
    import os
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        eng = build_engine(url)
        Base.metadata.drop_all(eng)
    else:
        eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        from sqlalchemy import event

        @event.listens_for(eng, "connect")
        def _fk(dbapi_conn, _):
            dbapi_conn.execute("PRAGMA foreign_keys=ON")
    init_db(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def db(engine):
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    yield session
    session.close()


@pytest.fixture()
def client(engine):
    maker = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def _get_db():
        s = maker()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _get_db
    # Not using `with TestClient(...)`: the lifespan would init the real configured DB.
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded(client):
    """Farmer Harini -> Field F001 (Rice, with coordinates) -> Sensor SM001."""
    client.post("/farmers", json={"farmer_id": "FR001", "name": "Harini", "phone": "9999900000"})
    client.post("/fields", json={
        "field_id": "F001", "farmer_id": "FR001", "name": "North Paddy",
        "location_name": "Hyderabad, Telangana", "latitude": 17.385, "longitude": 78.4867,
        "crop_type": "rice", "area_hectares": 1.5,
    })
    client.post("/sensors", json={"sensor_id": "SM001", "field_id": "F001"})
    return {"farmer": "FR001", "field": "F001", "sensor": "SM001"}
