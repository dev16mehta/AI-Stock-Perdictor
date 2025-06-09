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
    #My Watchlist
    *Welcome back, {st.session_state.get('email', 'Investor')}!*
""")
st.divider()

# --- State & Helper Functions ---
uid = st.session_state.get('uid')

# Load the watchlist from Firestore
try:
    watchlist = get_watchlist(uid)
except Exception as e:
    st.error(f"Could not load watchlist: {e}")
    watchlist = []

# --- Display Watchlist ---
if not watchlist:
    st.info("Your watchlist is empty. Go to the Analyser to add stocks!")
else:
    st.success(f"You are watching {len(watchlist)} stock(s).")
    
    # Use a dictionary to store stock data to avoid re-fetching on every interaction
    if 'watchlist_data' not in st.session_state:
        st.session_state.watchlist_data = {}

    # Fetch data for any new stocks in the watchlist
    with st.spinner("Loading watchlist data..."):
        for ticker in watchlist:
            if ticker not in st.session_state.watchlist_data:
                today = date.today()
                # Fetch only a small amount of data for the last price
                stock_info, stock_hist = get_stock_data(ticker, start_date=(today - timedelta(days=5)), end_date=today)
                if stock_info and not stock_hist.empty:
                    st.session_state.watchlist_data[ticker] = {
                        'info': stock_info.info,
                        'price': stock_hist['Close'].iloc[-1]
                    }

    # Display each stock in the watchlist
    for ticker in watchlist:
        if ticker in st.session_state.watchlist_data:
            data = st.session_state.watchlist_data[ticker]
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.subheader(data['info'].get('longName', ticker))
                st.caption(ticker)
            
            with col2:
                st.metric("Last Price", f"${data['price']:,.2f}")
            
            with col3:
                market_cap = data['info'].get('marketCap', 0)
                st.metric("Market Cap", f"${market_cap / 1e9:,.2f}B")

            with col4:
                # The 'key' is crucial to make each button unique
                if st.button("❌ Remove", key=f"remove_{ticker}"):
                    remove_from_watchlist(uid, ticker)
                    # Clear the cached data for the removed stock
                    if ticker in st.session_state.watchlist_data:
                        del st.session_state.watchlist_data[ticker]
                    st.rerun() # Rerun the page to reflect the change

            st.divider()
