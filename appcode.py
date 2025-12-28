import streamlit as st
import pandas as pd

# --- 1. INITIAL APP CONFIG ---
st.set_page_config(page_title="Offensive Play-Call Assistant", layout="wide")

# Initialize the Database
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=['Down', 'Distance', 'Hash', 'Play_Name', 'Gain', 'Success'])

# --- 2. THE FIXED HUDL PROCESSING FUNCTION ---
def process_hudl(file):
    try:
        # Load the file
        data = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        
        # Clean headers: remove spaces and make uppercase
        data.columns = data.columns.str.strip().str.upper()
        
        # MAPPING BASED ON YOUR SCREENSHOT:
        # DN -> Down | DIST -> Distance | HASH -> Hash | OFF PLAY -> Play_Name | GN/LS -> Gain
        mapping = {
            'DN': 'Down', 
            'DIST': 'Distance', 
            'HASH': 'Hash', 
            'OFF PLAY': 'Play_Name', 
            'GN/LS': 'Gain'
        }
        
        # Rename the columns found in your Excel
        clean = data.rename(columns=mapping)
        
        # Ensure 'Down' and 'Distance' are numbers (not text)
        clean['Down'] = pd.to_numeric(clean['Down'], errors='coerce')
        clean['Distance'] = pd.to_numeric(clean['Distance'], errors='coerce')
        clean['Gain'] = pd.to_numeric(clean['Gain'], errors='coerce')

        # Map your 'L', 'M', 'R' values to full words
        hash_map = {'L': 'Left', 'M': 'Middle', 'R': 'Right'}
        if 'Hash' in clean.columns:
            clean['Hash'] = clean['Hash'].map(hash_map).fillna('Middle')
        else:
            clean['Hash'] = 'Middle'

        # Calculate Success (Success if Gain >= Distance)
        def calc_success(row):
            try:
                return 1 if row['Gain'] >= row['Distance'] else 0
            except:
                return 0

        clean['Success'] = clean.apply(calc_success, axis=1)
        
        # SAFETY CHECK: Only try to use columns that actually exist
        final_cols = ['Down', 'Distance', 'Hash', 'Play_Name', 'Gain', 'Success']
        available_cols = [col for col in final_cols if col in clean.columns]
        
        # Return only the cleaned data
        return clean[available_cols].dropna(subset=['Down'])
    
    except Exception as e:
        st.error(f"Hudl Error: {e}")
        return None

# --- 3. SIDEBAR (TOOLS & LOGGING) ---
with st.sidebar:
    st.title("📂 Team Tools")
    
    st.subheader("Import Game Data")
    hudl_file = st.file_uploader("Upload Hudl Excel", type=['csv', 'xlsx'])
    if hudl_file:
        new_data = process_hudl(hudl_file)
        if new_data is not None:
            st.session_state.df = pd.concat([st.session_state.df, new_data], ignore_index=True)
            st.success("Hudl Data Imported!")

    st.divider()

    st.subheader("Log Live Play")
    with st.form("live_log", clear_on_submit=True):
        f_dn = st.selectbox("Down", [1, 2, 3, 4])
        f_dist = st.number_input("Distance", value=10)
        f_hash = st.radio("Hash", ["Left", "Middle", "Right"], horizontal=True)
        f_play = st.text_input("Play Name")
        f_gain = st.number_input("Gain/Loss", value=0)
        
        if st.form_submit_button("Save Play"):
            suc = 1 if f_gain >= f_dist else 0
            new_row = pd.DataFrame([[f_dn, f_dist, f_hash, f_play, f_gain, suc]], 
                                   columns=['Down', 'Distance', 'Hash', 'Play_Name', 'Gain', 'Success'])
            st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
            st.toast(f"Logged {f_play}")

# --- 4. MAIN DASHBOARD ---
st.title("🏈 Offensive Play-Call Assistant")

# The Situation Area
st.subheader("Current Situation")
c1, c2, c3 = st.columns(3)
with c1: cur_dn = st.selectbox("Current Down", [1, 2, 3, 4], key="s_dn")
with c2: cur_dist = st.slider("Distance to Go", 1, 20, 10)
with c3: cur_hash = st.radio("Field Position", ["Left", "Middle", "Right"], horizontal=True, index=1)

st.divider()

# Filter and Show Results
if not st.session_state.df.empty:
    results = st.session_state.df[
        (st.session_state.df['Down'] == cur_dn) & 
        (st.session_state.df['Distance'].between(cur_dist-2, cur_dist+2)) &
        (st.session_state.df['Hash'] == cur_hash)
    ]

    if not results.empty:
        st.subheader("Statistical Suggestions")
        summary = results.groupby('Play_Name').agg({'Success': 'mean', 'Gain': 'mean', 'Play_Name': 'count'})
        summary.columns = ['Success %', 'Avg Gain', 'Calls']
        summary['Success %'] = (summary['Success %'] * 100).astype(int)
        st.table(summary.sort_values('Success %', ascending=False))
    else:
        st.info("No historical data matches this situation.")
else:
    st.info("Upload data in the sidebar to see suggestions.")

with st.expander("View Full History"):
    st.dataframe(st.session_state.df, use_container_width=True)
