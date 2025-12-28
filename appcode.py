import streamlit as st
import pandas as pd

# --- 1. INITIAL APP CONFIG ---
st.set_page_config(page_title="Sideline Science", layout="wide", initial_sidebar_state="expanded")

# Initialize the "Database" in session state with the 'Hash' column
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=['Down', 'Distance', 'Hash', 'Play_Name', 'Gain', 'Success'])

# --- 2. HUDL PROCESSING (FIXED FOR GAIN/HASH) ---
def process_hudl(file):
    try:
        data = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        
        # Clean column names (remove spaces and make uppercase for matching)
        data.columns = data.columns.str.strip().str.upper()
        
        # Mapping Hudl logic to our App
        # We search for 'GN/LS' first, then 'GAIN', then 'YDS' to get the actual play yardage
        mapping = {
            'DN': 'Down', 
            'DIST': 'Distance', 
            'OFF PLAY': 'Play_Name', 
            'GN/LS': 'Gain',  # Primary Hudl gain column
            'HASH': 'Hash'
        }
        
        # Fallback: if 'GN/LS' is missing but 'GAIN' exists, use 'GAIN'
        if 'GN/LS' not in data.columns and 'GAIN' in data.columns:
            mapping['GAIN'] = 'Gain'
        
        clean = data.rename(columns=mapping)
        
        # Ensure we have a Hash column
        if 'Hash' not in clean.columns:
            clean['Hash'] = 'Middle' # Default if missing
            
        # Success Logic (Football Efficiency)
        def calc_success(row):
            dist = row['Distance']
            gain = row['Gain']
            if row['Down'] == 1: return 1 if gain >= (dist * 0.4) else 0
            if row['Down'] == 2: return 1 if gain >= (dist * 0.5) else 0
            return 1 if gain >= dist else 0

        clean['Success'] = clean.apply(calc_success, axis=1)
        
        # Return only the columns we need for the app
        return clean[['Down', 'Distance', 'Hash', 'Play_Name', 'Gain', 'Success']]
    except Exception as e:
        st.error(f"Hudl Error: {e}. Check if your Excel has 'DN', 'DIST', and 'GN/LS' columns.")
        return None

# --- 3. SIDEBAR: LOGGING & TOOLS ---
with st.sidebar:
    st.title("📂 Team Tools")
    
    st.subheader("Import Game Data")
    hudl_file = st.file_uploader("Upload Hudl Excel/CSV", type=['csv', 'xlsx'])
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
        f_hash = st.radio("Hash Mark", ["Left", "Middle", "Right"], horizontal=True)
        f_play = st.text_input("Play Called")
        f_gain = st.number_input("Yards Gained", value=0)
        
        if st.form_submit_button("Log Play"):
            success = 1 if f_gain >= f_dist else 0
            new_row = pd.DataFrame([[f_dn, f_dist, f_hash, f_play, f_gain, success]], 
                                   columns=['Down', 'Distance', 'Hash', 'Play_Name', 'Gain', 'Success'])
            st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
            st.toast(f"Logged {f_play}!")

# --- 4. MAIN DASHBOARD ---
st.title("🏈 Sideline Science")

if not st.session_state.df.empty:
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Plays", len(st.session_state.df))
    m2.metric("Success Rate", f"{int(st.session_state.df['Success'].mean() * 100)}%")
    m3.metric("Avg Gain", round(st.session_state.df['Gain'].mean(), 1))

st.divider()

col_input, col_results = st.columns([1, 2])

with col_input:
    st.subheader("The Situation")
    cur_dn = st.pills("Down", [1, 2, 3, 4], key="pills_dn", default=1)
    cur_dist = st.slider("Distance to Go", 1, 20, 10)
    cur_hash = st.segmented_control("Field Position", ["Left", "Middle", "Right"], default="Middle")

with col_results:
    st.subheader("Top Suggestions")
    
    # FILTER: Using Down, Distance (+/- 2), and Hash
    results = st.session_state.df[
        (st.session_state.df['Down'] == cur_dn) & 
        (st.session_state.df['Distance'].between(cur_dist-2, cur_dist+2)) &
        (st.session_state.df['Hash'] == cur_hash)
    ]
    
    if not results.empty:
        summary = results.groupby('Play_Name').agg({
            'Success': 'mean',
            'Gain': 'mean',
            'Play_Name': 'count'
        }).rename(columns={'Play_Name': 'Calls', 'Success': 'Success %', 'Gain': 'Avg Gain'})
        
        # Formatting for readability
        summary['Success %'] = (summary['Success %'] * 100).astype(int)
        st.dataframe(summary.sort_values('Success %', ascending=False), use_container_width=True)
    else:
        st.info(f"No data for {cur_dn} & {cur_dist} from the {cur_hash} hash.")

with st.expander("View Raw Play History"):
    st.dataframe(st.session_state.df, use_container_width=True)
  
