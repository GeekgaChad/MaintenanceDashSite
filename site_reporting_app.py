import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils import get_table, time_to_hours, get_wo_permit_overview

# ---- SIDEBAR NAV ----
st.sidebar.title("Site Reporting Dashboard")
menu = st.sidebar.radio(
    "Go to",
    [
        "📊 Maintenance Dashboard",
        "📊 Permit Dashboard",
        "📊 QC Dashboard",
        "📊 Patrol Dashboard",
        "🔗 WO & Permit Overview",
        "📊 MAP Dashboard",
        "➕ Submit Maintenance Report",
    ]
)

st.set_page_config(layout="wide")

# ---- VIEW REPORTS ----
if menu == "📋 View Reports":
    st.title("Maintenance Reports")
    st.subheader("View and filter maintenance reports submitted by Employees.")
    df = get_table("maintenance_reports")
    with st.expander("🔎 Filter Records", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        min_date, max_date = pd.to_datetime(df['report_date']).min(), pd.to_datetime(df['report_date']).max()
        date_range = col1.date_input("Date Range", [min_date, max_date])
        areas = sorted(df['area'].dropna().unique())
        area_select = col2.multiselect("Area", areas, default=None)
        statuses = sorted(df['status'].dropna().unique())
        status_select = col3.multiselect("Status", statuses, default=None)
        sections = sorted(df['section'].dropna().unique())
        section_select = col4.multiselect("Section", sections, default=None)

        filtered = df.copy()
        if len(date_range) == 2:
            start, end = [pd.to_datetime(d) for d in date_range]
            filtered = filtered[(pd.to_datetime(filtered['report_date']) >= start) & (pd.to_datetime(filtered['report_date']) <= end)]
        if area_select:
            filtered = filtered[filtered['area'].isin(area_select)]
        if status_select:
            filtered = filtered[filtered['status'].isin(status_select)]
        if section_select:
            filtered = filtered[filtered['section'].isin(section_select)]

        st.write(f"Filtered records: **{len(filtered)}**")
        st.dataframe(filtered)

        open_permits = df[df['status'].str.lower().str.contains("open|on-progress", na=False)]
        st.write("### Open/On-progress Permits")
        st.dataframe(open_permits)

# ---- SUBMIT WORK PERMIT (FORM) ----
elif menu == "➕ Submit Maintenance Report":
    st.title("Submit New Maintenance Report (DMR)")
    st.subheader("Please fill out the form below to submit a new maintenance report.")
    with st.form("dmr_form", clear_on_submit=True):
        area = st.text_input("Area")
        unit = st.text_input("Unit")
        tag_number = st.text_input("Tag Number")
        wo_number = st.text_input("WO Number")
        observation = st.text_area("Observation")
        recommendation = st.text_area("Recommendation")
        date = st.date_input("Date")
        status = st.selectbox("Status", ["Open", "On-progress", "Completed", "Cancelled"])
        reason_remark = st.text_input("Reason / Remark")
        root_cause = st.text_input("Root Cause")
        section = st.text_input("Section")
        report_date = st.date_input("Report Date")
        submit = st.form_submit_button("Submit Record")
    if submit:
        import sqlite3
        DB_PATH = "/Users/msagar/SankyuWork/site_reporting_project/site_reporting.db"
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO maintenance_reports (
                    area, unit, tag_number, wo_number, observation, recommendation, date,
                    status, reason_remark, root_cause, section, report_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                area, unit, tag_number, wo_number, observation, recommendation,
                date.strftime("%Y-%m-%d"),
                status, reason_remark, root_cause, section, report_date.strftime("%Y-%m-%d")
            ))
            conn.commit()
        st.success("Record submitted successfully!")

