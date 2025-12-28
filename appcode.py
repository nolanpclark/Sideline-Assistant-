import streamlit as st
import pandas as pd
import os
import glob

st.set_page_config(page_title="Season Play-Finder", layout="wide")

# --- Step 1: Set up Persistent Storage Folder ---
SAVE_DIR = "Season_Data"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# --- Step 2: Improved Loader ---
def load_hudl(file_source, is_path=False):
    try:
        # Load from path (saved file) or UploadedFile object
        if is_path:
            raw = pd.read_excel(file_source, header=None) if file_source.endswith('.xlsx') else pd.read_csv(file_source, header=None)
        else:
            raw = pd.read_excel(file_source, header=None) if file_source.name.endswith('.xlsx') else pd.read_csv(file_source, header=None)
        
        header_idx = 0
        for i, row in raw.iterrows():
            if "DN" in [str(v).strip().upper() for v in row.values]:
                header_idx = i
                break
        
        data = raw.iloc[header_idx:].copy()
        data.columns = data.iloc[0].str.strip().str.upper() 
        data = data[1:] 
        
        final = pd.DataFrame()
        def clean_to_num(series):
            return pd.to_numeric(series.astype(str).str.extract('([-+]?\d+)', expand=False), errors='coerce')

        final['DN'] = clean_to_num(data.get('DN', pd.Series()))
        final['DIST'] = clean_to_num(data.get('DIST', pd.Series()))
        final['HASH'] = data.get('HASH', pd.Series()).fillna('M').astype(str).str.strip().str.upper()
        final['PLAY'] = data.get('OFF PLAY', pd.Series()).astype(str).str.strip()
        final['GAIN'] = clean_to_num(data.get('GN/LS', pd.Series()))
        
        return final.dropna(subset=['DN', 'PLAY'])
    except Exception as e:
        return None

# --- Step 3: Automatic Season Sync ---
def sync_season():
    all_games = []
    # Find every excel/csv file in the Season_Data folder
    files = glob.glob(os.path.join(SAVE_DIR, "*.xlsx")) + glob.glob(os.path.join(SAVE_DIR, "*.csv"))
    for f in files:
        game_data = load_hudl(f, is_path=True)
        if game_data is not None:
            all_games.append(game_data)
    
    if all_games:
        return pd.concat(all_games, ignore_index=True)
    return pd.DataFrame()

# Initialize Season Data
st.session_state.df = sync_season()

# --- SIDEBAR: Multi-File Upload & Storage ---
with st.sidebar:
    st.header("🏈 Season Manager")
    # Allow multiple files at once
    new_files = st.file_uploader("Upload New Game(s)", type=['xlsx', 'csv'], accept_multiple_files=True)
    
    if new_files:
        for f in new_files:
            # Save the file to the local folder permanently
            save_path = os.path.join(SAVE_DIR, f.name)
            with open(save_path, "wb") as buffer:
                buffer.write(f.getbuffer())
        
        st.success(f"Saved {len(new_files)} new game(s) to Season Memory!")
        # Refresh the master database
        st.session_state.df = sync_season()

    if st.button("🗑️ Clear All Season Data"):
        for f in glob.glob(os.path.join(SAVE_DIR, "*")):
            os.remove(f)
        st.session_state.df = pd.DataFrame()
        st.rerun()

    st.info(f"Currently tracking {len(glob.glob(os.path.join(SAVE_DIR, '*')))} games.")

# --- MAIN APP INTERFACE (Same as before) ---
st.title("🏈 Season-Wide Play-Finder")

col_ui, col_stats = st.columns([1, 2])
with col_ui:
    st.subheader("Current Situation")
    ui_dn = st.selectbox("Down", [1, 2, 3, 4], index=0)
    ui_dist = st.slider("Distance", 0, 20, 10)
    ui_hash = st.radio("Hash", ["L", "M", "R"], horizontal=True, index=1)

with col_stats:
    st.subheader("🔥 Top 3 Suggested Plays (Season Avg)")
    if not st.session_state.df.empty:
        match = st.session_state.df[
            (st.session_state.df['DN'] == ui_dn) & 
            (st.session_state.df['HASH'] == ui_hash) &
            (st.session_state.df['DIST'].between(ui_dist - 3, ui_dist + 3))
        ]
        
        if not match.empty:
            summary = match.groupby('PLAY').agg({'GAIN': ['mean', 'count']})
            summary.columns = ['Avg Gain', 'Times Run']
            st.table(summary.sort_values(by='Avg Gain', ascending=False).head(3))
        else:
            st.info("No plays found for this situation in your season history.")
    else:
        st.info("Upload your games in the sidebar to build your season database.")
