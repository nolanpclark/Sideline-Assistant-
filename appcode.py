import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sideline Play-Finder", layout="wide")

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()

def load_hudl(file):
    try:
        raw = pd.read_excel(file, header=None) if file.name.endswith('.xlsx') else pd.read_csv(file, header=None)
        
        header_idx = 0
        for i, row in raw.iterrows():
            if "DN" in [str(v).strip().upper() for v in row.values]:
                header_idx = i
                break
        
        data = raw.iloc[header_idx:].copy()
        data.columns = data.iloc[0].str.strip().str.upper() 
        data = data[1:] 
        
        final = pd.DataFrame()
        # Clean numeric data to ensure math works for suggestions
        final['DN'] = pd.to_numeric(data.get('DN', pd.Series()).astype(str).str.extract('(\d+)', expand=False), errors='coerce')
        final['DIST'] = pd.to_numeric(data.get('DIST', pd.Series()).astype(str).str.extract('(\d+)', expand=False), errors='coerce')
        final['HASH'] = data.get('HASH', pd.Series()).fillna('M').astype(str).str.strip().str.upper()
        final['PLAY'] = data.get('OFF PLAY', pd.Series()).astype(str)
        final['GAIN'] = pd.to_numeric(data.get('GN/LS', pd.Series()).astype(str).str.extract('([-+]?\d+)', expand=False), errors='coerce')
        
        return final.dropna(subset=['DN'])
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

# Split screen into Inputs and Suggestions
col_input, col_suggest = st.columns([1, 2])

with col_input:
    st.subheader("Current Situation")
    ui_dn = st.selectbox("Down", [1, 2, 3, 4])
    ui_dist = st.slider("Distance", 0, 15, 10)
    ui_hash = st.radio("Hash", ["L", "M", "R"], horizontal=True)

with col_suggest:
    st.subheader("🔥 Top 3 Suggested Plays")
    if not st.session_state.df.empty:
        # Filter data based on user input
        match = st.session_state.df[
            (st.session_state.df['DN'] == ui_dn) & 
            (st.session_state.df['HASH'] == ui_hash) &
            (st.session_state.df['DIST'].between(ui_dist-2, ui_dist+2))
        ]
        
        if not match.empty:
            # Group by Play Name and calculate the Average Gain
            summary = match.groupby('PLAY').agg({'GAIN': ['mean', 'count']})
            summary.columns = ['Avg Gain', 'Times Run']
            
            # Sort by highest gain and show top 3
            top_3 = summary.sort_values(by='Avg Gain', ascending=False).head(3)
            st.table(top_3)
        else:
            st.info("No plays found for this specific situation. Try adjusting the distance slider.")
    else:
        st.warning("Upload a file in the sidebar to see suggestions.")

st.divider()

# Optional: Keep the detailed list at the bottom
if not st.session_state.df.empty:
    with st.expander("View All Matching Plays"):
        match_full = st.session_state.df[
            (st.session_state.df['DN'] == ui_dn) & 
            (st.session_state.df['HASH'] == ui_hash)
        ]
        st.dataframe(match_full.sort_values(by='GAIN', ascending=False))
