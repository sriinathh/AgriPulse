import sqlite3, pathlib, sys
project_root = pathlib.Path(__file__).parents[1]
db_path = project_root / 'backend' / 'irrigation.db'
if not db_path.is_file():
    print('DB not found', db_path)
    sys.exit(1)
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print('Tables:', cur.fetchall())
# List columns of sensor_readings if exists
cur.execute("PRAGMA table_info(sensor_readings);")
print('sensor_readings schema:', cur.fetchall())
cur.execute('SELECT * FROM sensor_readings LIMIT 5;')
rows = cur.fetchall()
print('Rows sample:', rows)
conn.close()
