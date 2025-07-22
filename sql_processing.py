import pandas as pd
import sqlite3

# --- 1. Reset Tables with Clean Schema ---

DB_PATH = "/Users/msagar/SankyuWork/site_reporting_project/site_reporting.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Drop if exist
c.execute("DROP TABLE IF EXISTS maintenance_reports;")
c.execute("DROP TABLE IF EXISTS daily_safety_patrol;")
c.execute("DROP TABLE IF EXISTS qc_activities;")

# Create
c.execute("""
CREATE TABLE maintenance_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area TEXT,
    unit TEXT,
    tag_number TEXT,
    wo_number TEXT,
    observation TEXT,
    recommendation TEXT,
    date TEXT,
    status TEXT,
    reason_remark TEXT,
    root_cause TEXT,
    section TEXT,
    report_date TEXT
)
""")
c.execute("""
CREATE TABLE daily_safety_patrol (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area TEXT,
    rtm TEXT,
    permit_no TEXT,
    work_description TEXT,
    observation TEXT,
    action TEXT,
    type TEXT,
    group_ TEXT,
    status TEXT,
    report_by TEXT,
    section TEXT,
    report_date TEXT
)
""")
c.execute("""
CREATE TABLE qc_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sn TEXT,
    area TEXT,
    wo_number TEXT,
    eqp_number TEXT,
    scope_of_work TEXT,
    work_procedure_use TEXT,
    observation_findings TEXT,
    action TEXT,
    status TEXT,
    reported_by TEXT,
    remarks TEXT,
    section TEXT,
    report_date TEXT
)
""")
conn.commit()
conn.close()
print("✅ Reset and created new tables.")


# --- 2. Load and Clean DataFrames ---

# Paths to your cleaned CSVs
maint_path = "site_reporting_project/cleaned_data/maintenance_cleaned.csv"
patrol_path = "site_reporting_project/cleaned_data/patrol_cleaned.csv"
qc_path = "site_reporting_project/cleaned_data/qc_cleaned.csv"

# Maintenance Reports
maint_rename = {
    '#': None,  # drop
    'Area': 'area',
    'Unit': 'unit',
    'Tag #': 'tag_number',
    'W/O#': 'wo_number',
    'Observation': 'observation',
    'Recommendation': 'recommendation',
    'Date ': 'date',  # Watch trailing space!
    'Status ': 'status',
    'Remining / Reason / Remark': 'reason_remark',
    'Root Cause': 'root_cause',
    'section': 'section',
    'report_date': 'report_date'
}
maint_cols = [k for k, v in maint_rename.items() if v is not None]

df_maint = pd.read_csv(maint_path)
df_maint = df_maint[[col for col in maint_cols if col in df_maint.columns]]
df_maint = df_maint.rename(columns={k: v for k, v in maint_rename.items() if v})

# Daily Safety Patrol
patrol_rename = {
    'area': 'area',
    'rtm': 'rtm',
    'permit_no': 'permit_no',
    'work_description': 'work_description',
    'observation': 'observation',
    'action': 'action',
    'type': 'type',
    'group': 'group_',  # Rename to group_
    'status': 'status',
    'report_by': 'report_by',
    'section': 'section',
    'report_date': 'report_date',
    'nan': None,  # drop if present
}
patrol_cols = [k for k, v in patrol_rename.items() if v is not None]
df_patrol = pd.read_csv(patrol_path)
if 'nan' in df_patrol.columns:
    df_patrol = df_patrol.drop(columns=['nan'])
df_patrol = df_patrol[[col for col in patrol_cols if col in df_patrol.columns]]
df_patrol = df_patrol.rename(columns={k: v for k, v in patrol_rename.items() if v})

# QC Activities
qc_rename = {
    's/n': 'sn',
    'area': 'area',
    'wo#': 'wo_number',
    'eqp#': 'eqp_number',
    'scope_of_work': 'scope_of_work',
    'work_procedure_use': 'work_procedure_use',
    'observations/findings': 'observation_findings',
    'action': 'action',
    'status': 'status',
    'reported_by': 'reported_by',
    'remarks': 'remarks',
    'section': 'section',
    'report_date': 'report_date'
}
qc_cols = [k for k, v in qc_rename.items() if v is not None]
df_qc = pd.read_csv(qc_path)
df_qc = df_qc[[col for col in qc_cols if col in df_qc.columns]]
df_qc = df_qc.rename(columns=qc_rename)

print("Maintenance columns:", df_maint.columns.tolist())
print("Patrol columns:", df_patrol.columns.tolist())
print("QC columns:", df_qc.columns.tolist())

# --- 3. Save to SQLite ---

conn = sqlite3.connect(DB_PATH)
df_maint.to_sql('maintenance_reports', conn, if_exists='append', index=False)
df_patrol.to_sql('daily_safety_patrol', conn, if_exists='append', index=False)
df_qc.to_sql('qc_activities', conn, if_exists='append', index=False)
conn.close()

print("✅ All cleaned data loaded into SQLite!")

# (Optional) Print record counts for sanity check
print("Maintenance count:", len(df_maint))
print("Patrol count:", len(df_patrol))
print("QC count:", len(df_qc))


