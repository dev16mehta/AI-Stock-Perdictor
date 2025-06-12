import streamlit as st
import sys
import os
import pandas as pd

# --- Authentication Guard & Path Setup ---
if not st.session_state.get("logged_in", False):
    st.error("You need to log in to access this page.")
    st.stop()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.portfolio_manager import get_portfolio, get_live_prices, remove_from_portfolio

# --- Page Configuration ---
st.set_page_config(page_title="My Portfolio", page_icon="💼", layout="wide")

st.markdown(f" # My Portfolio")
st.caption("Track the value and performance of your stock holdings.")
st.divider()

# --- State & Data Loading ---
uid = st.session_state.get('uid')
# st.write(f"UID: {uid}")  # DEBUG: Show the current user ID
portfolio_holdings = get_portfolio(uid)
# st.write(portfolio_holdings)  # DEBUG: Show the raw portfolio holdings

# --- Display Portfolio ---
if not portfolio_holdings:
    st.info("Your portfolio is empty. Add holdings from the 'Detailed Analysis' tab on the Analyser page.")
else:
    # --- Create DataFrame from holdings ---
    df = pd.DataFrame(portfolio_holdings)
    
    # --- Get live prices for all tickers in the portfolio ---
    unique_tickers = df['ticker'].unique().tolist()
    with st.spinner("Fetching live market prices..."):
        live_prices = get_live_prices(unique_tickers)

    # --- Calculations ---
    df['Current Price'] = df['ticker'].map(live_prices).fillna(0)
    df['Cost Basis'] = df['shares'] * df['purchase_price']
    df['Market Value'] = df['shares'] * df['Current Price']
    df['P/L'] = df['Market Value'] - df['Cost Basis']
    
    # --- Display Summary Metrics ---
    total_market_value = df['Market Value'].sum()
    total_cost_basis = df['Cost Basis'].sum()
    total_pl = df['P/L'].sum()
    
    st.header("Portfolio Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Market Value", f"${total_market_value:,.2f}")
    col2.metric("Total Cost Basis", f"${total_cost_basis:,.2f}")
    
    pl_color = "normal" if total_pl >= 0 else "inverse"
    col3.metric("Total Profit/Loss", f"${total_pl:,.2f}", delta_color=pl_color)
    st.divider()

    # --- Display Holdings Table ---
    st.header("Your Holdings")
    
    # Format the DataFrame for display
    df_display = df[['ticker', 'shares', 'purchase_price', 'Cost Basis', 'Current Price', 'Market Value', 'P/L']].copy()
    df_display.rename(columns={'ticker': 'Ticker', 'shares': 'Shares', 'purchase_price': 'Avg. Purchase Price'}, inplace=True)
    
    st.dataframe(
        df_display, 
        use_container_width=True,
        column_config={
            "Avg. Purchase Price": st.column_config.NumberColumn(format="$%.2f"),
            "Cost Basis": st.column_config.NumberColumn(format="$%.2f"),
            "Current Price": st.column_config.NumberColumn(format="$%.2f"),
            "Market Value": st.column_config.NumberColumn(format="$%.2f"),
            "P/L": st.column_config.NumberColumn(format="$%.2f"),
        }
    )

    # --- Section to Remove Holdings ---
    st.subheader("Manage Holdings")
    selected_holding_id = st.selectbox(
        "Select a holding to remove:", 
        options=[(f"{h['ticker']} - {h['shares']} shares", h['id']) for h in portfolio_holdings],
        format_func=lambda x: x[0],
        index=None,
        placeholder="Choose a holding..."
    )

    if selected_holding_id:
        if st.button("❌ Remove Selected Holding", type="primary"):
            if remove_from_portfolio(uid, selected_holding_id[1]):
                st.success("Holding removed successfully!")
                st.rerun()
            else:
                st.error("Failed to remove holding.")

