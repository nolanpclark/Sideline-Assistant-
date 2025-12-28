import streamlit as st
import pandas as pd

st.set_page_config(page_title="Play-Call Finder", layout="wide")

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()

def load_hudl(file):
    try:
        # Load the raw data without assuming where the headers are
        raw = pd.read_excel(file, header=None) if file.name.endswith('.xlsx') else pd.read_csv(file, header=None)
        
        # --- NEW LOGIC: FIND THE HEADER ROW ---
        header_row_index = 0
        for i, row in raw.iterrows():
            # Search for 'DN' or 'DIST' in the row to find the start of the data
            if any("DN" in str(val).upper() for val in row.values):
                header_row_index = i
                break
        
        # Re-read the file starting from the correct row
        data = raw.iloc[header_row_index:].copy()
        data.columns = data.iloc[0].str.strip().str.upper() # Set headers
        data = data[1:] # Remove the header row from the data
        
        # --- EXTRACT DATA PIECE BY PIECE ---
        final = pd.DataFrame()
        # We use .get() so the app doesn't crash if a column is missing
        final['DN'] = pd.to_numeric(data.get('DN'), errors='coerce')
        final['DIST'] = pd.to_numeric(data.get('DIST'), errors='coerce')
        final['HASH'] = data.get('HASH').astype(str).str.strip().str.upper()
        final['PLAY'] = data.get('OFF PLAY').astype(str)
        final['GAIN'] = pd.to_numeric(data.get('GN/LS'), errors='coerce')
        
        return final.dropna(subset=['DN'])
    except Exception as e:
        st.error(f"Excel Error: {e}")
        return None

with st.sidebar:
    st.header("Upload Game")
    uploaded_file = st.file_uploader("Hudl Excel", type=['xlsx', 'csv'])
    if uploaded_file:
        data = load_hudl(uploaded_file)
        if data is not None:
            st.session_state.df = data
            st.success("File Loaded!")

st.title("🏈 Play-Call Finder")

c1, c2, c3 = st.columns(3)
with c1: ui_dn = st.selectbox("Down", [1, 2, 3, 4])
with c2: ui_dist = st.slider("Distance", 0, 15, 10)
with c3: ui_hash = st.radio("Hash", ["L", "M", "R"], horizontal=True)

st.divider()

if not st.session_state.df.empty:
    # Filter the data based on your buttons (L, M, R)
    results = st.session_state.df[
        (st.session_state.df['DN'] == ui_dn) & 
        (st.session_state.df['DIST'].between(ui_dist-2, ui_dist+2)) &
        (st.session_state.df['HASH'] == ui_hash)
    ]
    
    if not results.empty:
        st.subheader(f"Top Plays for {ui_dn} & {ui_dist}")
        # Show top 10 plays by GAIN (GN/LS)
        st.table(results.sort_values(by='GAIN', ascending=False).head(10))
    else:
        st.info("No plays found for this specific situation.")
else:
    st.warning("Please upload your Hudl Excel in the sidebar.")
