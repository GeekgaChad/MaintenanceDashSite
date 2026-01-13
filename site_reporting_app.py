import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils import get_connection, get_table, insert_wpr, insert_dmr, time_to_hours, get_wo_permit_overview, format_timedelta_to_h_m


import altair as alt

import sqlite3
from datetime import datetime



# Simple password protection
def check_password():
    #return True  # Disable password protection for now
    def password_entered():
        if st.session_state["password"] == "mypassword123":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input
        st.text_input("Password:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password:", type="password", on_change=password_entered, key="password")
        st.error("Password incorrect")
        return False
    else:
        return True


# ----------------------------------------------------------------------
# GLOBAL CONFIGURATION AND CSS INJECTION
# ----------------------------------------------------------------------

# MUST be the first Streamlit command
# --- GLOBAL CONFIGURATION AND CSS INJECTION ---
# MUST be the first Streamlit command
st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        width: 540px; /* Set a specific width to prevent "Maintenance Dashboard" from wrapping */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 🚨 GLOBAL FIX: Cache Data Loading Functions for Performance

@st.cache_data(ttl=600) # Cache data for 10 minutes
def load_maintenance_data():
    df = get_table("maintenance_reports")
    df['report_date'] = pd.to_datetime(df['report_date'], errors='coerce')
    return df

@st.cache_data(ttl=600)
def load_wpr_data():
    wpr = get_table("WPR")
    #print(wpr.columns.tolist())
    #print('time of requesting permit')
    #print(wpr['time_of_requesting_permit'])
    #print('time of issuer starting swp preperation')
    #print(wpr['time_of_issuer_starting_swp_preperation'])
    #print('time of permit issuance')
    #print(wpr['time_of_permit_issuance'])
    #rint('swp closing time')
    #print(wpr['swp_closing_time'])
    
    # 1. Standard Date/Time Conversions
    wpr['date'] = pd.to_datetime(wpr['date'], errors='coerce')
    wpr['work_actual_start_time'] = pd.to_datetime(wpr['work_actual_start_time'], errors='coerce')
    wpr['work_finish_time'] = pd.to_datetime(wpr['work_finish_time'], errors='coerce')

    
    # 2. Robust Time Parsing Function (FIXED to handle NaT and invalid strings)
    def parse_time_only(t):
            if pd.isna(t) or not str(t).strip() or str(t).lower() == 'nat':
                return None
            
            s = str(t).strip()
            
            # 🚨 FIX 1: Replace semicolon with colon and strip milliseconds
            # This handles '13;20' and '07:00:00.000000'
            s = s.replace(";", ":")
            
            # Optional: Try to remove milliseconds if present, as they mess up simple format inferral
            if '.' in s:
                s = s.split('.')[0]
            
            # Coerce string into a datetime object (trying common HH:MM:SS and HH:MM formats)
            dt = pd.to_datetime(s, format='%H:%M:%S', errors='coerce')
            if pd.isna(dt):
                dt = pd.to_datetime(s, format='%H:%M', errors='coerce')
            
            # Check if coercion failed (resulted in NaT)
            if pd.isna(dt):
                return None
            
            # 🚨 FIX 2: Return a formatted string for display in Streamlit
            return dt.strftime('%H:%M')

    # Apply fix to all time columns
    # 🚨 FIX for ValueError: NaTType
    time_cols = ["time_of_requesting_permit", "time_of_issuer_starting_swp_preperation", "time_of_permit_issuance", "swp_closing_time"]
    for col in time_cols:
        # Check if the column exists to prevent error on get_table result
        if col in wpr.columns:
            wpr[col] = wpr[col].apply(parse_time_only)

    # 3. Calculation Conversions
    wpr['work_duration'] = wpr['(m-l)'].apply(time_to_hours)
    wpr['total_permit_time'] = wpr['(n-i)'].apply(time_to_hours)
    wpr['efficiency'] = round(pd.to_numeric(wpr['(m-l)/(n-i)'], errors='coerce'),2)
    # Ensure numeric types for calculation columns
    numeric_cols = ['work_duration', 'total_permit_time', 'efficiency']
    for col in numeric_cols:
        if col in wpr.columns:
            wpr[col] = pd.to_numeric(wpr[col], errors='coerce')
    return wpr


# ======================================================================
# APPLICATION START
# ======================================================================

