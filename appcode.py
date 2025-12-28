import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Sideline Play-Finder", layout="wide")

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()

def load_hudl(file):
    try:
        # 1. Read the file using your working logic
        raw = pd.read_excel(file, header=None) if file.name.endswith('.xlsx') else pd.read_csv(file, header=None)
        
        # 2. Locate the row that contains 'DN'
        header_idx = 0
        for i, row in raw.iterrows():
            if "DN" in [str(v).strip().upper() for v in row.values]:
                header_idx = i
                break
        
        # 3. Re-load from that specific row
        data = raw.iloc[header_idx:].copy()
        data.columns = data.iloc[0].str.strip().str.upper() 
        data = data[1:] 
        
        # 4. Map directly to your columns with AGGRESSIVE cleaning
        final = pd.DataFrame()
        
        # Function to strip all non-numeric characters (handles "10 D", "4 K", etc)
        def clean_num(series):
            return pd.to_numeric(series.astype(str).str.extract('([-+]?\d+)', expand=False), errors='coerce')

        final['DN'] = clean_num(data.get('DN', pd.Series()))
        final['DIST'] = clean_num(data.get('DIST', pd.Series()))
        final['HASH'] = data.get('HASH', pd.Series()).fillna('M').astype(str).str.strip().str.upper()
        final['PLAY'] = data.get('OFF PLAY', pd.Series()).astype(str).str.strip()
        final['GAIN'] = clean_num(data.get('GN/LS', pd.Series()))
        
        # Remove empty rows but keep everything else
        return final.dropna(subset=['DN', 'PLAY'])
    except Exception as e:
        st.error(f"Excel Error: {e}")
        return None

# --- Sidebar ---
with st.sidebar:
    st.header("Upload Game")
    uploaded_file = st.file_uploader("Hudl Excel", type=['xlsx', 'csv'])
    if uploaded_file:
        data = load_hudl(uploaded_file)
        if data is not None:
            st.session_state.df = data
            st.success("Loaded Successfully!")

# --- Main App ---
st.title("🏈 Sideline Play-Finder")

col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("Current Situation")
    ui_dn = st.selectbox("Down", [1, 2, 3, 4], index=0)
    ui_dist = st.slider("Distance", 0, 20, 10)
    ui_hash = st.radio("Hash", ["L", "M", "R"], horizontal=True, index=1)

with col_right:
    st.subheader("🔥 Top 3 Suggested Plays")
    
    if not st.session_state.df.empty:
        # Step 1: Filter by Down and Hash
        match = st.session_state.df[
            (st.session_state.df['DN'] == ui_dn) & 
            (st.session_state.df['HASH'] == ui_hash)
        ]
        
        # Step 2: Narrow by Distance (using a wider window to ensure results)
        results = match[match['DIST'].between(ui_dist - 3, ui_dist + 3)]
        
        # Step 3: If distance is too specific, fall back to just Down/Hash
        final_view = results if not results.empty else match
        
        if not final_view.empty:
            # Step 4: Group and Sort by GAIN
            summary = final_view.groupby('PLAY').agg({'GAIN': ['mean', 'count']})
            summary.columns = ['Avg Gain', 'Times Run']
            
            # Show the top 3 with the highest GN/LS
            st.table(summary.sort_values(by='Avg Gain', ascending=False).head(3))
        else:
            st.info(f"No {ui_dn} Down plays found for hash {ui_hash} in the uploaded file.")
    else:
        st.info("Upload your Hudl Excel in the sidebar to see suggestions.")

st.divider()

# DEBUG: This will show you exactly what is inside the app's brain
if not st.session_state.df.empty:
    with st.expander("🔍 Debug: View Processed Data"):
        st.write("This is what the app 'sees' after cleaning your file:")
        st.dataframe(st.session_state.df.head(20))