# ---- MAINTENANCE DASHBOARD ----
elif menu == "📊 Maintenance Dashboard":
    st.title("Maintenance KPIs Dashboard")
    st.subheader("Key Performance Indicators for Maintenance Reports")
    st.write("This dashboard provides insights into maintenance reports submitted by employees.")
    df = get_table("maintenance_reports")
    with st.expander("🔎 Filter Records", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        min_date, max_date = pd.to_datetime(df['report_date']).min(), pd.to_datetime(df['report_date']).max()
        date_range = col1.date_input("Date Range", [min_date, max_date])
        areas = sorted(df['area'].dropna().unique())
        area_select = col2.multiselect("Area", areas, default=None)
        statuses = sorted(df['status'].dropna().unique())
        status_select = col3.multiselect("Status", statuses, default=None)
        sections = sorted(df['section'].dropna().unique())
        section_select = col4.multiselect("Section", sections, default=None)

        filtered = df.copy()
        if len(date_range) == 2:
            start, end = [pd.to_datetime(d) for d in date_range]
            filtered = filtered[(pd.to_datetime(filtered['report_date']) >= start) & (pd.to_datetime(filtered['report_date']) <= end)]
        if area_select:
            filtered = filtered[filtered['area'].isin(area_select)]
        if status_select:
            filtered = filtered[filtered['status'].isin(status_select)]
        if section_select:
            filtered = filtered[filtered['section'].isin(section_select)]

        show_open = st.checkbox("Show only Open/On-progress Permits", value=False)
        if show_open:
            filtered = filtered[filtered['status'].str.lower().str.contains("open|on-progress", na=False)]
        
        st.write(f"Filtered records: **{len(filtered)}**")
        st.dataframe(filtered)
        
        

        status_counts = df['status'].value_counts()
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"### Total Maintenance Records: **{len(df)}**")
        with col2:
            try:
                comp = int(status_counts.get("Completed", 0))
                total = len(df)
                st.metric("Completion Rate", f"{(comp/total*100):.1f}%" if total else "N/A")
            except Exception:
                st.write("Status breakdown not available.")
        st.write("---")
        
        st.bar_chart(status_counts)

    st.write("---")

    st.subheader("📈 Trend Analysis for the Month")
    filtered['report_date'] = pd.to_datetime(filtered['report_date'], errors='coerce')
    filtered = filtered[filtered['report_date'].notna()]
    filtered['status_clean'] = filtered['status'].astype(str).str.strip().str.upper()
    filtered['is_completed'] = filtered['status_clean'] == "COMPLETED"
    filtered['is_on_progress'] = filtered['status_clean'].str.contains("ON-PROGRESS")
    filtered['is_failed'] = filtered['status_clean'].isin(["CANCELLED", "FAILURE", "FAILED"])
    daily = filtered.groupby(filtered['report_date'].dt.date).size().rename("Jobs per Day")
    daily_completed = filtered.groupby(filtered['report_date'].dt.date)['is_completed'].sum().rename("Completed Jobs per Day")
    daily_on_progress = filtered.groupby(filtered['report_date'].dt.date)['is_on_progress'].sum().rename("On-progress Jobs per Day")
    daily_failed = filtered.groupby(filtered['report_date'].dt.date)['is_failed'].sum().rename("Failures/Cancellations per Day")
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    with col1:
        st.subheader("Total Jobs Per Day")
        st.line_chart(daily)
    with col2:
        st.subheader("Completed Jobs Per Day")
        st.line_chart(daily_completed)
    with col3:
        st.subheader("On-progress Jobs Per Day")
        st.line_chart(daily_on_progress)
    with col4:
        st.subheader("Failures/Cancellations per Day")
        st.line_chart(daily_failed)

