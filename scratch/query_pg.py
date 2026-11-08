import os, json, sys
from sqlalchemy import create_engine, text
url = os.getenv('DATABASE_URL') or 'postgresql+psycopg2://irrigation:irrigation@localhost:5433/irrigation'
engine = create_engine(url)
with engine.connect() as conn:
    result = conn.execute(text('SELECT reading_id, sensor_id, soil_moisture FROM sensor_readings WHERE reading_id = :rid'), {'rid': 111})
    rows = result.fetchall()
    print('Rows:', rows)
