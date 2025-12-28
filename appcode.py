import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sideline Assistant", layout="wide")

# 1. Initialize Database
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=['DN', 'DIST', 'HASH', 'OFF PLAY', 'GN/LS'])

# 2. Simplified Hudl Loader
def process_hudl(file):
    try:
        data = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        # Clean headers to match your file exactly
        data.columns = data.columns.str.strip().str.upper()
        
        # We only keep the columns you specifically care about
        needed = ['DN', 'DIST', 'HASH', 'OFF PLAY', 'GN/LS']
        # Filter data to only include these 5 columns
        subset = data[[c for c in needed if c in data.columns]]
        
        # Standardize HASH values (L/M/R -> Left/Middle/Right)
        if 'HASH' in subset.columns:
            h_map = {'L': 'Left', 'M': 'Middle', 'R': 'Right'}
            subset['HASH'] = subset['HASH'].astype(str).str.strip().str.upper().map(h_map).fillna('Middle')
            
        return subset.dropna(subset=['DN'])
    except Exception as e:
        st.error(f"Excel Error: {e}")
        return None

# 3. Sidebar Tools
with st.sidebar:
    st.header("Upload Game")
    uploaded_file = st.file_uploader("Hudl Excel", type=['xlsx', 'csv'])
    if uploaded_file:
        df_new = process_hudl(uploaded_file)
        if df_new is not None:
            st.session_state.df = df_new
            st.success("Loaded!")

# 4. Main App Interface
st.title("🏈 Play-Call Finder")

col1, col2, col3 = st.columns(3)
with col1:
    ui_dn = st.pills("Down", [1, 2, 3, 4], default=1)
with col2:
    ui_dist = st.slider("Distance", 0, 15, 10)
with col3:
    ui_hash = st.segmented_control("Hash", ["Left", "Middle", "Right"], default="Middle")

st.divider()

# 5. Matching & Result Finding
if not st.session_state.df.empty:
    # Filter the data based on your buttons
    match = st.session_state.df[
        (st.session_state.df['DN'] == ui_dn) & 
        (st.session_state.df['DIST'].between(ui_dist-2, ui_dist+2)) &
        (st.session_state.df['HASH'] == ui_hash)
    ]
    
    if not match.empty:
        st.subheader("Plays with Highest Yardage")
        # Sort by GN/LS (Yards Gained) to find the biggest plays
        top_plays = match.sort_values(by='GN/LS', ascending=False)
        st.dataframe(top_plays[['OFF PLAY', 'GN/LS', 'DN', 'DIST']], use_container_width=True, hide_index=True)
    else:
        st.info("No plays found for this specific DN/DIST/HASH combination.")
else:
    st.warning("Please upload a Hudl Excel file in the sidebar to begin.")