# ---- WPR DASHBOARD ----
# ---- WPR DASHBOARD ----
# ---- PERMIT DASHBOARD ----
elif menu == "📊 Permit Dashboard":
    st.title("Work Permit & Efficiency Dashboard (WPR Table)")

    wpr = get_table("WPR")
    wpr['date'] = pd.to_datetime(wpr['date'], errors='coerce')
    wpr['work_actual_start_time'] = pd.to_datetime(wpr['work_actual_start_time'], errors='coerce')
    wpr['work_finish_time'] = pd.to_datetime(wpr['work_finish_time'], errors='coerce')
    wpr['work_duration'] = wpr['(m-l)'].apply(time_to_hours)
    wpr['total_permit_time'] = wpr['(n-i)'].apply(time_to_hours)
    wpr['efficiency'] = pd.to_numeric(wpr['(m-l)/(n-i)'], errors='coerce')

    min_date, max_date = wpr['date'].min(), wpr['date'].max()
    date_range = st.date_input("Date Range", [min_date, max_date], key="permit_date")
    filtered = wpr
    if len(date_range) == 2:
        start, end = pd.to_datetime(date_range)
        filtered = wpr[(wpr['date'] >= start) & (wpr['date'] <= end)]

    col1, col2 = st.columns([2, 3])

    # ---- KPI CARDS ----
    with col1:
        st.metric("Total Permits Issued", len(filtered))
        # Avg Work Duration (from m-l)
        if filtered['work_duration'].notna().sum():
            st.metric("Avg Work Duration (hrs)", f"{filtered['work_duration'].mean():.2f}")
        else:
            st.metric("Avg Work Duration (hrs)", "N/A")
        # Avg Permit Cycle (from n-i)
        if filtered['total_permit_time'].notna().sum():
            st.metric("Avg Permit Cycle (hrs)", f"{filtered['total_permit_time'].mean():.2f}")
        else:
            st.metric("Avg Permit Cycle (hrs)", "N/A")
        # Avg Efficiency
        if filtered['efficiency'].notna().sum():
            st.metric("Avg Efficiency", f"{filtered['efficiency'].mean():.2f}")
        else:
            st.metric("Avg Efficiency", "N/A")
        # Avg Permit Close Time (from actual start/finish)
        if not filtered['work_finish_time'].isna().all() and not filtered['work_actual_start_time'].isna().all():
            filtered['duration'] = (filtered['work_finish_time'] - filtered['work_actual_start_time']).dt.total_seconds() / 3600
            avg_duration = filtered['duration'].mean()
            st.metric("Avg Permit Close Time (hrs)", f"{avg_duration:.2f}" if pd.notnull(avg_duration) else "N/A")
        else:
            st.metric("Avg Permit Close Time (hrs)", "N/A")

    with col2:
        if 'plant/rtm_no' in filtered.columns:
            st.subheader("Permits by Plant/RTM")
            st.bar_chart(filtered['plant/rtm_no'].value_counts())
    
    if 'crew_members' in filtered.columns:
            st.subheader("Permits by Crew")
            st.bar_chart(filtered['crew_members'].value_counts())

    # ---- Efficiency Trend Toggle ----
    show_trend = st.checkbox("Show Efficiency Trend Over Time", value=False)
    if show_trend:
        st.subheader("Efficiency Trend Over Time")
        eff_trend = filtered.set_index('date').resample('D')['efficiency'].mean().dropna()
        st.line_chart(eff_trend)

    st.write("### Permit Table")
    st.dataframe(filtered)



# ---- QC DASHBOARD ----
# ---- QC DASHBOARD ----
elif menu == "📊 QC Dashboard":
    st.title("Quality Control (QC) Activities Dashboard")

    qc = get_table("qc_activities")
    qc['report_date'] = pd.to_datetime(qc['report_date'], errors='coerce')

    with st.expander("🔎 Filter Records", expanded=False):
        col1, col2, col3, col4 = st.columns(4)

        min_date, max_date = qc['report_date'].min(), qc['report_date'].max()
        date_range = col1.date_input("Date Range", [min_date, max_date], key="qc_date")

        areas = sorted(qc['area'].dropna().unique())
        area_select = col2.multiselect("Area", areas, default=None)

        statuses = sorted(qc['status'].dropna().unique())
        status_select = col3.multiselect("Status", statuses, default=None)

        sections = sorted(qc['section'].dropna().unique()) if 'section' in qc.columns else []
        section_select = col4.multiselect("Section", sections, default=None)

        filtered_qc = qc.copy()
        if len(date_range) == 2:
            start, end = [pd.to_datetime(d) for d in date_range]
            filtered_qc = filtered_qc[(filtered_qc['report_date'] >= start) & (filtered_qc['report_date'] <= end)]
        if area_select:
            filtered_qc = filtered_qc[filtered_qc['area'].isin(area_select)]
        if status_select:
            filtered_qc = filtered_qc[filtered_qc['status'].isin(status_select)]
        if section_select:
            filtered_qc = filtered_qc[filtered_qc['section'].isin(section_select)]

        filter_linked = st.checkbox("Show only QC linked to WO and Permit", value=False)
        filtered_qc['linked_to_wo'] = filtered_qc['wo_number'].notna() & (filtered_qc['wo_number'] != "")
        filtered_qc['linked_to_permit'] = filtered_qc['wo_number'].isin(get_table('WPR')['wo_number'].dropna().unique())
        if filter_linked:
            filtered_qc = filtered_qc[filtered_qc['linked_to_wo'] & filtered_qc['linked_to_permit']]

        st.write(f"Filtered records: **{len(filtered_qc)}**")
        st.dataframe(filtered_qc)

    # ---- KPIs and Charts ----
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total QC Activities", len(filtered_qc))
        st.metric("QC Linked to WO", filtered_qc['linked_to_wo'].sum())
        st.metric("QC Linked to Permit", filtered_qc['linked_to_permit'].sum())
        st.write("### QC Linked to Permit")
        st.bar_chart(filtered_qc['linked_to_permit'].value_counts())
    with col2:
        if st.checkbox("Show QC linked to WO", value=False):
            st.write("### Linked vs Unlinked (QC to WO)")
            st.bar_chart(filtered_qc['linked_to_wo'].value_counts())

    # ---- More Analytics ----
    if st.checkbox("Show Top Work Types (scope_of_work)", value=False):
        st.subheader("Top Work Types")
        top_scope = filtered_qc['scope_of_work'].value_counts().head(10)
        st.bar_chart(top_scope)
        
    if st.checkbox("Show Most Common Procedures Used", value=False):
        st.subheader("Most Common Procedures Used")
        top_proc = filtered_qc['work_procedure_use'].value_counts().head(10)
        st.bar_chart(top_proc)

    if st.checkbox("Show Work Types by Area", value=False):
        st.subheader("Work Types by Area")
        if 'area' in filtered_qc.columns:
            area_counts = filtered_qc.groupby('area')['scope_of_work'].count()
            st.bar_chart(area_counts)

