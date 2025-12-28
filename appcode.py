import streamlit as st
import pandas as pd

st.set_page_config(page_title="Play-Call Finder", layout="wide")

# 1. Setup the Database
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()

# 2. Simplest Possible Loader
def load_hudl(file):
    try:
        # Load the raw data
        raw = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        
        # Clean the headers: remove spaces and force Uppercase
        raw.columns = raw.columns.str.strip().str.upper()
        
        # Manually pick only what we need to avoid "Index" errors
        final = pd.DataFrame()
        final['DN'] = pd.to_numeric(raw['DN'], errors='coerce')
        final['DIST'] = pd.to_numeric(raw['DIST'], errors='coerce')
        final['HASH'] = raw['HASH'].astype(str).str.strip().str.upper()
        final['PLAY'] = raw['OFF PLAY'].astype(str)
        final['GAIN'] = pd.to_numeric(raw['GN/LS'], errors='coerce')
        
        return final.dropna(subset=['DN'])
    except Exception as e:
        st.error(f"Excel Error: {e}")
        return None

# 3. Sidebar
with st.sidebar:
    st.header("Upload Game")
    uploaded_file = st.file_uploader("Hudl Excel", type=['xlsx', 'csv'])
    if uploaded_file:
        data = load_hudl(uploaded_file)
        if data is not None:
            st.session_state.df = data
            st.success("File Loaded!")

# 4. Main App Interface
st.title("🏈 Play-Call Finder")

c1, c2, c3 = st.columns(3)
with c1: ui_dn = st.selectbox("Down", [1, 2, 3, 4])
with c2: ui_dist = st.slider("Distance", 0, 15, 10)
with c3: ui_hash = st.radio("Hash", ["L", "M", "R"], horizontal=True)

st.divider()

# 5. Matching & Result Finding
if not st.session_state.df.empty:
    # Match the Excel column names (DN, DIST, HASH) directly to the buttons
    results = st.session_state.df[
        (st.session_state.df['DN'] == ui_dn) & 
        (st.session_state.df['DIST'].between(ui_dist-2, ui_dist+2)) &
        (st.session_state.df['HASH'] == ui_hash)
    ]
    
    if not results.empty:
        st.subheader(f"Top Plays for {ui_dn} & {ui_dist}")
        # Sort by GAIN so the best plays are at the top
        st.table(results.sort_values(by='GAIN', ascending=False).head(10))
    else:
        st.info("No plays found for this specific situation.")
else:
    st.warning("Please upload your Hudl Excel in the sidebar.")
