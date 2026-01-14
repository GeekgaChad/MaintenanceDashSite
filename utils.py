import pandas as pd
import psycopg2
import streamlit as st
import os

def get_connection():
    """Retrieve the Frankfurt URI from the secure Streamlit vault."""
    return psycopg2.connect(st.secrets["database"]["url"])

def get_table(table):
    """Fetch an entire table from the Cloud PostgreSQL vault."""
    conn = get_connection()
    try:
        # PostgreSQL uses double quotes to ensure table names are read correctly
        query = f'SELECT * FROM "{table}"'
        return pd.read_sql(query, conn)
    finally:
        conn.close()

def get_wo_permit_overview():
    """Unified view for the Overview Dashboard using Cloud PostgreSQL."""
    conn = get_connection()
    try:
        # 🚨 FIX: Using the Full-Width Hash "＃" as identified by the Postgres HINT
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
                qc.scope_of_work
            FROM "maintenance_reports" mr
            LEFT JOIN "WPR" wpr ON mr.wo_number = wpr.wo_number
            LEFT JOIN "qc_activities" qc ON mr.wo_number = qc.wo_number
            LEFT JOIN "MAP" m ON mr.wo_number = m."wo_＃"   -- 🚨 SWAPPED TO FULL-WIDTH ＃
        """
        df = pd.read_sql_query(query, conn)
        
        # Ensure efficiency is numeric before rounding
        df['efficiency'] = pd.to_numeric(df['efficiency'], errors='coerce')
        df['efficiency'] = df['efficiency'].round(2)
        
        # Apply visual formatting
        time_cols = ['work_actual_start_time', 'work_finish_time', 'work_duration', 'total_permit_time']
        for col in time_cols:
            if col in df.columns:
                df[col] = df[col].apply(format_timedelta_to_h_m)
            
        return df
    finally:
        conn.close()

def insert_wpr(conn, payload):
    """Professional Write logic for Work Permits."""
    cols = [
        "receiver_name","position","date","crew_members","wo_number","wo_description",
        "permit_number","plant/rtm_no","time_of_requesting_permit",
        "time_of_issuer_starting_swp_preperation","time_of_permit_issuance",
        "work_actual_start_time","work_finish_time","swp_closing_time",
        "remarks","(m-l)","(n-i)","(m-l)/(n-i)"
    ]
    # PostgreSQL uses %s placeholders
    placeholders = ",".join(["%s"] * len(cols))
    query = f'INSERT INTO "WPR" ({",".join([f'"{c}"' for c in cols])}) VALUES ({placeholders})'
    
    with conn.cursor() as cur:
        cur.execute(query, [payload.get(c) for c in cols])

def insert_dmr(conn, payload):
    """Professional Write logic for Maintenance Reports."""
    cols = [
        "area","unit","tag_number","wo_number","observation","recommendation",
        "date","status","reason_remark","root_cause","section","report_date"
    ]
    placeholders = ",".join(["%s"] * len(cols))
    query = f'INSERT INTO "maintenance_reports" ({",".join(cols)}) VALUES ({placeholders})'
    
    with conn.cursor() as cur:
        cur.execute(query, [payload.get(c) for c in cols])

def time_to_hours(t):
    """Utility to convert time strings/timedeltas to numeric hours."""
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

def format_timedelta_to_h_m(td):
    """Formats durations for visual interpretability."""
    if pd.isna(td):
        return None
    if isinstance(td, str):
        try:
            td = pd.to_timedelta(td)
        except ValueError:
            return "Invalid Format"
    if not isinstance(td, pd.Timedelta):
        return None
    
    total_seconds = td.total_seconds()
    sign = "-" if total_seconds < 0 else ""
    abs_seconds = abs(total_seconds)
    hours = int(abs_seconds // 3600)
    minutes = int((abs_seconds % 3600) // 60)
    return f"{sign}{hours:02d}:{minutes:02d}"
