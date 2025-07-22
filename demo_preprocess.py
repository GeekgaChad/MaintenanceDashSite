import pandas as pd
import os

import pandas as pd
import os
import numpy as np
import re

# Get base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

RAW_DATA_PATH = os.path.join(PROJECT_ROOT, "raw_data")
CLEANED_DATA_PATH = os.path.join(PROJECT_ROOT, "cleaned_data")


if not os.path.exists(CLEANED_DATA_PATH):
    os.makedirs(CLEANED_DATA_PATH)


# Load Work Permit Tracking Register
wpr_file = os.path.join(RAW_DATA_PATH, "Work_Permit_Tracking_Register_2025.xlsx")
df_wpr = pd.read_excel(wpr_file)

# Load MAP Activity Overview
map_file = os.path.join(RAW_DATA_PATH, "MAP_Activity_Overview.xlsx")
df_map = pd.read_excel(map_file)

# Load WAVE Daily Activity Report
wave_file = os.path.join(RAW_DATA_PATH, "WAVE-I_Daily_Activity_Report_30_June_2025.xlsx")
#df_wave = pd.read_excel(wave_file)


print("WPR Columns:", df_wpr.columns.tolist())
print("MAP Columns:", df_map.columns.tolist())
#print("WAVE Columns:", df_wave.columns.tolist())
print(df_wpr.head(3))
print(df_map.head(3))
#print(df_wave.head(3))
#print(df_wave.head(4))
#print(df_wave.head(5))

# cleaned_data 

print("[INFO] Loading Excel files with correct headers...")

df_wpr = pd.read_excel(wpr_file, header=1)
df_map = pd.read_excel(map_file, header=1)
#df_wave = pd.read_excel(wave_file, header=3)

print("[INFO] Loaded!")
print("WPR Columns:", df_wpr.columns.tolist())
print("MAP Columns:", df_map.columns.tolist())
#print("WAVE Columns:", df_wave.columns.tolist())


def clean_columns(df):
    df.columns = [c.strip().lower().replace(" ", "_").replace("#","number") for c in df.columns]
    return df

df_wpr = clean_columns(df_wpr)
df_map = clean_columns(df_map)
##df_wave = clean_columns(df_wave)

print("WPR Cleaned Columns:", df_wpr.columns.tolist())
print("MAP Cleaned Columns:", df_map.columns.tolist())
#print("WAVE Cleaned Columns:", df_wave.columns.tolist())



print(df_map.isnull().sum())
#print(df_wave.isnull().sum())
print(df_wpr.isnull().sum())


# Replace placeholder 'N/A' with real NaNs
for df in [df_map, df_wpr]:
    df.replace('N/A', pd.NA, inplace=True)

# Drop all columns that are completely empty
for name, df in [('MAP', df_map), ('WPR', df_wpr)]:
    before_cols = df.columns.tolist()
    df.dropna(axis=1, how='all', inplace=True)
    after_cols = df.columns.tolist()
    print(f"[INFO] {name} Columns before drop: {before_cols}")
    print(f"[INFO] {name} Columns after drop: {after_cols}")

# Fill remaining NaNs with 'N/A' for reporting
for df in [df_map, df_wpr]:
    df.fillna('N/A', inplace=True)



print(df_map['unnamed:_11'].value_counts(dropna=False))


if 'unnamed:_11' in df_map.columns and 'note/highlight' in df_map.columns:
    print("[INFO] Fixing split Note/Highlight in MAP...")
    df_map['unnamed:_11'] = df_map['unnamed:_11'].replace('N/A', np.nan)
    df_map['note/highlight'] = df_map.apply(
        lambda row: (
            row['note/highlight'] + " " + row['unnamed:_11']
            if pd.notnull(row['unnamed:_11'])
            else row['note/highlight']
        ),
        axis=1
    )
    df_map.drop(columns=['unnamed:_11'], inplace=True)

print("[INFO] MAP Note/Highlight sample:", df_map['note/highlight'].dropna().sample(5))

# Inspect the target row to verify merge worked
print("[INFO] Checking merged Note/Highlight for SN=W1-2400065:")
print(df_map[df_map['sn'] == 'W1-2400065'][['sn', 'note/highlight']])
df_map.loc[df_map['sn'] == 'W1-2400065', 'note/highlight'] = df_map.loc[df_map['sn'] == 'W1-2400065', 'note/highlight'].str.replace('N/A ', '', regex=False)
print(df_map[df_map['sn'] == 'W1-2400065'][['sn', 'note/highlight']])



from datetime import datetime

def standardize_date_column(df, column):
    if column in df.columns:
        print(f"[INFO] Parsing date column: {column}")
        df[column] = pd.to_datetime(df[column], errors='coerce', infer_datetime_format=True).dt.strftime('%Y-%m-%d')
        df[column] = df[column].fillna('N/A')


