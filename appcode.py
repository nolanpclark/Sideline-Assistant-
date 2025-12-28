import streamlit as st
import pandas as pd 
import datetime

def process_hudl_upload(uploaded_file):
    # Read the Hudl Excel/CSV
    hudl_df = pd.read_csv(uploaded_file) # or pd.read_excel
    
    # Map Hudl's columns to your App's format
    # Adjust these names based on your specific Hudl setup
    clean_df = hudl_df.rename(columns={
        'DN': 'Down',
        'DIST': 'Distance',
        'OFF PLAY': 'Play_Name',
        'GN/LS': 'Gain'
    })
    
    # Save it to your app's database
    return clean_df
# --- CONFIGURATION ---
st.set_page_config(page_title="OC Sideline Assistant", layout="wide")
DB_FILE = "play_data.csv"

# Load or Initialize Data
try:
    df = pd.read_csv(DB_FILE)
except FileNotFoundError:
    df = pd.DataFrame(columns=['Timestamp', 'Down', 'Distance', 'Hash', 'Play_Type', 'Play_Name', 'Gain', 'Success'])

# --- SIDEBAR: LOG NEW PLAY ---
# INSIDE YOUR SIDEBAR SECTION
st.sidebar.title("Data Tools")

hudl_file = st.sidebar.file_uploader("Upload Hudl Export", type=['csv', 'xlsx'])

if hudl_file is not None:
    new_data = process_hudl_upload(hudl_file)
    if new_data is not None:
        # This merges the Hudl data into your existing play database
        df = pd.concat([df, new_data], ignore_index=True)
        st.sidebar.success("Hudl Data Imported!")

st.sidebar.header("📊 Log Recent Play")
with st.sidebar.form("play_form", clear_on_submit=True):
    down = st.selectbox("Down", [1, 2, 3, 4])
    dist = st.number_input("Distance to Go", min_value=1, max_value=99, value=10)
    hash_mark = st.radio("Hash Mark", ["Left", "Middle", "Right"])
    p_type = st.selectbox("Type", ["Run", "Pass", "RPO", "Screen"])
    name = st.text_input("Play Name (e.g., Inside Zone)")
    gain = st.number_input("Yards Gained", value=0)

    submitted = st.form_submit_button("Save Play")
    if submitted:
        # Success Logic: 40% on 1st, 50% on 2nd, 100% on 3rd/4th
        success_threshold = dist if down >= 3 else (dist * 0.5 if down == 2 else dist * 0.4)
        is_success = 1 if gain >= success_threshold else 0
        
        new_row = pd.DataFrame([{
            'Timestamp': datetime.datetime.now(),
            'Down': down, 'Distance': dist, 'Hash': hash_mark,
            'Play_Type': p_type, 'Play_Name': name, 'Gain': gain, 'Success': is_success
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        st.sidebar.success("Play Logged!")

# --- MAIN PAGE: CALL THE NEXT PLAY ---
st.title("🏈 Offensive Play-Call Assistant")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Current Situation")
    cur_down = st.pills("Current Down", [1, 2, 3, 4], key="cur_down")
    cur_dist = st.slider("Distance to Go", 1, 20, 10)
    cur_hash = st.segmented_control("Field Position", ["Left", "Middle", "Right"])

with col2:
    st.subheader("Statistical Suggestions")
    
    # Filter Logic
    if not df.empty:
        # Match current down and distance (+/- 2 yards)
        suggestions = df[(df['Down'] == cur_down) & (df['Distance'].between(cur_dist-2, cur_dist+2))]
        
        if not suggestions.empty:
            stats = suggestions.groupby('Play_Name').agg({
                'Success': 'mean',
                'Gain': 'mean',
                'Play_Name': 'count'
            }).rename(columns={'Play_Name': 'Calls', 'Success': 'Success %', 'Gain': 'Avg Gain'})
            
            st.dataframe(stats.sort_values('Success %', ascending=False), use_container_width=True)
        else:
            st.info("No historical data for this exact situation yet.")
    else:
        st.warning("Log some plays in the sidebar to see recommendations.")

# --- TENDENCY CHART ---
if not df.empty:
    st.divider()
    st.subheader("Game Tendencies")
    st.bar_chart(df['Play_Type'].value_counts())