if check_password():
    # ---- SIDEBAR NAV ----
    st.sidebar.title("Site Reporting Dashboard")
    
    menu = st.sidebar.radio(
        "Go to",
        [
            # 1. WO 360 Entry
            "🧾 WO 360 Entry",
            # 2. Maintenance Dashboard
            "📊 Maintenance Dashboard",
            # 3. MAP Dashboard
            "📊 Dashboard", 
            # 4. WO & Permit Overview
            "🔗 WO & Permit Overview",
            # 5. Permit Dashboard
            "📊 Permit Dashboard",
            # 6. QC Dashboard
            "📊 QC Dashboard",
            # 7. Safety Dashboard
            "📊 Safety Dashboard",
        ]
    )

    # ----------------------------------------------------------------------
    # ---- 1. WO 360 ENTRY (UNCHANGED) ----
    # ----------------------------------------------------------------------
    if menu == "🧾 WO 360 Entry":
        st.title("WO 360 — Single Entry (Cloud Sync)")
        
        # --- Local Helpers ---
        def parse_date(d):
            return pd.to_datetime(d, errors="coerce")

        def parse_time(t):
            if t is None or (isinstance(t, float) and pd.isna(t)) or (isinstance(t, str) and not t.strip()):
                return None
            s = str(t).strip().replace(";", ":")
            try:
                parts = s.split(":")
                if len(parts) == 2:
                    s = f"{int(parts[0]):02d}:{int(parts[1]):02d}:00"
                elif len(parts) == 3:
                    s = f"{int(parts[0]):02d}:{int(parts[1]):02d}:{int(float(parts[2])):02d}"
                else: return None
                datetime.strptime(s, "%H:%M:%S")
                return s
            except Exception: return None

        # --- Entry Form ---
        with st.form("wo360", clear_on_submit=False):
            # ... (UI input fields remain exactly as you had them) ...
            # [Ensure all your st.text_input and st.selectbox fields are here]
            
            submitted = st.form_submit_button("Submit to Cloud Vault")

        if submitted:
            if not wo_number.strip():
                st.error("WO Number is required.")
                st.stop()

            # Prepare time data
            times = {k: parse_time(v) for k, v in {
                "time_of_requesting_permit": t_req,
                "time_of_issuer_starting_swp_preperation": t_prep,
                "time_of_permit_issuance": t_issue,
                "work_actual_start_time": t_start,
                "work_finish_time": t_finish,
                "swp_closing_time": t_close
            }.items()}

            try:
                # 🚨 PROFESSIONAL CLOUD SYNC
                conn = get_connection() 
                with conn: # Handles Transaction automatically
                    with conn.cursor() as cur:
                        # 1) UPSERT Meta Data (Postgres Syntax)
                        cur.execute("""
                            INSERT INTO work_order_meta (wo_number, supervisor, department, shift, done_by)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT(wo_number) DO UPDATE SET
                                supervisor=EXCLUDED.supervisor,
                                department=EXCLUDED.department,
                                shift=EXCLUDED.shift,
                                done_by=EXCLUDED.done_by
                        """, (wo_number.strip(), supervisor or None, department or None, shift or None, done_by or receiver_name or None))

                        # 2) Payload Creation
                        wpr_payload = {
                            "receiver_name": receiver_name or None,
                            "position": position or None,
                            "date": str(parse_date(wpr_date).date()),
                            "crew_members": str(crew_members or "").strip() or None,
                            "wo_number": wo_number.strip(),
                            "wo_description": wo_description or None,
                            "permit_number": permit_number or None,
                            "plant/rtm_no": plant_rtm_no or None,
                            **times,
                            "remarks": wpr_remarks or None,
                            "(m-l)": None, "(n-i)": None, "(m-l)/(n-i)": None
                        }

                        dmr_payload = {
                            "area": area or None,
                            "unit": unit or None,
                            "tag_number": tag_number or None,
                            "wo_number": wo_number.strip(),
                            "observation": observation or None,
                            "recommendation": recommendation or None,
                            "date": str(parse_date(mr_date).date()),
                            "status": status,
                            "reason_remark": reason_remark or None,
                            "root_cause": root_cause or None,
                            "section": (section or department or None),
                            "report_date": str(parse_date(report_date).date())
                        }

                        # 3) Execute Cloud Inserts via Utils
                        insert_wpr(conn, wpr_payload)
                        insert_dmr(conn, dmr_payload)

                st.success(f"✅ WO {wo_number} synchronized with Frankfurt Cloud Vault.")
                st.cache_data.clear() # Refresh dashboards with new data

            except Exception as e:
                st.error(f"❌ Cloud Sync Failed — {e}")

    # ----------------------------------------------------------------------
    # ---- 2. MAINTENANCE DASHBOARD (ENHANCED) ----
    # ----------------------------------------------------------------------
    elif menu == "📊 Maintenance Dashboard":
        st.title("Maintenance Dashboard")
        st.write("This dashboard provides insights into maintenance reports submitted by employees.")

        # Load data using the cached function
        df = load_maintenance_data()
        df = df.drop(columns='date', errors='ignore')

        with st.expander("🔎 Filter Records", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            
            min_date, max_date = df['report_date'].min(), df['report_date'].max()
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
                filtered = filtered[(filtered['report_date'] >= start) & (filtered['report_date'] <= end)]
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
            st.dataframe(filtered, use_container_width=True)
            
            # --- KPIs and Charts ---
            status_counts = filtered['status'].value_counts()
            
            # 🚨 FIX: Remove Avg Resolution Time Logic since 'completion_date' is unavailable
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Records", len(filtered))
            with col2:
                try:
                    comp = int(status_counts.get("Completed", 0))
                    total = len(filtered)
                    st.metric("Completion Rate", f"{(comp/total*100):.1f}%" if total else "N/A")
                except Exception:
                    st.metric("Completion Rate", "N/A")
            # The previous third column for Avg Resolution Time is now omitted

            st.write("---")
            
            # 🚨 STATUS CHART: Displaying the Status Breakdown
            st.subheader("Current Status Breakdown")
            st.bar_chart(status_counts, use_container_width=True) 
            
        # ... (Your trend analysis line charts remain outside the expander) ...
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
            st.line_chart(daily, use_container_width=True)
        with col2:
            st.subheader("Completed Jobs Per Day")
            st.line_chart(daily_completed, use_container_width=True)
        with col3:
            st.subheader("On-progress Jobs Per Day")
            st.line_chart(daily_on_progress, use_container_width=True)
        with col4:
            st.subheader("Failures/Cancellations per Day")
            st.line_chart(daily_failed, use_container_width=True)


    # ----------------------------------------------------------------------
    # ---- 3. MAP DASHBOARD (UNCHANGED) ----
    # ----------------------------------------------------------------------
    elif menu == "📊 Dashboard":
        st.title("MAP Activity Overview")
        map_ = get_table("MAP")
        map_['execution_date'] = pd.to_datetime(map_['execution_date'], errors='coerce')
        min_date, max_date = map_['execution_date'].min(), map_['execution_date'].max()
        date_range = st.date_input("MAP Date Range", [min_date, max_date], key="map_date")
        if len(date_range) == 2:
            start, end = [pd.to_datetime(d) for d in date_range]
            map_ = map_[(map_['execution_date'] >= start) & (map_['execution_date'] <= end)]

        st.write(f"Filtered records: **{len(map_)}**")

        # --- Granularity Selector (Daily/Weekly/Monthly fix) ---
        st.subheader("MAP Activities Over Time")
        granularity = st.radio(
            "Select Time Granularity",
            ('Monthly', 'Weekly', 'Daily'),
            index=0 
        )
        
        if granularity == 'Daily':
            daily = map_.groupby(map_['execution_date'].dt.date).size().rename("Activities per Day")
            st.line_chart(daily, use_container_width=True)

        elif granularity == 'Weekly':
            weekly = map_.groupby(map_['execution_date'].dt.to_period("W")).size()
            weekly.index = weekly.index.astype(str) 
            st.bar_chart(weekly.rename("Activities per Week"), use_container_width=True)

        else: # Default is 'Monthly'
            monthly = map_.groupby(map_['execution_date'].dt.to_period("M")).size()
            monthly.index = monthly.index.astype(str) 
            st.bar_chart(monthly.rename("Activities per Month"), use_container_width=True)

        # Toggle for area/type breakdowns
        show_area = st.checkbox("Show Activities by Area", value=True)
        show_type = st.checkbox("Show Activities by Type", value=True if 'maint_activ_type' in map_.columns else False)

        if show_area:
            st.subheader("Activities by Area")
            st.bar_chart(map_['area'].value_counts(), use_container_width=True)

        if show_type and 'maint_activ_type' in map_.columns:
            st.subheader("Activities by Type")
            st.bar_chart(map_['maint_activ_type'].value_counts(), use_container_width=True)

        st.write("### MAP Activities Table")
        st.dataframe(map_, use_container_width=True) 


    # ----------------------------------------------------------------------
    # ---- 4. WO & PERMIT OVERVIEW (UNCHANGED) ----
    # ----------------------------------------------------------------------
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
                st.bar_chart(filtered['permit_number'].notna().value_counts(), use_container_width=True)
        st.write("### Linked WO & Permit Table")
        st.dataframe(filtered, use_container_width=True) 
        if st.checkbox("Show WO by Area Chart", value=True):
            st.write("### Work Orders by Area")
            st.bar_chart(filtered['maintenance_area'].value_counts(), use_container_width=True)


    # ----------------------------------------------------------------------
    # ---- 5. PERMIT DASHBOARD (ENHANCED) ----
    # ----------------------------------------------------------------------
    elif menu == "📊 Permit Dashboard":
        st.title("Work Permit & Efficiency Dashboard (WPR Table)")

        # Load data using the cached function
        wpr = load_wpr_data()

        min_date, max_date = wpr['date'].min(), wpr['date'].max()
        date_range = st.date_input("Date Range", [min_date, max_date], key="permit_date")
        filtered = wpr

        filtered['Work Duration (H:M)'] = filtered['(m-l)'].apply(format_timedelta_to_h_m)

        # 2. Format the (n-i) column (Permit Cycle Time)
        filtered['Permit Cycle (H:M)'] = filtered['(n-i)'].apply(format_timedelta_to_h_m)

        # 3. Optional: Format the efficiency percentage to two decimals (if it's not already)
        

        # filtering the decimals
        # filtering the decimals - ensure they are float first
        for col in ["work_duration", "total_permit_time", "efficiency"]:
            filtered[col] = pd.to_numeric(filtered[col], errors='coerce')
        
        filtered["work_duration"] = filtered["work_duration"].round(2)
        filtered["total_permit_time"] = filtered["total_permit_time"].round(2)
        filtered["efficiency"] = filtered["efficiency"].round(2)
        filtered['Efficiency (%)'] = filtered['efficiency']

        
        filtered.drop(columns=['duration'], errors='ignore', inplace=True) # same as work_duration 

        print(filtered.columns.tolist())


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
            # ENHANCEMENT: Toggle for RTM/Plant vs Crew
            chart_selection = st.radio(
                "Permit Breakdown By:",
                ("Plant/RTM Number", "Crew Members"),
                horizontal=True
            )
            st.subheader(f"Permits by {chart_selection}")
            
            if chart_selection == "Plant/RTM Number" and 'plant/rtm_no' in filtered.columns:
                st.bar_chart(filtered['plant/rtm_no'].value_counts().head(10), use_container_width=True)
            elif chart_selection == "Crew Members" and 'crew_members' in filtered.columns:
                st.bar_chart(filtered['crew_members'].value_counts().head(10), use_container_width=True)
            else:
                st.info(f"Column '{'plant/rtm_no' if chart_selection == 'Plant/RTM Number' else 'crew_members'}' not available or empty.")

        
        # 🚨 ENHANCEMENT: Efficiency Scatter Plot (FIXED)
        st.subheader("Efficiency vs Permit Times (Outlier Detection)")
        
        scatter_data = filtered.copy()
        print(scatter_data)
        scatter_data = scatter_data[
            (scatter_data['work_duration'].notna()) & 
            (scatter_data['total_permit_time'].notna()) &
            (scatter_data['work_duration'] > 0) & 
            (scatter_data['total_permit_time'] > 0)
        ].rename(columns={'work_duration': 'Work Duration (m-l)', 'total_permit_time': 'Total Permit Time (n-i)'})
        
        if len(scatter_data) > 5:
            # The check 'if 'altair' in globals()' is removed, 
            # as it was causing the misleading error message.
            chart = alt.Chart(scatter_data).mark_circle().encode(
                x=alt.X('Total Permit Time (n-i)', title='Total Permit Time (hrs)', scale=alt.Scale(type="log")),
                y=alt.Y('Work Duration (m-l)', title='Work Duration (hrs)', scale=alt.Scale(type="log")),
                color=alt.Color('efficiency', scale=alt.Scale(domain=[0, 50, 100], range=['red', 'yellow', 'green'], type="linear"), title="Efficiency"),
                tooltip=['wo_number', 'permit_number', 'Work Duration (m-l)', 'Total Permit Time (n-i)', alt.Tooltip('efficiency', format='.2f')]
            ).properties(
                title='Permit Efficiency Scatter Plot (Log Scale)'
            ).interactive()
            st.altair_chart(chart, use_container_width=True)
            st.caption("Lower left (low time investment, high efficiency) is optimal. Hover for details.")
        else:
            st.info("Not enough valid data points to plot the Efficiency Scatter Plot.")


        # 🚨 ENHANCEMENT: Time-Loss Breakdown (KPI Display)
        st.subheader("Average Permit Phase Time Breakdown")
        breakdown_data = {
            "Phase": ["Avg Work Duration (m-l)", "Avg Permit Cycle (n-i)"],
            "Time (Hours)": [
                filtered['work_duration'].mean(),
                filtered['total_permit_time'].mean()
            ]
        }
        
        breakdown_df = pd.DataFrame(breakdown_data).set_index("Phase").dropna()
        if not breakdown_df.empty:
            st.dataframe(breakdown_df.style.format(precision=2), use_container_width=True)
            st.caption("This shows the average time spent in the two main phases: the actual work (duration) and the permit issuance/closure (cycle).")
        
        # ---- Efficiency Trend Toggle ----
        show_trend = st.checkbox("Show Efficiency Trend Over Time", value=False)
        if show_trend:
            st.subheader("Efficiency Trend Over Time")
            eff_trend = filtered.set_index('date').resample('D')['efficiency'].mean().dropna()
            st.line_chart(eff_trend, use_container_width=True)

        st.write("### Permit Table")
        st.dataframe(
                    filtered[[
                        'receiver_name', 
                        'position', 
                        'date', 
                        'crew_members', 
                        'wo_number', 
                        'wo_description', 
                        'permit_number', 
                        'plant/rtm_no', 
                        'time_of_requesting_permit', 
                        'time_of_issuer_starting_swp_preperation', 
                        'time_of_permit_issuance', 
                        'work_actual_start_time', 
                        'work_finish_time', 
                        'swp_closing_time', 
                        'remarks', 
                        'Work Duration (H:M)', 
                        'Permit Cycle (H:M)', 
                        'Efficiency (%)'
                    ]],
                    width='stretch')



    # ----------------------------------------------------------------------
    # ---- 6. QC DASHBOARD (UNCHANGED) ----
    # ----------------------------------------------------------------------
    elif menu == "📊 QC Dashboard":
        st.title("Quality Control (QC) Activities Dashboard")
        # ... (rest of QC Dashboard code remains here) ...
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
            st.dataframe(filtered_qc, use_container_width=True) 

        # ---- KPIs and Charts ----
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total QC Activities", len(filtered_qc))
            st.metric("QC Linked to WO", filtered_qc['linked_to_wo'].sum())
            st.metric("QC Linked to Permit", filtered_qc['linked_to_permit'].sum())
            st.write("### QC Linked to Permit")
            st.bar_chart(filtered_qc['linked_to_permit'].value_counts(), use_container_width=True)
        with col2:
            if st.checkbox("Show QC linked to WO", value=False):
                st.write("### Linked vs Unlinked (QC to WO)")
                st.bar_chart(filtered_qc['linked_to_wo'].value_counts(), use_container_width=True)

        # ---- More Analytics ----
        if st.checkbox("Show Top Work Types (scope_of_work)", value=False):
            st.subheader("Top Work Types")
            top_scope = filtered_qc['scope_of_work'].value_counts().head(10)
            st.bar_chart(top_scope, use_container_width=True)
            
        if st.checkbox("Show Most Common Procedures Used", value=False):
            st.subheader("Most Common Procedures Used")
            top_proc = filtered_qc['work_procedure_use'].value_counts().head(10)
            st.bar_chart(top_proc, use_container_width=True)

        if st.checkbox("Show Work Types by Area", value=False):
            st.subheader("Work Types by Area")
            if 'area' in filtered_qc.columns:
                area_counts = filtered_qc.groupby('area')['scope_of_work'].count()
                st.bar_chart(area_counts, use_container_width=True)

    # ----------------------------------------------------------------------
    # ---- 7. PATROL DASHBOARD (UNCHANGED) ----
    # ----------------------------------------------------------------------
    elif menu == "📊 Safety Dashboard":
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

            # Add permit link column and filter
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
            # Fixed width
            st.dataframe(filtered_patrol, use_container_width=True)

        # --- CHARTS OUTSIDE EXPANDER START HERE ---

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
