import streamlit as st
import pandas as pd

st.set_page_config(page_title="Offensive Play-Call Assistant", layout="wide")

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()

def load_hudl(file):
    try:
        raw = pd.read_excel(file, header=None) if file.name.endswith('.xlsx') else pd.read_csv(file, header=None)
        
        # 1. Find the header row by searching for 'DN'
        header_idx = 0
        for i, row in raw.iterrows():
            if "DN" in [str(v).strip().upper() for v in row.values]:
                header_idx = i
                break
        
        data = raw.iloc[header_idx:].copy()
        data.columns = data.iloc[0].str.strip().str.upper()
        data = data[1:]
        
        # 2. Extract and Clean Data
        final = pd.DataFrame()
        # Extract only numbers (removes 'D' or 'K' suffixes)
        final['DN'] = pd.to_numeric(data.get('DN').astype(str).str.extract('(\d+)', expand=False), errors='coerce')
        final['DIST'] = pd.to_numeric(data.get('DIST').astype(str).str.extract('(\d+)', expand=False), errors='coerce')
        # Clean Hash to match L, M, R
        final['HASH'] = data.get('HASH').astype(str).str.strip().str.upper()
        # Match Play Name
        final['PLAY'] = data.get('OFF PLAY', data.get('PLAY TYPE', 'Unknown')).astype(str)
        # Extract Gain (handles negative numbers)
        final['GAIN'] = pd.to_numeric(data.get('GN/LS').astype(str).str.extract('([-+]?\d+)', expand=False), errors='coerce')
        
        return final.dropna(subset=['DN'])
    except Exception as e:
        st.error(f"Excel Error: {e}")
        return None

# --- Sidebar Tools ---
with st.sidebar:
    st.header("📂 Team Tools")
    uploaded_file = st.file_uploader("Upload Hudl Excel", type=['xlsx', 'csv'])
    if uploaded_file:
        data = load_hudl(uploaded_file)
        if data is not None:
            st.session_state.df = data
            st.success("Loaded Successfully!")

# --- Main App Interface ---
st.title("🏈 Offensive Play-Call Assistant")

col_input, col_stats = st.columns([1, 2])

with col_input:
    st.subheader("Current Situation")
    ui_dn = st.selectbox("Current Down", [1, 2, 3, 4], index=0)
    ui_dist = st.slider("Distance to Go", 0, 20, 10)
    ui_hash = st.radio("Field Position (Hash)", ["L", "M", "R"], horizontal=True, index=1)

with col_stats:
    st.subheader("Statistical Suggestions")
    if not st.session_state.df.empty:
        # Filter: Exact match for Down/Hash, +/- 2 yard window for Distance
        results = st.session_state.df[
            (st.session_state.df['DN'] == ui_dn) & 
            (st.session_state.df['HASH'] == ui_hash) &
            (st.session_state.df['DIST'].between(ui_dist - 2, ui_dist + 2))
        ]
        
        if not results.empty:
            # Group and find top 3 plays by Average Gain
            summary = results.groupby('PLAY').agg({'GAIN': 'mean', 'PLAY': 'count'})
            summary.columns = ['Avg Gain', 'Times Called']
            st.table(summary.sort_values(by='Avg Gain', ascending=False).head(3))
        else:
            st.info(f"No plays found for {ui_dn} Down & {ui_dist} yds from the {ui_hash} hash.")
    else:
        st.info("Upload your Hudl Excel in the sidebar to see top-performing plays.")

st.divider()

# --- Debug Section ---
with st.expander("🔍 View Processed Play Data"):
    if not st.session_state.df.empty:
        st.dataframe(st.session_state.df.head(20))
