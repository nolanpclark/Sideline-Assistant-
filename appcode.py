import streamlit as st
import pandas as pd

# --- 1. INITIAL APP CONFIG ---
st.set_page_config(page_title="Offensive Play-Call Assistant", layout="wide")

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=['Down', 'Distance', 'Hash', 'Play_Name', 'Gain', 'Success'])

# --- 2. AGGRESSIVE DATA PROCESSING ---
def process_hudl(file):
    try:
        data = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        
        # Clean up column names immediately
        data.columns = data.columns.str.strip().str.upper()
        
        # Create a new clean dataframe
        clean = pd.DataFrame()

        # MANUALLY EXTRACT BY KEYWORD (More reliable than rename)
        # We look for headers that look like your Hudl export
        for col in data.columns:
            if col in ['DN', 'DOWN']: clean['Down'] = data[col]
            if col in ['DIST', 'DISTANCE']: clean['Distance'] = data[col]
            if col in ['HASH', 'SIDE']: clean['Hash'] = data[col]
            if col in ['OFF PLAY', 'PLAY NAME', 'PLAY']: clean['Play_Name'] = data[col]
            if col in ['GN/LS', 'GAIN', 'YDS']: clean['Gain'] = data[col]

        # Safety: If we still don't have Down, the app can't run
        if 'Down' not in clean.columns:
            st.error("Could not find 'DN' column in your file. Headers found: " + str(list(data.columns)))
            return None

        # Convert numeric columns and fill gaps
        clean['Down'] = pd.to_numeric(clean['Down'], errors='coerce')
        clean['Distance'] = pd.to_numeric(clean['Distance'], errors='coerce')
        clean['Gain'] = pd.to_numeric(clean['Gain'], errors='coerce')
        
        # Map L/M/R values
        hash_map = {'L': 'Left', 'M': 'Middle', 'R': 'Right'}
        if 'Hash' in clean.columns:
            clean['Hash'] = clean['Hash'].astype(str).str.strip().str.upper().map(hash_map).fillna('Middle')
        else:
            clean['Hash'] = 'Middle'

        # Success Logic
        clean['Success'] = clean.apply(lambda r: 1 if r['Gain'] >= r['Distance'] else 0, axis=1)
        
        # Drop rows where Down is missing
        return clean.dropna(subset=['Down'])
    
    except Exception as e:
        st.error(f"Hudl Error: {e}")
        return None

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("📂 Team Tools")
    hudl_file = st.file_uploader("Upload Hudl Excel", type=['csv', 'xlsx'])
    if hudl_file:
        new_data = process_hudl(hudl_file)
        if new_data is not None:
            st.session_state.df = pd.concat([st.session_state.df, new_data], ignore_index=True)
            st.success("Data Imported!")

    st.divider()
    st.subheader("Log Live Play")
    with st.form("live_log", clear_on_submit=True):
        f_dn = st.selectbox("Down", [1, 2, 3, 4])
        f_dist = st.number_input("Distance", value=10)
        f_hash = st.radio("Hash", ["Left", "Middle", "Right"], horizontal=True)
        f_play = st.text_input("Play Name")
        f_gain = st.number_input("Gain", value=0)
        if st.form_submit_button("Save"):
            suc = 1 if f_gain >= f_dist else 0
            new_row = pd.DataFrame([[f_dn, f_dist, f_hash, f_play, f_gain, suc]], 
                                   columns=['Down', 'Distance', 'Hash', 'Play_Name', 'Gain', 'Success'])
            st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)

# --- 4. MAIN DASHBOARD ---
st.title("🏈 Offensive Play-Call Assistant")

st.subheader("Current Situation")
c1, c2, c3 = st.columns(3)
with c1: cur_dn = st.selectbox("Current Down", [1, 2, 3, 4], key="s_dn")
with c2: cur_dist = st.slider("Distance to Go", 1, 20, 10)
with c3: cur_hash = st.radio("Field Position", ["Left", "Middle", "Right"], horizontal=True, index=1)

st.divider()

if not st.session_state.df.empty:
    results = st.session_state.df[
        (st.session_state.df['Down'] == cur_dn) & 
        (st.session_state.df['Distance'].between(cur_dist-2, cur_dist+2)) &
        (st.session_state.df['Hash'] == cur_hash)
    ]

    if not results.empty:
        summary = results.groupby('Play_Name').agg({'Success': 'mean', 'Gain': 'mean', 'Play_Name': 'count'})
        summary.columns = ['Success %', 'Avg Gain', 'Calls']
        summary['Success %'] = (summary['Success %'] * 100).astype(int)
        st.table(summary.sort_values('Success %', ascending=False))
    else:
        st.info("No historical data found.")
else:
    st.info("Upload data in the sidebar.")
