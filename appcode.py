import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sideline Play-Finder", layout="wide")

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()

def load_hudl(file):
    try:
        # 1. Use your working read logic
        raw = pd.read_excel(file, header=None) if file.name.endswith('.xlsx') else pd.read_csv(file, header=None)
        
        # 2. Locate the row that contains 'DN'
        header_idx = 0
        for i, row in raw.iterrows():
            if "DN" in [str(v).strip().upper() for v in row.values]:
                header_idx = i
                break
        
        # 3. Process data from the confirmed header row
        data = raw.iloc[header_idx:].copy()
        data.columns = data.iloc[0].str.strip().str.upper() 
        data = data[1:] 
        
        # 4. AGGRESSIVE CLEANING: Strip letters (like 'D' or 'K') so math works
        final = pd.DataFrame()
        
        def clean_to_num(series):
            # Keeps only numbers and minus signs
            return pd.to_numeric(series.astype(str).str.extract('([-+]?\d+)', expand=False), errors='coerce')

        final['DN'] = clean_to_num(data.get('DN', pd.Series()))
        final['DIST'] = clean_to_num(data.get('DIST', pd.Series()))
        final['HASH'] = data.get('HASH', pd.Series()).fillna('M').astype(str).str.strip().str.upper()
        final['PLAY'] = data.get('OFF PLAY', pd.Series()).astype(str).str.strip()
        final['GAIN'] = clean_to_num(data.get('GN/LS', pd.Series()))
        
        return final.dropna(subset=['DN', 'PLAY'])
    except Exception as e:
        st.error(f"Excel Error: {e}")
        return None

# --- Sidebar (Your Working Logic) ---
with st.sidebar:
    st.header("Upload Game")
    uploaded_file = st.file_uploader("Hudl Excel", type=['xlsx', 'csv'])
    if uploaded_file:
        data = load_hudl(uploaded_file)
        if data is not None:
            st.session_state.df = data
            st.success("Loaded Successfully!")

# --- Main App Interface ---
st.title("🏈 Sideline Play-Finder")

col_ui, col_stats = st.columns([1, 2])

with col_ui:
    st.subheader("Current Situation")
    ui_dn = st.selectbox("Down", [1, 2, 3, 4], index=0)
    ui_dist = st.slider("Distance", 0, 20, 10)
    ui_hash = st.radio("Hash", ["L", "M", "R"], horizontal=True, index=1)

with col_stats:
    st.subheader("🔥 Top 3 Suggested Plays")
    
    if not st.session_state.df.empty:
        # Step 1: Match Down and Hash exactly
        match = st.session_state.df[
            (st.session_state.df['DN'] == ui_dn) & 
            (st.session_state.df['HASH'] == ui_hash)
        ]
        
        # Step 2: Wider search for Distance (+/- 3 yards) to ensure results populate
        results = match[match['DIST'].between(ui_dist - 3, ui_dist + 3)]
        
        # Step 3: Fallback if distance is too specific
        display_data = results if not results.empty else match
        
        if not display_data.empty:
            # Group by Play and find the highest Average Gain
            summary = display_data.groupby('PLAY').agg({'GAIN': ['mean', 'count']})
            summary.columns = ['Avg Gain', 'Times Run']
            
            # Show top 3 by Gain
            st.table(summary.sort_values(by='Avg Gain', ascending=False).head(3))
        else:
            st.info(f"No {ui_dn} Down plays found for hash {ui_hash}.")
    else:
        st.info("Upload your Hudl Excel in the sidebar to see play suggestions.")

st.divider()

# DEBUG: Use this to see if the data is actually reaching the app's "brain"
if not st.session_state.df.empty:
    with st.expander("🔍 Debug: See Processed Data"):
        st.write("This is how the app reads your file after cleaning:")
        st.dataframe(st.session_state.df.head(20))