# ---- PATROL DASHBOARD ----
elif menu == "📊 Patrol Dashboard":
    st.title("Daily Safety Patrol Dashboard")
    patrol = get_table("daily_safety_patrol")
    patrol['report_date'] = pd.to_datetime(patrol['report_date'], errors='coerce')

    with st.expander("🔎 Filter Records", expanded=False):
        col1, col2, col3, col4 = st.columns(4)

        min_date, max_date = patrol['report_date'].min(), patrol['report_date'].max()
        date_range = col1.date_input("Date Range", [min_date, max_date], key="patrol_date")

        areas = sorted(patrol['area'].dropna().unique())
        area_select = col2.multiselect("Area", areas, default=None)

        statuses = sorted(patrol['status'].dropna().unique()) if 'status' in patrol.columns else []
        status_select = col3.multiselect("Status", statuses, default=None)

        types = sorted(patrol['type'].dropna().unique()) if 'type' in patrol.columns else []
        type_select = col4.multiselect("Type", types, default=None)

        filtered_patrol = patrol.copy()
        if len(date_range) == 2:
            start, end = [pd.to_datetime(d) for d in date_range]
            filtered_patrol = filtered_patrol[(filtered_patrol['report_date'] >= start) & (filtered_patrol['report_date'] <= end)]
        if area_select:
            filtered_patrol = filtered_patrol[filtered_patrol['area'].isin(area_select)]
        if status_select:
            filtered_patrol = filtered_patrol[filtered_patrol['status'].isin(status_select)]
        if type_select:
            filtered_patrol = filtered_patrol[filtered_patrol['type'].isin(type_select)]

        filtered_patrol['linked_to_permit'] = filtered_patrol['permit_no'].notna() & (filtered_patrol['permit_no'] != "")
        show_linked = st.checkbox("Show Only Patrols Linked to Permit", value=False)
        if show_linked:
            filtered_patrol = filtered_patrol[filtered_patrol['linked_to_permit']]

        # ---- Patrol Summary & Bar Chart in expander ----
        colA, colB = st.columns([2, 2])
        with colA:
            st.metric("Total Patrols", len(filtered_patrol))
            st.metric("Patrols Linked to Permit", filtered_patrol['linked_to_permit'].sum())
            st.metric("Patrols Without Permit", (~filtered_patrol['linked_to_permit']).sum())
        with colB:
            st.write("### Linked to Permit?")
            st.bar_chart(filtered_patrol['linked_to_permit'].value_counts(), use_container_width=True)

        st.write(f"Filtered records: **{len(filtered_patrol)}**")
        st.dataframe(filtered_patrol, use_container_width=True)

    # ---- Charts OUTSIDE expander ---

        if st.checkbox("Show 'Most Common Actions Taken' Chart", value=False):
            st.subheader("Most Common Actions Taken")
            st.bar_chart(filtered_patrol['action'].value_counts().head(10), use_container_width=True)

        if st.checkbox("Show 'Most Common Patrol Types' Chart", value=False):
            st.subheader("Most Common Patrol Types")
            st.bar_chart(filtered_patrol['type'].value_counts().head(10), use_container_width=True)

    if st.checkbox("Show 'Patrols per Area' Chart", value=True):
        st.subheader("### Patrols per Area")
        st.bar_chart(filtered_patrol['area'].value_counts(), use_container_width=True)

    if st.checkbox("Show 'By Status' Chart", value=True):
            if 'status' in filtered_patrol.columns:
                st.write("### By Status")
                st.bar_chart(filtered_patrol['status'].value_counts(), use_container_width=True)


