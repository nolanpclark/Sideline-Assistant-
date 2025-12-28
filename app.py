import streamlit as st
import pandas as pd
import datetime

# --- 1. INITIAL APP CONFIG ---
st.set_page_config(page_title="OC Sideline Assistant", layout="wide", initial_sidebar_state="expanded")

# Initialize the "Database" in the app's memory
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=['Down', 'Distance', 'Play_Name', 'Gain', 'Success'])

# --- 2. THE HUDL PROCESSING FUNCTION ---
def process_hudl(file):
    try:
        # Hudl can be .csv or .xlsx
        if file.name.endswith('.csv'):
            data = pd.read_csv(file)
        else:
            data = pd.read_excel(file)
        
        # Mapping Hudl's standard shorthand to our App
        # Note: If your Hudl uses different names, change the 'DN' part below
        clean = data.rename(columns={
            'DN': 'Down', 
            'DIST': 'Distance', 
            'OFF PLAY': 'Play_Name', 
            'GN/LS': 'Gain'
        })
        
        # Calculate success for the imported plays
        clean['Success'] = clean.apply(lambda x: 1 if x['Gain'] >= x['Distance'] else 0, axis=1)
        
        return clean[['Down', 'Distance', 'Play_Name', 'Gain', 'Success']]
    except Exception as e:
        st.error(f"Could not read Hudl file. Error: {e}")
        return None

# --- 3. SIDEBAR: DATA & LOGGING ---
with st.sidebar:
    st.title("📂 Team Tools")
    
    # --- HUDL UPLOADER ---
    st.subheader("Import Game Data")
    hudl_file = st.file_uploader("Upload Hudl Excel/CSV", type=['csv', 'xlsx'])
    
    if hudl_file:
        new_data = process_hudl(hudl_file)
        if new_data is not None:
            st.session_state.df = pd.concat([st.session_state.df, new_data], ignore_index=True)
            st.success("Successfully imported Hudl stats!")

    st.divider()

    # --- MANUAL PLAY LOG ---
    st.subheader("Log Live Play")
    with st.form("live_log", clear_on_submit=True):
        f_dn = st.selectbox("Down", [1, 2, 3, 4])
        f_dist = st.number_input("Distance", value=10)
        f_play = st.text_input("Play Called (e.g. Power O)")
        f_gain = st.number_input("Yards Gained", value=0)
        
        if st.form_submit_button("Log Play"):
            # Simple success logic: Did we get the first down?
            success = 1 if f_gain >= f_dist else 0
            new_row = pd.DataFrame([[f_dn, f_dist, f_play, f_gain, success]], 
                                   columns=['Down', 'Distance', 'Play_Name', 'Gain', 'Success'])
            st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
            st.toast(f"Logged {f_play}!")

# --- 4. MAIN DASHBOARD: THE SUGGESTION ENGINE ---
st.title("🏈 Offensive Play-Call Assistant")

# Quick Stats at a glance
if not st.session_state.df.empty:
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Plays", len(st.session_state.df))
    m2.metric("Success Rate", f"{int(st.session_state.df['Success'].mean() * 100)}%")
    m3.metric("Avg Gain", round(st.session_state.df['Gain'].mean(), 1))

st.divider()

# The "Play Caller" Selection
col_input, col_results = st.columns([1, 2])

with col_input:
    st.subheader("The Situation")
    cur_dn = st.pills("Down", [1, 2, 3, 4], key="pills_dn")
    cur_dist = st.slider("Distance to Go", 1, 20, 10)

with col_results:
    st.subheader("Top Suggestions")
    
    # Filter data based on user input
    # We look for the same down and a similar distance (+/- 2 yards)
    results = st.session_state.df[
        (st.session_state.df['Down'] == cur_dn) & 
        (st.session_state.df['Distance'].between(cur_dist-2, cur_dist+2))
    ]
    
    if not results.empty:
        # Create a summary of what's working
        summary = results.groupby('Play_Name').agg({
            'Success': 'mean',
            'Gain': 'mean',
            'Play_Name': 'count'
        }).rename(columns={'Play_Name': 'Calls', 'Success': 'Success %', 'Gain': 'Avg Gain'})
        
        # Sort by best success rate
        st.dataframe(summary.sort_values('Success %', ascending=False), use_container_width=True)
    else:
        st.info("No historical data found for this situation. Start logging plays or upload a Hudl export!")

# --- 5. DATA PREVIEW ---
with st.expander("View Raw Play History"):
    st.dataframe(st.session_state.df, use_container_width=True)
