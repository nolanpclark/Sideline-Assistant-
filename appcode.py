import streamlit as st
import pandas as pd

st.set_page_config(page_title="Offensive Assistant", layout="wide")

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()

def load_hudl(file):
    try:
        raw = pd.read_excel(file, header=None) if file.name.endswith('.xlsx') else pd.read_csv(file, header=None)
        
        # 1. Find the header row
        header_idx = 0
        for i, row in raw.iterrows():
            if "DN" in [str(v).strip().upper() for v in row.values]:
                header_idx = i
                break
        
        data = raw.iloc[header_idx:].copy()
        data.columns = data.iloc[0].str.strip().str.upper()
        data = data[1:]
        
        # 2. Aggressive Data Extraction
        final = pd.DataFrame()
        # Extract numbers only to bypass 'D' or 'K' suffixes in your file
        final['DN'] = pd.to_numeric(data.get('DN').astype(str).str.extract('(\d+)', expand=False), errors='coerce')
        final['DIST'] = pd.to_numeric(data.get('DIST').astype(str).str.extract('(\d+)', expand=False), errors='coerce')
        final['HASH'] = data.get('HASH').astype(str).str.strip().str.upper()
        # Use 'OFF PLAY' column for the play name
        final['PLAY'] = data.get('OFF PLAY', data.get('PLAY TYPE')).astype(str)
        # Extract numeric Gain (handles negative yardage)
        final['GAIN'] = pd.to_numeric(data.get('GN/LS').astype(str).str.extract('([-+]?\d+)', expand=False), errors='coerce')
        
        return final.dropna(subset=['DN'])
    except Exception as e:
        st.error(f"Excel Error: {e}")
        return None

# --- Sidebar ---
with st.sidebar:
    st.header("📂 Data Import")
    uploaded_file = st.file_uploader("Upload Hudl Excel", type=['xlsx', 'csv'])
    if uploaded_file:
        data = load_hudl(uploaded_file)
        if data is not None:
            st.session_state.df = data
            st.success("File Loaded!")

# --- Main App ---
st.title("🏈 Offensive Play-Call Assistant")

col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("Situation")
    # Match buttons to L, M, R as seen in your spreadsheet
    ui_dn = st.pills("Down", [1, 2, 3, 4], default=1)
    ui_hash = st.segmented_control("Hash", ["L", "M", "R"], default="M")
    ui_dist = st.slider("Distance", 0, 20, 10)

with col_right:
    st.subheader("Statistical Suggestions")
    if not st.session_state.df.empty:
        # APPROACH: Filter by Down and Hash first (the most reliable data)
        match = st.session_state.df[
            (st.session_state.df['DN'] == ui_dn) & 
            (st.session_state.df['HASH'] == ui_hash)
        ]
        
        # Then, prioritize Distance if we have it
        dist_match = match[match['DIST'].between(ui_dist - 2, ui_dist + 2)]
        
        # If distance matches exist, show those. Otherwise, show all plays for that Down.
        display_data = dist_match if not dist_match.empty else match
        
        if not display_data.empty:
            # Group by play name and show the top 3 by average gain
            stats = display_data.groupby('PLAY').agg({'GAIN': 'mean', 'PLAY': 'count'})
            stats.columns = ['Avg Gain', 'Count']
            st.table(stats.sort_values(by='Avg Gain', ascending=False).head(3))
        else:
            st.info(f"No {ui_dn} Down plays found from the {ui_hash} hash.")
    else:
        st.info("Upload your Excel in the sidebar to populate plays.")

st.divider()

# --- Verification Table ---
if not st.session_state.df.empty:
    with st.expander("🔍 Click to see all plays for this Down/Hash"):
        st.dataframe(match.sort_values(by='GAIN', ascending=False))
