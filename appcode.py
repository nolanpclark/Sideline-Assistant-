import streamlit as st
import pandas as pd
from docx import Document

# --- 1. SETUP & DATA ---
st.set_page_config(page_title="OC Sideline Assistant", layout="wide")

# This creates a "blank" database if you don't have one yet
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=['Down', 'Distance', 'Play_Name', 'Gain', 'Success'])

# --- 2. THE HUDL UPLOADER FUNCTION ---
def process_hudl(file):
    if file.name.endswith('.csv'):
        data = pd.read_csv(file)
    else:
        data = pd.read_excel(file)
    
    # Rename Hudl's "DN" and "DIST" to match our app
    clean = data.rename(columns={'DN': 'Down', 'DIST': 'Distance', 'OFF PLAY': 'Play_Name', 'GN/LS': 'Gain'})
    return clean[['Down', 'Distance', 'Play_Name', 'Gain']]

# --- 3. SIDEBAR TOOLS ---
with st.sidebar:
    st.header("📋 Admin Tools")   
with st.sidebar:
    st.header("📊 Data Tools")
    
    # This creates the button you're looking for
    hudl_file = st.file_uploader("Upload Hudl Excel", type=['csv', 'xlsx'])
    
    if hudl_file is not None:
        # Code to process the file
        hudl_df = pd.read_excel(hudl_file) if hudl_file.name.endswith('.xlsx') else pd.read_csv(hudl_file)
        
        # Mapping Hudl columns to your app (Adjust these if your Hudl names differ)
        hudl_df = hudl_df.rename(columns={'DN': 'Down', 'DIST': 'Distance', 'OFF PLAY': 'Play_Name', 'GN/LS': 'Gain'})
        
        # Add it to your main database
        st.session_state.df = pd.concat([st.session_state.df, hudl_df], ignore_index=True)
        st.success("Hudl Data Imported!")
    # Upload Hudl Export
    hudl_file = st.file_uploader("Upload Hudl CSV/Excel", type=['csv', 'xlsx'])
    if hudl_file:
        hudl_data = process_hudl(hudl_file)
        st.session_state.df = pd.concat([st.session_state.df, hudl_data], ignore_index=True)
        st.success("Hudl Data Imported!")

    st.divider()
    
    # Manual Logging (The "Hudl-style" manual entry)
    st.subheader("Log a Play")
    with st.form("manual_entry"):
        d = st.selectbox("Down", [1,2,3,4])
        dist = st.number_input("Distance", value=10)
        p = st.text_input("Play Name")
        g = st.number_input("Gain", value=0)
        if st.form_submit_button("Add Play"):
            new_row = pd.DataFrame([[d, dist, p, g, (1 if g >= dist else 0)]], 
                                   columns=['Down', 'Distance', 'Play_Name', 'Gain', 'Success'])
            st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)

# --- 4. THE OC DASHBOARD ---
st.title("🏈 Play-Call Recommendations")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Situation")
    now_dn = st.radio("Current Down", [1,2,3,4], horizontal=True)
    now_dist = st.slider("Distance to Go", 1, 20, 10)

with col2:
    st.subheader("What's Working?")
    # Simple Filter Logic
    situation_df = st.session_state.df[
        (st.session_state.df['Down'] == now_dn) & 
        (st.session_state.df['Distance'].between(now_dist-2, now_dist+2))
    ]
    
    if not situation_df.empty:
        stats = situation_df.groupby('Play_Name').agg({'Gain': 'mean', 'Down': 'count'})
        stats.columns = ['Avg Gain', 'Times Called']
        st.table(stats.sort_values('Avg Gain', ascending=False))
    else:
        st.info("No data for this situation yet. Log a play or upload Hudl data.")
