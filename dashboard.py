import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Electronics Assembly | PS-002", page_icon="⚙️", layout="wide")
st.title("⚙️ Smart Electronics Assembly Monitoring")
st.markdown("Live OEE, downtime tracking, and production output for SMT Line 1.")

# --- MACHINE MAP ---
machine_map = {
    'M1_ComponentMounter': 'Component Mounter', 
    'M2_ReflowOven': 'Reflow Oven', 
    'M3_AOI_Scanner': 'AOI Scanner'
}

# --- SMART DIAGNOSTICS DICTIONARY ---
diagnostic_map = {
    "Feeder Jam": {"cause": "Component tape stuck in the feeder mechanism.", "action": "Open feeder, clear stuck tape, and re-index."},
    "Vacuum Nozzle Clogged": {"cause": "Dust blocking the pick-up nozzle.", "action": "Clean nozzle with a thin wire and alcohol."},
    "Component Reel Empty": {"cause": "Out of microchips on the reel.", "action": "Splice new component reel into the feeder."},
    "Vision Alignment Error": {"cause": "Camera cannot locate the fiducial marks on the PCB.", "action": "Clean camera lens and verify PCB seating."},
    "Operator Break": {"cause": "Operator away from station.", "action": "Wait or call relief operator."},
    
    "Heating Zone Failure": {"cause": "Thermocouple or heater element burnt out.", "action": "Check zone heater resistance and replace thermocouple."},
    "Conveyor Belt Stalled": {"cause": "PCB edge caught on the oven track.", "action": "Clear the track and check chain tension."},
    "Temperature Out of Spec": {"cause": "Oven temperature deviated from the recipe profile.", "action": "Hold boards, check heating profile software."},
    "Cooling Fan Fault": {"cause": "Cooling fan stopped, risking thermal shock.", "action": "Replace cooling fan motor."},
    "Shift Handover": {"cause": "Scheduled shift change.", "action": "Complete handover checklist."},

    "Camera Calibration Error": {"cause": "Optical vision system out of alignment.", "action": "Run auto-calibration routine."},
    "Lighting Module Failure": {"cause": "LED ring light burnt out or disconnected.", "action": "Replace AOI lighting module."},
    "Software Timeout": {"cause": "Inspection software froze or lost network.", "action": "Restart AOI software and re-run board."},
    "Conveyor Sensor Blocked": {"cause": "Dust or debris on the optical sensor.", "action": "Wipe down the conveyor sensor lens."},
    "Quality Check Required": {"cause": "Scheduled verification by QC engineer.", "action": "Manually inspect the last 5 rejected boards."},

    # Cascading Failure Diagnostics
    "Starved (Waiting for M1)": {"cause": "Upstream Component Mounter is down.", "action": "Clear bottleneck at M1."},
    "Blocked (Waiting for M2)": {"cause": "Downstream Reflow Oven is down.", "action": "Clear bottleneck at M2."}
}

# --- DATABASE CONNECTION ---
DB_PATH = 'data/factory.db'

def get_data():
    conn = sqlite3.connect(DB_PATH)
    
    query_latest = """
        SELECT machine_id, status, parts_produced, cycle_time_sec, timestamp, downtime_reason
        FROM machine_events
        WHERE id IN (SELECT MAX(id) FROM machine_events GROUP BY machine_id)
    """
    df_latest = pd.read_sql_query(query_latest, conn)
    df_latest['machine_name'] = df_latest['machine_id'].map(machine_map)
    
    query_downtime = """
        SELECT machine_id, downtime_reason, COUNT(*) as occurrences
        FROM machine_events 
        WHERE status = 'DOWN' 
        GROUP BY machine_id, downtime_reason
    """
    df_downtime = pd.read_sql_query(query_downtime, conn)
    df_downtime['machine_name'] = df_downtime['machine_id'].map(machine_map)
    
    query_history = """
        SELECT timestamp, machine_id, parts_produced 
        FROM machine_events 
        ORDER BY timestamp ASC
    """
    df_history = pd.read_sql_query(query_history, conn)
    df_history['machine_name'] = df_history['machine_id'].map(machine_map)
    
    conn.close()
    return df_latest, df_downtime, df_history

# --- SIDEBAR ---
with st.sidebar:
    st.header("System Controls")
    with st.expander("ℹ️ System Information", expanded=True):
        st.write("**Line:** SMT Electronics 1")
        st.write("**Data Source:** Simulated PLC")
        st.write("**Status:** Connected")
    if st.button('🔄 Force Data Refresh', use_container_width=True):
        st.rerun()
    st.divider()
    st.caption("PS-002 Prototype | Smart Manufacturing")

