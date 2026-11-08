import sqlite3, sys

db_path = r'C:\Users\Arpitha Medharametla\Documents\smart-irrigation\backend\irrigation.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()
sensor_id = 'SM004'
field_id = 'F005'
cur.execute('SELECT sensor_id, field_id, measurement_type, value, temperature, humidity FROM sensor_readings WHERE sensor_id=? AND field_id=?', (sensor_id, field_id))
rows = cur.fetchall()
print('Rows:', rows)
conn.close()
