import sqlite3
import pandas as pd
import psycopg2
import streamlit as st

#DB_PATH = "/Users/msagar/SankyuWork/site_reporting_project/site_reporting.db"
#DB_PATH = "sample_site_reporting.db"
'''
def get_table(table):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql(f"SELECT * FROM {table}", conn)
'''

def get_connection():
    # Retrieve the Frankfurt URI from the secure Streamlit vault
    return psycopg2.connect(st.secrets["database"]["url"])

def get_table(table):
    conn = get_connection()
    try:
        # PostgreSQL uses double quotes to ensure table names are read correctly
        query = f'SELECT * FROM "{table}"'
        return pd.read_sql(query, conn)
    finally:
        conn.close()
        
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

        columns_to_drop = ['map_sn', 'map_area', 'execution_date']
        df = df.drop(columns=columns_to_drop, errors='ignore')

        df['efficiency'] = round(pd.to_numeric(df['efficiency'], errors='coerce'),2)

        df['work_actual_start_time'] = df['work_actual_start_time'].apply(format_timedelta_to_h_m)
        df['work_finish_time'] = df['work_finish_time'].apply(format_timedelta_to_h_m)
        df['work_duration'] = df['work_duration'].apply(format_timedelta_to_h_m)
        df['total_permit_time'] = df['total_permit_time'].apply(format_timedelta_to_h_m)

        
    return df

# Place this revised function in your utilities file (utils.py or before calling it)

def format_timedelta_to_h_m(td):
    """
    Converts a string duration or Timedelta to a string format like 'HH:MM'.
    
    This function handles both Timedelta objects and string representations 
    of time that may be present in the DataFrame.
    """
    if pd.isna(td):
        return None
    
    # 🚨 FIX: Convert to Timedelta if the input is a string
    if isinstance(td, str):
        try:
            td = pd.to_timedelta(td)
        except ValueError:
            # Handle cases where the string isn't a valid timedelta format
            return "Invalid Format"
    
    # Check if the result is a Timedelta object (or NaT)
    if pd.isna(td) or not isinstance(td, pd.Timedelta):
        return None
    
    # Calculation (Original Logic)
    total_seconds = td.total_seconds()
    
    # Handle negative durations if necessary (though rare for work/permit times)
    sign = "-" if total_seconds < 0 else ""
    abs_seconds = abs(total_seconds)
    
    # Calculate hours and minutes
    hours = int(abs_seconds // 3600)
    minutes = int((abs_seconds % 3600) // 60)
    
    # Return formatted string: [sign]HH:MM
    return f"{sign}{hours:02d}:{minutes:02d}"

# NOTE: No changes are needed to the application code where you call this:
# filtered['Work Duration (H:M)'] = filtered['(m-l)'].apply(format_timedelta_to_h_m)