# Load data
try:
    df_latest, df_downtime, df_history = get_data()
    
    # --- TOP LEVEL KPIs ---
    total_parts = df_latest['parts_produced'].sum()
    machines_down = len(df_latest[df_latest['status'] == 'DOWN'])
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric(label="Total PCBs Assembled", value=f"{total_parts:,}", help="Cumulative sum of all circuit boards produced.")
    kpi2.metric(label="Machines Running", value=f"{len(df_latest) - machines_down} / {len(df_latest)}", help="Machines running vs total.")
    kpi3.metric(label="Active Alerts", value=machines_down, delta="Requires Action" if machines_down > 0 else "All Clear", delta_color="inverse", help="Warnings for DOWN machines.")
    
    st.divider()

    # --- REAL-TIME STATUS & SMART DIAGNOSTICS ---
    st.subheader("Live Equipment Status")
    st.caption("Real-time view of assembly line states with engineering diagnostic recommendations.")
        
    cols = st.columns(len(df_latest))
    
    for index, row in df_latest.iterrows():
        with cols[index]:
            if row['status'] == 'RUNNING':
                st.success(f"**{row['machine_name']}**\n\nStatus: RUNNING")
            else:
                st.error(f"**{row['machine_name']}**\n\nStatus: DOWN")
                
                reason = row['downtime_reason']
                diag = diagnostic_map.get(reason, {"cause": "Unknown fault.", "action": "Investigate manually."})
                
                st.warning(f"**Fault:** {reason}")
                with st.expander("🔍 Why is it down & How to fix", expanded=True):
                    st.write(f"**Possible Cause:** {diag['cause']}")
                    st.info(f"**Action:** {diag['action']}")
                
                st.toast(f"🚨 ALERT: {row['machine_name']} is DOWN!", icon="⚠️")
            
            st.metric(label="Units Processed", value=f"{row['parts_produced']:,}")
            st.caption(f"Last Ping: {row['timestamp']}")

    st.divider()

    # --- ANALYTICS ---
    col1, col2 = st.columns([6, 4])
    
    with col1:
        st.subheader("Production Output Trend")
        st.caption("Tracks cumulative units processed. A flat line indicates downtime.")
        fig_history = px.line(df_history, x="timestamp", y="parts_produced", color="machine_name", markers=True)
        fig_history.update_layout(xaxis_title="Time", yaxis_title="Cumulative Units", legend_title="Machine")
        st.plotly_chart(fig_history, use_container_width=True)
        
    with col2:
        st.subheader("Downtime Pareto (Bottlenecks)")
        st.caption("Ranks fault scenarios to identify the biggest line stoppages.")
        if not df_downtime.empty:
            fig_pareto = px.bar(df_downtime, x="occurrences", y="downtime_reason", color="machine_name", orientation='h', barmode="group")
            fig_pareto.update_layout(xaxis_title="Number of Stops", yaxis_title="", legend_title="Machine")
            st.plotly_chart(fig_pareto, use_container_width=True)
        else:
            st.info("No downtime events recorded yet. Wait a bit!")

    st.divider()

    # --- BOTTOM SECTION: REPORT ---
    st.subheader("Shift Downtime Log")
    st.caption("Detailed log of recent line stops with actionable engineering instructions.")
    
    query_log = """
        SELECT timestamp, machine_id, downtime_reason, cycle_time_sec 
        FROM machine_events 
        WHERE status = 'DOWN' 
        ORDER BY timestamp DESC LIMIT 20
    """
    conn = sqlite3.connect(DB_PATH)
    df_log = pd.read_sql_query(query_log, conn)
    conn.close()
    
    df_log['Action Required'] = df_log['downtime_reason'].apply(lambda x: diagnostic_map.get(x, {}).get('action', 'Investigate'))
    
    df_log = df_log.rename(columns={"timestamp": "Date/Time", "machine_id": "Machine", "downtime_reason": "Fault Scenario", "cycle_time_sec": "Cycle Time (s)"})
    df_log['Machine'] = df_log['Machine'].map(machine_map)
    df_log = df_log[["Date/Time", "Machine", "Fault Scenario", "Action Required", "Cycle Time (s)"]]
    
    st.dataframe(df_log, use_container_width=True, hide_index=True)
    
    csv = df_log.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Shift Report (CSV)",
        data=csv,
        file_name='electronics_shift_report.csv',
        mime='text/csv',
        help="Download this table as a spreadsheet for management."
    )

except Exception as e:
    st.error(f"Waiting for database... Make sure `simulate.py` is running. Error: {e}")