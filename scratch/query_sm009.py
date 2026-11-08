import sqlite3, os, json, sys
db_path = os.path.abspath('backend/irrigation.db')
print('DB path', db_path)
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute('SELECT reading_id, sensor_id, field_id, measurement_type, value FROM sensor_readings WHERE sensor_id = ?', ('SM009',))
rows = c.fetchall()
print('Rows count', len(rows))
for r in rows:
    print(r)
conn.close()
