import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sideline Play-Finder", layout="wide")

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()

def load_hudl(file):
    try:
        # 1. Read the excel file
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
        
        # 4. Map directly to your screenshot's column names
        final = pd.DataFrame()
        # Cleaning numbers to remove 'D' or 'K' seen in Hudl files
        final['DN'] = pd.to_numeric(data.get('DN', pd.Series()).astype(str).str.extract('(\d+)', expand=False), errors='coerce')
        final['DIST'] = pd.to_numeric(data.get('DIST', pd.Series()).astype(str).str.extract('(\d+)', expand=False), errors='coerce')
        final['HASH'] = data.get('HASH', pd.Series()).fillna('M').astype(str).str.strip().str.upper()
        # Use 'OFF PLAY' or fallback to 'PLAY TYPE'
        final['PLAY'] = data.get('OFF PLAY', data.get('PLAY TYPE', pd.Series())).astype(str)
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

c1, c2, c3 = st.columns(3)
with c1: ui_dn = st.selectbox("Down", [1, 2, 3, 4])
with c2: ui_dist = st.slider("Distance", 0, 20, 10)
with c3: ui_hash = st.radio("Hash", ["L", "M", "R"], horizontal=True)

st.divider()

if not st.session_state.df.empty:
    st.subheader("Top 3 Suggested Plays")
    
    # FILTER LOGIC: Find anything for this Down and Hash
    match = st.session_state.df[
        (st.session_state.df['DN'] == ui_dn) & 
        (st.session_state.df['HASH'] == ui_hash)
    ]
    
    # NARROW SEARCH: Look for plays within +/- 2 yards of the slider
    results = match[match['DIST'].between(ui_dist-2, ui_dist+2)]
    
    # If no close distance match, show all plays for that Down/Hash
    display_data = results if not results.empty else match
    
    if not display_data.empty:
        # Group by play name and show the 3 with highest average gain
        summary = display_data.groupby('PLAY').agg({'GAIN': ['mean', 'count']})
        summary.columns = ['Avg Gain', 'Times Run']
        st.table(summary.sort_values(by='Avg Gain', ascending=False).head(3))
    else:
        st.info(f"No {ui_dn} down plays found from the {ui_hash} hash.")
else:
    st.warning("Please upload your Hudl Excel in the sidebar.")
