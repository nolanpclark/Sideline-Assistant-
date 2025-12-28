import streamlit as st
import pandas as pd

st.set_page_config(page_title="Offensive Play-Call Assistant", layout="wide")

# Initialize the Database
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()

def load_hudl(file):
    try:
        # Read file without assuming header location
        raw = pd.read_excel(file, header=None) if file.name.endswith('.xlsx') else pd.read_csv(file, header=None)
        
        # FIND THE HEADER: Look for the row containing 'DN' as seen in Screenshot 122738
        header_idx = 0
        for i, row in raw.iterrows():
            if "DN" in [str(v).strip().upper() for v in row.values]:
                header_idx = i
                break
        
        # Process the data from that row forward
        data = raw.iloc[header_idx:].copy()
        data.columns = data.iloc[0].str.strip().str.upper()
        data = data[1:].reset_index(drop=True)
        
        # CLEANING: Map your specific columns to a clean table
        final = pd.DataFrame()
        # Extract numbers only to remove 'D' or 'K' seen in Screenshot 122817
        final['DN'] = pd.to_numeric(data['DN'].astype(str).str.extract('(\d+)', expand=False), errors='coerce')
        final['DIST'] = pd.to_numeric(data['DIST'].astype(str).str.extract('(\d+)', expand=False), errors='coerce')
        # Map Hash (L, M, R) directly
        final['HASH'] = data['HASH'].astype(str).str.strip().str.upper()
        # Match Play Name from 'OFF PLAY' column
        final['PLAY'] = data['OFF PLAY'].astype(str).str.strip()
        # Extract numeric yardage from 'GN/LS'
        final['GAIN'] = pd.to_numeric(data['GN/LS'].astype(str).str.extract('([-+]?\d+)', expand=False), errors='coerce')
        
        return final.dropna(subset=['DN'])
    except Exception as e:
        st.error(f"Excel Error: {e}")
        return None

# --- SIDEBAR: The section that successfully uploaded in Screenshot 130529 ---
with st.sidebar:
    st.header("📂 Team Tools")
    uploaded_file = st.file_uploader("Upload Hudl Excel", type=['xlsx', 'csv'])
    if uploaded_file:
        data = load_hudl(uploaded_file)
        if data is not None:
            st.session_state.df = data
            st.success("Loaded Successfully!") # This is the confirmation you saw earlier

# --- MAIN DASHBOARD ---
st.title("🏈 Offensive Play-Call Assistant")

col_ui, col_stats = st.columns([1, 2])

with col_ui:
    st.subheader("Current Situation")
    ui_dn = st.selectbox("Current Down", [1, 2, 3, 4], index=0)
    ui_dist = st.slider("Distance to Go", 0, 20, 10)
    # Buttons match the L, M, R used in your file (Screenshot 122817)
    ui_hash = st.radio("Hash Marker", ["L", "M", "R"], horizontal=True, index=1)

with col_stats:
    st.subheader("Statistical Suggestions")
    if not st.session_state.df.empty:
        # FILTER: Down and Hash must match. Distance allows a 3-yard buffer for more results.
        results = st.session_state.df[
            (st.session_state.df['DN'] == ui_dn) & 
            (st.session_state.df['HASH'] == ui_hash) &
            (st.session_state.df['DIST'].between(ui_dist - 3, ui_dist + 3))
        ]
        
        if not results.empty:
            # Group by Play Name and show Top 3 by Average Gain
            summary = results.groupby('PLAY').agg({'GAIN': 'mean', 'PLAY': 'count'})
            summary.columns = ['Avg Gain', 'Times Called']
            st.table(summary.sort_values(by='Avg Gain', ascending=False).head(3))
        else:
            st.info(f"No plays found for {ui_dn} Down around {ui_dist} yards.")
    else:
        st.info("Upload your Hudl data in the sidebar to populate suggestions.")

st.divider()

# DEBUG: Shows you what the app is actually reading
if not st.session_state.df.empty:
    with st.expander("🔍 View Processed Data"):
        st.dataframe(st.session_state.df.head(20))