# ---- WO & PERMIT OVERVIEW ----
elif menu == "🔗 WO & Permit Overview":
    st.title("Unified Work Order & Permit Overview")
    df = get_wo_permit_overview()
    with st.expander("🔎 Filter Records", expanded=False):
        col1, col2 = st.columns([2,3])
        if not df['maintenance_report_date'].isnull().all():
            min_date, max_date = pd.to_datetime(df['maintenance_report_date']).min(), pd.to_datetime(df['maintenance_report_date']).max()
            date_range = col1.date_input("WO Report Date Range", [min_date, max_date])
        else:
            date_range = None
        areas = sorted(df['maintenance_area'].dropna().unique())
        area_select = col2.multiselect("Maintenance Area", areas, default=None)
        filtered = df.copy()
        if date_range and len(date_range) == 2:
            start, end = [pd.to_datetime(d) for d in date_range]
            filtered = filtered[
                (pd.to_datetime(filtered['maintenance_report_date']) >= start) & (pd.to_datetime(filtered['maintenance_report_date']) <= end)
            ]
        if area_select:
            filtered = filtered[filtered['maintenance_area'].isin(area_select)]
    with col1:
        st.subheader("KPI Cards")
        st.metric("Total Work Orders", len(filtered))
        st.metric("WOs with Permits", filtered['permit_number'].notna().sum())
        eff_numeric = pd.to_numeric(filtered['efficiency'], errors='coerce')
        if eff_numeric.notna().sum() > 0:
            st.metric("Avg Efficiency", f"{eff_numeric.mean():.2f}")
        else:
            st.metric("Avg Efficiency", "N/A")
    with col2:
        if st.checkbox("Show WOs With/Without Permit Chart", value=True):
            st.write("### WOs With/Without Permit")
            st.bar_chart(filtered['permit_number'].notna().value_counts())
    st.write("### Linked WO & Permit Table")
    st.dataframe(filtered)
    if st.checkbox("Show WO by Area Chart", value=True):
        st.write("### Work Orders by Area")
        st.bar_chart(filtered['maintenance_area'].value_counts())

# ---- MAP DASHBOARD ----
elif menu == "📊 MAP Dashboard":
    st.title("MAP Activity Overview Dashboard")
    map_ = get_table("MAP")
    map_['execution_date'] = pd.to_datetime(map_['execution_date'], errors='coerce')
    min_date, max_date = map_['execution_date'].min(), map_['execution_date'].max()
    date_range = st.date_input("MAP Date Range", [min_date, max_date], key="map_date")
    if len(date_range) == 2:
        start, end = [pd.to_datetime(d) for d in date_range]
        map_ = map_[(map_['execution_date'] >= start) & (map_['execution_date'] <= end)]

    st.write(f"Filtered records: **{len(map_)}**")

    # Toggle for granularity
    show_daily = st.checkbox("Show Daily Trend", value=False)
    st.subheader("MAP Activities Over Time")
    if show_daily:
        # Daily (spiky)
        daily = map_.groupby(map_['execution_date'].dt.date).size().rename("Activities per Day")
        st.line_chart(daily)
    else:
        # Monthly (cleaner)
        monthly = map_.groupby(map_['execution_date'].dt.to_period("M")).size()
        monthly.index = monthly.index.astype(str)  # for Streamlit x-axis
        st.bar_chart(monthly.rename("Activities per Month"))

    # Toggle for area/type breakdowns
    show_area = st.checkbox("Show Activities by Area", value=True)
    show_type = st.checkbox("Show Activities by Type", value=True if 'maint_activ_type' in map_.columns else False)

    if show_area:
        st.subheader("Activities by Area")
        st.bar_chart(map_['area'].value_counts())

    if show_type and 'maint_activ_type' in map_.columns:
        st.subheader("Activities by Type")
        st.bar_chart(map_['maint_activ_type'].value_counts())

    st.write("### MAP Activities Table")
    st.dataframe(map_)

# ---- PERMIT EFFICIENCY DASHBOARD ----