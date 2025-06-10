import streamlit as st
import sys
import os
from datetime import date, timedelta

# --- Authentication Guard & Path Setup ---
if not st.session_state.get("logged_in", False):
    st.error("You need to log in to access this page.")
    st.stop()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.data_handler import get_watchlist, get_stock_data, remove_from_watchlist

# --- Page Configuration ---
st.set_page_config(page_title="My Watchlist", page_icon="⭐", layout="wide")

st.markdown(f"""
    # ⭐ My Watchlist
    *Welcome back, {st.session_state.get('email', 'Investor')}!*
""")
st.divider()

# --- Callback Function ---
def handle_remove_from_watchlist(uid, ticker):
    """Callback to remove a stock from the watchlist page."""
    remove_from_watchlist(uid, ticker)
    if ticker in st.session_state.get('watchlist_data', {}):
        del st.session_state.watchlist_data[ticker]

# --- State & Data Loading ---
uid = st.session_state.get('uid')
watchlist = get_watchlist(uid)

# --- Display Watchlist ---
if not watchlist:
    st.info("Your watchlist is empty. Go to the Analyser to add stocks!")
else:
    st.success(f"You are watching {len(watchlist)} stock(s).")
    
    if 'watchlist_data' not in st.session_state:
        st.session_state.watchlist_data = {}

    with st.spinner("Loading watchlist data..."):
        today = date.today()
        for ticker in watchlist:
            if ticker not in st.session_state.watchlist_data:
                stock_info, stock_hist = get_stock_data(ticker, start_date=(today - timedelta(days=5)), end_date=today)
                if stock_info and not stock_hist.empty:
                    st.session_state.watchlist_data[ticker] = {
                        'info': stock_info.info,
                        'price': stock_hist['Close'].iloc[-1]
                    }

    # Display each stock using its own container
    for ticker in watchlist:
        if ticker in st.session_state.watchlist_data:
            data = st.session_state.watchlist_data[ticker]
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                col1.subheader(data['info'].get('longName', ticker))
                col1.caption(ticker)
                col2.metric("Last Price", f"${data['price']:,.2f}")
                col3.metric("Market Cap", f"${data['info'].get('marketCap', 0) / 1e9:,.2f}B")
                col4.button("❌ Remove", key=f"remove_watchlist_{ticker}", on_click=handle_remove_from_watchlist, args=(uid, ticker))
                st.divider()