standardize_date_column(df_wpr, 'date')
standardize_date_column(df_map, 'execution_date')
#standardize_date_column(df_wave, 'date')


def standardize_text_column(df, column):
    if column in df.columns:
        print(f"[INFO] Standardizing text column: {column}")
        df[column] = df[column].str.strip().str.upper().fillna('N/A')
        df[column] = df[column].fillna('N/A')

standardize_text_column(df_wpr, 'remarks')
#standardize_text_column(df_wave, 'status')



for df in [df_wpr, df_map]:
    df.fillna('N/A', inplace=True)



import sqlite3
# EXPORT TO CSV
df_wpr.to_csv(os.path.join(CLEANED_DATA_PATH, 'wpr_cleaned.csv'), index=False)
df_map.to_csv(os.path.join(CLEANED_DATA_PATH, 'map_cleaned.csv'), index=False)
#df_wave.to_csv(os.path.join(CLEANED_DATA_PATH, 'wave_cleaned.csv'), index=False)

# WRITE TO SQLITE
conn = sqlite3.connect(os.path.join(PROJECT_ROOT, 'site_reporting.db'))
df_wpr.to_sql('WPR', conn, if_exists='replace', index=False)
df_map.to_sql('MAP', conn, if_exists='replace', index=False)
#df_wave.to_sql('WAVE', conn, if_exists='replace', index=False)
conn.close()

print("[INFO] All cleaning complete, CSV and DB outputs ready!")

# WAVE Daily Activity Report Processing


MAINTENANCE_SECTIONS = [
    "Rotating", "Static", "Electrical", "Instrument",
    "Scaffolding", "Boom Truck", "Crane", "Insulation"
]
PATROL_SECTIONS = ["HSE Activities", "Daily Safety Patrol"]
QC_SECTIONS     = ["QC Activities"]

ALL_SECTION_LABELS = MAINTENANCE_SECTIONS + PATROL_SECTIONS + QC_SECTIONS

# # 1) pick the sheet you want to test
xls = pd.ExcelFile(wave_file)
# print("[INFO] Available sheets:", xls.sheet_names)


def wave_file_processing(wave_file=wave_file,maintenance_sections=MAINTENANCE_SECTIONS, patrol_sections=PATROL_SECTIONS, qc_sections=QC_SECTIONS):
    print("[INFO] Processing WAVE file:", wave_file)
    ALL_SECTION_LABELS = maintenance_sections + patrol_sections + qc_sections
    xls = pd.ExcelFile(wave_file)
    print("[INFO] Available sheets:", xls.sheet_names)

    all_maintenance = []
    all_patrol = []
    all_qc = []

    for sheet_name in xls.sheet_names:
        print(f"\n[INFO] → Parsing sheet: {sheet_name}")

        raw = pd.read_excel(wave_file, sheet_name=sheet_name, header=None)

        # extract report_date from the sheet name
        m = re.search(r"\((.*?)\)", sheet_name)
        report_date = pd.to_datetime(m.group(1), errors="coerce").strftime("%Y-%m-%d") if m else "N/A"

        # Maintenance parsing (your current logic)
        maintenance_header_idx = None
        for i, row in raw.iterrows():
            header = row.astype(str).str.lower().tolist()
            if "area" in header and "unit" in header and ("tag #" in header or "tag_number" in header or "wo #" in header):
                maintenance_header_idx = i
                break

        maintenance_parts = []
        if maintenance_header_idx is not None:
            header_row = raw.iloc[maintenance_header_idx].tolist()
            section_indices = {}
            for idx, cell in raw[0].items():
                if isinstance(cell, str) and cell.strip() in MAINTENANCE_SECTIONS:
                    section_indices[cell.strip()] = idx
            ordered_sections = sorted(section_indices.items(), key=lambda x: x[1])
            for i, (section, start_idx) in enumerate(ordered_sections):
                next_start = raw.shape[0]
                if i+1 < len(ordered_sections):
                    next_start = ordered_sections[i+1][1]
                data_block = raw.iloc[start_idx+1:next_start].reset_index(drop=True)
                data_block.columns = header_row
                data_block.dropna(how="all", inplace=True)
                if not data_block.empty:
                    data_block["section"] = section
                    data_block["report_date"] = report_date
                    maintenance_parts.append(data_block)
        if maintenance_parts:
            all_maintenance.append(pd.concat(maintenance_parts, ignore_index=True))

        # Section parsing for Patrol and QC
        section_starts = {}
        for idx, cell in raw[0].items():
            if isinstance(cell, str):
                low = cell.lower()
                for label in ALL_SECTION_LABELS:
                    if label.lower() in low:
                        section_starts[label] = idx
        ordered = sorted(section_starts.items(), key=lambda x: x[1])

        patrol_parts = []
        qc_parts = []
        for i, (sec, start_row) in enumerate(ordered):
            end_row = raw.shape[0]
            if i + 1 < len(ordered):
                end_row = ordered[i+1][1]
            block = raw.iloc[start_row+1:end_row].copy()
            block.dropna(how="all", inplace=True)
            if block.empty:
                continue

            if sec in PATROL_SECTIONS:
                mask = block.apply(lambda r: 
                    r.astype(str).str.contains("permit no", case=False, na=False).any() and 
                    r.astype(str).str.contains("rtm", case=False, na=False).any(), axis=1)
            elif sec in QC_SECTIONS:
                mask = block.apply(lambda r: 
                    r.astype(str).str.contains(r"s/n", case=False, na=False).any(), axis=1)
            else:
                continue
            if not mask.any():
                continue

            hdr_idx = mask[mask].index[0]
            block = block.loc[hdr_idx:]
            block.columns = block.iloc[0]
            block = block.iloc[1:].reset_index(drop=True)
            block.columns = [str(c).strip().lower().replace(" ", "_") for c in block.columns]

            # 🟡 STOP at 'OPEN ITEM' or 'PLANT / FACILITY' row in 'Area'
            if 'area' in block.columns:
                block["area_stripped"] = block["area"].astype(str).str.strip().str.upper()
                stop_markers = ["OPEN ITEM", "PLANT / FACILITY"]
                stop_idx = block[block["area_stripped"].isin(stop_markers)].index
                if not stop_idx.empty:
                    block = block.loc[:stop_idx[0]-1]  # before the stop marker
                block = block.drop(columns=["area_stripped"])

            block["section"] = sec
            block["report_date"] = report_date

            if sec in PATROL_SECTIONS:
                patrol_parts.append(block)
            else:
                qc_parts.append(block)

        if patrol_parts:
            all_patrol.append(pd.concat(patrol_parts, ignore_index=True))
        if qc_parts:
            all_qc.append(pd.concat(qc_parts, ignore_index=True))

    # FINAL: Combine everything
    df_maintenance = pd.concat(all_maintenance, ignore_index=True) if all_maintenance else pd.DataFrame()
    df_patrol      = pd.concat(all_patrol, ignore_index=True) if all_patrol else pd.DataFrame()
    df_qc          = pd.concat(all_qc, ignore_index=True) if all_qc else pd.DataFrame()

    print("[INFO] Maintenance shape:", df_maintenance.shape)
    print("[INFO] Patrol shape:", df_patrol.shape)
    print("[INFO] QC shape:", df_qc.shape)

