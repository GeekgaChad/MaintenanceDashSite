import sqlite3
import pandas as pd

DB_PATH = "/Users/msagar/SankyuWork/site_reporting_project/sample_site_reporting.db"

def get_table(table):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql(f"SELECT * FROM {table}", conn)

def time_to_hours(t):
    try:
        if pd.isnull(t):
            return None
        if isinstance(t, (pd.Timedelta, pd._libs.tslibs.timedeltas.Timedelta)):
            return t.total_seconds() / 3600
        if isinstance(t, str):
            td = pd.to_timedelta(t)
            return td.total_seconds() / 3600
        return float(t)
    except Exception:
        return None

def get_wo_permit_overview():
    with sqlite3.connect(DB_PATH) as conn:
        query = """
            SELECT 
                mr.wo_number AS maintenance_wo,
                mr.area AS maintenance_area,
                mr.status AS maintenance_status,
                mr.report_date AS maintenance_report_date,
                wpr.permit_number,
                wpr.date AS permit_date,
                wpr.work_actual_start_time,
                wpr.work_finish_time,
                wpr."(m-l)" AS work_duration,
                wpr."(n-i)" AS total_permit_time,
                wpr."(m-l)/(n-i)" AS efficiency,
                qc.id AS qc_id,
                qc.area AS qc_area,
                qc.scope_of_work,
                map.sn AS map_sn,
                map.area AS map_area,
                map.execution_date
            FROM maintenance_reports mr
            LEFT JOIN WPR wpr ON mr.wo_number = wpr.wo_number
            LEFT JOIN qc_activities qc ON mr.wo_number = qc.wo_number
            LEFT JOIN MAP map ON mr.wo_number = map."wo_＃"
        """
        df = pd.read_sql_query(query, conn)
    return df
