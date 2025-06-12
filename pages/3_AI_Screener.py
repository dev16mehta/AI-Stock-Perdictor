import streamlit as st
import sys
import os
import pandas as pd

# --- Authentication Guard & Path Setup ---
if not st.session_state.get("logged_in", False):
    st.error("You need to log in to access this page.")
    st.stop()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.screener import run_ai_screener

# --- Page Configuration ---
st.set_page_config(page_title="AI Stock Screener", page_icon="🤖", layout="wide")

st.markdown(f" # AI Stock Screener")
st.caption("Use plain simple english to find stocks based on fundamental criteria!")
st.divider()

# --- Screener UI ---
st.info("Example prompts: 'Find tech stocks with a P/E ratio below 25' or 'Show me profitable companies with low debt'", icon="💡")

prompt = st.text_input(
    "Enter your screening criteria:",
    placeholder="e.g., Profitable healthcare companies with high revenue growth"
)

if st.button("Screen Stocks", type="primary"):
    if prompt:
        with st.spinner("Running AI screener... This may take a moment as it processes data for multiple stocks."):
            summary, results_df = run_ai_screener(prompt)
        
        st.success(summary)
        
        if not results_df.empty:
            st.dataframe(results_df, use_container_width=True)
        else:
            st.warning("No stocks in the S&P 500 sample matched your criteria.")
    else:
        st.warning("Please enter your criteria in the text box above.")

