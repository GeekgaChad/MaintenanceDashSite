import sqlite3
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()

DB_PATH = "/Users/msagar/SankyuWork/site_reporting_project/sample_site_reporting.db"

# TABLE CREATION SQL (fill in as per your schema for portability)
CREATE_TABLES = {
    'maintenance_reports': """
        CREATE TABLE IF NOT EXISTS maintenance_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area TEXT, unit TEXT, tag_number TEXT, wo_number TEXT, observation TEXT,
            recommendation TEXT, date TEXT, status TEXT, reason_remark TEXT,
            root_cause TEXT, section TEXT, report_date TEXT
        );
    """,
    'WPR': """
        CREATE TABLE IF NOT EXISTS WPR (
            receiver_name TEXT, position TEXT, date TEXT, crew_members TEXT, wo_number TEXT,
            wo_description TEXT, permit_number TEXT, "plant/rtm_no" TEXT,
            time_of_requesting_permit TEXT, time_of_issuer_starting_swp_preperation TEXT,
            time_of_permit_issuance TEXT, work_actual_start_time TEXT, work_finish_time TEXT,
            swp_closing_time TEXT, remarks TEXT, "(m-l)" TEXT, "(n-i)" TEXT, "(m-l)/(n-i)" TEXT
        );
    """,
    'qc_activities': """
        CREATE TABLE IF NOT EXISTS qc_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sn TEXT, area TEXT, wo_number TEXT, eqp_number TEXT, scope_of_work TEXT,
            work_procedure_use TEXT, observation_findings TEXT, action TEXT, status TEXT,
            reported_by TEXT, remarks TEXT, section TEXT, report_date TEXT
        );
    """,
    'daily_safety_patrol': """
        CREATE TABLE IF NOT EXISTS daily_safety_patrol (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area TEXT, rtm TEXT, permit_no TEXT, work_description TEXT, observation TEXT,
            action TEXT, type TEXT, group_ TEXT, status TEXT, report_by TEXT,
            section TEXT, report_date TEXT
        );
    """,
    'MAP': """
        CREATE TABLE IF NOT EXISTS MAP (
            sn TEXT, execution_date TEXT, dmr_sn TEXT, "wo_＃" TEXT, maint_activ_type TEXT,
            area TEXT, "functional_loc._/_item_no." TEXT, description TEXT,
            activity_overvise TEXT, "note/highlight" TEXT
        );
    """
}

tables = ['maintenance_reports', 'WPR', 'qc_activities', 'daily_safety_patrol', 'MAP']
TARGET_SIZE = 100  # You can change to 1000+ for bigger demo db

def random_date(start_days_ago=90):
    days = random.randint(0, start_days_ago)
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 1. Create tables if missing
for t in tables:
    cur.execute(CREATE_TABLES[t])

# 2. Delete old data for NDA-safe dummy DB
for t in tables:
    cur.execute(f"DELETE FROM {t}")

conn.commit()

# 3. Fill each table with ~TARGET_SIZE rows of dummy data
for _ in range(int(TARGET_SIZE * 0.9)):
    cur.execute("""
        INSERT INTO maintenance_reports (
            area, unit, tag_number, wo_number, observation, recommendation, date,
            status, reason_remark, root_cause, section, report_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        fake.word().capitalize() + " Area",
        fake.bothify(text='Unit-###'),
        fake.bothify(text='TAG-####'),
        fake.bothify(text='WO-#####'),
        fake.sentence(),
        fake.sentence(),
        random_date(),
        random.choice(['Open', 'On-progress', 'Completed', 'Cancelled']),
        fake.sentence(),
        fake.word(),
        fake.word().capitalize(),
        random_date()
    ))

for _ in range(int(TARGET_SIZE * 0.9)):
    cur.execute("""
        INSERT INTO WPR (
            receiver_name, position, date, crew_members, wo_number,
            wo_description, permit_number, "plant/rtm_no",
            time_of_requesting_permit, time_of_issuer_starting_swp_preperation,
            time_of_permit_issuance, work_actual_start_time, work_finish_time,
            swp_closing_time, remarks, "(m-l)", "(n-i)", "(m-l)/(n-i)"
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        fake.name(),
        fake.job(),
        random_date(),
        fake.name(),
        fake.bothify(text='WO-#####'),
        fake.sentence(),
        fake.bothify(text='PERMIT-#####'),
        fake.word().capitalize(),
        random_date(),
        random_date(),
        random_date(),
        random_date(),
        random_date(),
        random_date(),
        fake.sentence(),
        str(random.uniform(1, 5)),
        str(random.uniform(1, 7)),
        str(round(random.uniform(0.5, 1.1), 2))
    ))

for _ in range(int(TARGET_SIZE * 0.9)):
    cur.execute("""
        INSERT INTO qc_activities (
            sn, area, wo_number, eqp_number, scope_of_work, work_procedure_use,
            observation_findings, action, status, reported_by, remarks, section, report_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        fake.bothify(text='SN-#####'),
        fake.word().capitalize(),
        fake.bothify(text='WO-#####'),
        fake.bothify(text='EQP-###'),
        fake.word(),
        fake.word(),
        fake.sentence(),
        fake.word(),
        random.choice(['Open', 'Closed', 'On-progress', 'Completed']),
        fake.name(),
        fake.sentence(),
        fake.word().capitalize(),
        random_date()
    ))

for _ in range(int(TARGET_SIZE * 0.9)):
    cur.execute("""
        INSERT INTO daily_safety_patrol (
            area, rtm, permit_no, work_description, observation, action, type,
            group_, status, report_by, section, report_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        fake.word().capitalize(),
        fake.bothify(text='RTM-###'),
        fake.bothify(text='PERMIT-#####'),
        fake.sentence(),
        fake.sentence(),
        fake.word(),
        random.choice(['Routine', 'Special', 'Emergency']),
        fake.word(),
        random.choice(['Open', 'Closed']),
        fake.name(),
        fake.word().capitalize(),
        random_date()
    ))

for _ in range(int(TARGET_SIZE * 0.9)):
    cur.execute("""
        INSERT INTO MAP (
            sn, execution_date, dmr_sn, "wo_＃", maint_activ_type, area,
            "functional_loc._/_item_no.", description, activity_overvise, "note/highlight"
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        fake.bothify(text='SN-#####'),
        random_date(),
        fake.bothify(text='DMR-####'),
        fake.bothify(text='WO-#####'),
        fake.word(),
        fake.word().capitalize(),
        fake.bothify(text='FL-###'),
        fake.sentence(),
        fake.word(),
        fake.sentence()
    ))

conn.commit()
conn.close()

print(f"Sample DB created and filled: {int(TARGET_SIZE * 0.9)} rows per table. All dummy, NDA-safe!")
