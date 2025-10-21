import sqlite3


# scripts/migrations/001_create_meta_and_views.py
import sqlite3

DB_PATH = "/Users/msagar/SankyuWork/site_reporting_project/site_reporting.db"

ddl = """
BEGIN;

-- New meta table: keeps supervisor/department/shift/done_by by WO
CREATE TABLE IF NOT EXISTS work_order_meta (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  wo_number   TEXT NOT NULL UNIQUE,
  supervisor  TEXT,
  department  TEXT,       -- e.g., Static/Rotating/…
  shift       TEXT,       -- Day/Night
  done_by     TEXT,       -- default can be receiver_name
  created_at  TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_meta_wo ON work_order_meta(wo_number);

-- KPI view for durations in minutes from WPR
DROP VIEW IF EXISTS vw_wpr_durations;
CREATE VIEW vw_wpr_durations AS
SELECT
  permit_number,
  wo_number,
  "plant/rtm_no" AS plant_rtm_no,
  crew_members,
  date,
  time_of_requesting_permit,
  time_of_issuer_starting_swp_preperation,
  time_of_permit_issuance,
  work_actual_start_time,
  work_finish_time,
  swp_closing_time,
  CASE WHEN work_actual_start_time IS NOT NULL AND work_finish_time IS NOT NULL
       THEN (strftime('%s', work_finish_time) - strftime('%s', work_actual_start_time))/60.0
       ELSE NULL END AS minutes_exec,
  CASE WHEN time_of_requesting_permit IS NOT NULL AND swp_closing_time IS NOT NULL
       THEN (strftime('%s', swp_closing_time) - strftime('%s', time_of_requesting_permit))/60.0
       ELSE NULL END AS minutes_end_to_end
FROM WPR;

COMMIT;
"""

with sqlite3.connect(DB_PATH) as con:
    con.executescript(ddl)

print("✅ work_order_meta table and vw_wpr_durations view are ready.")

# quick smoke tests
with sqlite3.connect(DB_PATH) as con:
    cur = con.cursor()
    cur.execute("PRAGMA table_info(work_order_meta)")
    print("work_order_meta columns:", cur.fetchall())
    cur.execute("SELECT * FROM vw_wpr_durations LIMIT 3")
    print("vw_wpr_durations sample:", cur.fetchall())
