import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Base, SensorReading
from app.config import Settings

def main():
    settings = Settings()
    engine = create_engine(settings.database_url)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        total = session.execute(select(SensorReading)).scalars().count()
        print('Total readings:', total)
        rows = session.execute(select(SensorReading).limit(10)).scalars().all()
        for r in rows:
            print(r.reading_id, r.sensor_id, r.field_id, r.measurement_type, r.value, r.timestamp)

if __name__ == '__main__':
    main()