# You can now do:
# df_maintenance.to_csv("maintenance_all.csv", index=False)

    return df_maintenance, df_patrol, df_qc


df_maintenance, df_patrol, df_qc = wave_file_processing(wave_file=wave_file,
                     maintenance_sections=MAINTENANCE_SECTIONS,
                     patrol_sections=PATROL_SECTIONS,
                     qc_sections=QC_SECTIONS)



# validation with dates 

print(sorted(df_maintenance['report_date'].unique()))
print(sorted(df_patrol['report_date'].unique()))
print(sorted(df_qc['report_date'].unique()))


sheet_dates = sorted([
    pd.to_datetime(re.search(r"\((.*?)\)", s).group(1)).strftime("%Y-%m-%d")
    for s in xls.sheet_names if re.search(r"\((.*?)\)", s)
])

print("\nExcel file dates:", sheet_dates)
print("\nMaintenance report_dates:", sorted(df_maintenance['report_date'].unique()))
print("\nPatrol report_dates:", sorted(df_patrol['report_date'].unique()))
print("\nQC report_dates:", sorted(df_qc['report_date'].unique()))


df_maintenance.to_csv(os.path.join(CLEANED_DATA_PATH, 'maintenance_cleaned.csv'), index=False)
df_patrol.to_csv(os.path.join(CLEANED_DATA_PATH, 'patrol_cleaned.csv'), index=False)
df_qc.to_csv(os.path.join(CLEANED_DATA_PATH, 'qc_cleaned.csv'), index=False)
print("[INFO] Maintenance, QC, Patrol CSV files saved in cleaned_data directory!")

# Export to SQLite database
import os
import sqlite3

db_path = os.path.join(PROJECT_ROOT, 'site_reporting.db')
conn = sqlite3.connect(db_path)

df_maintenance.to_sql('maintenance_reports', conn, if_exists='replace', index=False)
df_patrol.to_sql('daily_safety_patrol', conn, if_exists='replace', index=False)
df_qc.to_sql('qc_activities', conn, if_exists='replace', index=False)


conn.commit()
conn.close()
print("[INFO] Data exported to site_reporting.db!")


conn = sqlite3.connect(db_path)
for table in ['maintenance_reports', 'daily_safety_patrol', 'qc_activities']:
    print(f"[INFO] {table} count:", conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
conn.close()
print("[INFO] All processing complete! Data is ready for analysis.")