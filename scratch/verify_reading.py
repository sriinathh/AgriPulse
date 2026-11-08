import sqlite3, pathlib, sys

# Paths
project_root = pathlib.Path(__file__).parents[1]
db_path = project_root / 'backend' / 'irrigation.db'
reading_id_file = project_root / 'scratch' / 'reading_id.txt'

if not db_path.is_file():
    print(f'ERROR: DB file not found at {db_path}')
    sys.exit(1)
if not reading_id_file.is_file():
    print(f'ERROR: reading_id.txt not found at {reading_id_file}')
    sys.exit(1)

with reading_id_file.open() as f:
    reading_id = f.read().strip()

conn = sqlite3.connect(str(db_path))
cur = conn.cursor()
cur.execute('SELECT reading_id, sensor_id, field_id, soil_moisture FROM sensor_readings WHERE reading_id = ?', (reading_id,))
row = cur.fetchone()
if row:
    print('Verification successful:')
    print(dict(zip(['reading_id','sensor_id','field_id','soil_moisture'], row)))
else:
    print('No reading found with ID', reading_id)
conn.close()
