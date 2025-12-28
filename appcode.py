import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sideline Play-Finder", layout="wide")

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()

def load_hudl(file):
    try:
        # 1. Read the excel file
        # header=None helps us find the headers manually if they aren't on Row 1
        raw = pd.read_excel(file, header=None) if file.name.endswith('.xlsx') else pd.read_csv(file, header=None)
        
        # 2. Locate the row that contains 'DN'
        header_idx = 0
        for i, row in raw.iterrows():
            if "DN" in [str(v).strip().upper() for v in row.values]:
                header_idx = i
                break
        
        # 3. Re-load from that specific row
        data = raw.iloc[header_idx:].copy()
        data.columns = data.iloc[0].str.strip().str.upper() # Clean the headers
        data = data[1:] # Drop the header row itself from the data
        
        # 4. Map directly to your screenshot's column names
        final = pd.DataFrame()
        # Using .get() with a default empty series to prevent the 'NoneType' error
        final['DN'] = pd.to_numeric(data.get('DN', pd.Series()), errors='coerce')
        final['DIST'] = pd.to_numeric(data.get('DIST', pd.Series()), errors='coerce')
        final['HASH'] = data.get('HASH', pd.Series()).fillna('M').astype(str).str.strip().str.upper()
        final['PLAY'] = data.get('OFF PLAY', pd.Series()).astype(str)
        final['GAIN'] = pd.to_numeric(data.get('GN/LS', pd.Series()), errors='coerce')
        
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
with c2: ui_dist = st.slider("Distance", 0, 15, 10)
with c3: ui_hash = st.radio("Hash", ["L", "M", "R"], horizontal=True)

st.divider()

if not st.session_state.df.empty:
    # Match the buttons to your Excel columns
    results = st.session_state.df[
        (st.session_state.df['DN'] == ui_dn) & 
        (st.session_state.df['DIST'].between(ui_dist-2, ui_dist+2)) &
        (st.session_state.df['HASH'] == ui_hash)
    ]
    
    if not results.empty:
        st.subheader(f"Best Plays for {ui_dn} & {ui_dist} from {ui_hash} Hash")
        # Sort by the largest gains (GN/LS column)
        st.table(results.sort_values(by='GAIN', ascending=False).head(10))
    else:
        st.info("No plays found for this specific situation.")
else:
    st.warning("Please upload your Hudl Excel in the sidebar.")
