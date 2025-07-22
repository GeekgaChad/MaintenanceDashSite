
import sqlite3

DB_PATH = "/Users/msagar/SankyuWork/site_reporting_project/site_reporting.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("All tables in database:")
tables = [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")]
for table in tables:
    print(f"\n=== {table.upper()} ===")
    schema = cursor.execute(f"PRAGMA table_info({table})").fetchall()
    for col in schema:
        print(col)
conn.close()

'''
import sqlite3
import pandas as pd

conn = sqlite3.connect("site_reporting.db")

df = pd.read_sql_query("""
SELECT 
    wpr.wo_number,
    wpr.permit_number,
    wpr.date AS permit_date,
    wpr.work_actual_start_time,
    wpr.work_finish_time,
    wpr."(m-l)" AS work_duration,
    wpr."(n-i)" AS total_permit_time,
    wpr."(m-l)/(n-i)" AS efficiency,
    mr.area AS maintenance_area,
    qc.area AS qc_area,
    map.area AS map_area
FROM wpr
LEFT JOIN maintenance_reports mr ON wpr.wo_number = mr.wo_number
LEFT JOIN qc_activities qc ON wpr.wo_number = qc.wo_number
LEFT JOIN map ON wpr.wo_number = map."wo_＃"
""", conn)

print(df.head())
'''