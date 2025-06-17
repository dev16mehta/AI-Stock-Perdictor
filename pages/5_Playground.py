import streamlit as st
import sys
import os
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time # Import time for logout sequence

# --- Authentication Guard & Path Setup ---
if not st.session_state.get("logged_in", False):
    st.error("You need to log in to access this page.")
    st.stop()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.playground_handler import get_playground_portfolio, execute_trade, generate_health_report
from backend.portfolio_manager import get_live_prices

# --- Page Configuration ---
st.set_page_config(page_title="Playground", page_icon="🎮", layout="wide")

# --- NEW: Logout Function ---
def logout():
    st.session_state.logged_in = False
    st.session_state.email = ""
    st.session_state.uid = ""
    st.success("You have been successfully logged out!")
    time.sleep(1.5)
    st.switch_page("landing.py")

# --- NEW: Sidebar with Logout Button ---
with st.sidebar:
    st.title("Account")
    st.write(f"Logged in as: {st.session_state.get('email')}")
    st.divider()
    st.button("Logout", key="logout_playground", on_click=logout, use_container_width=True)

# --- Custom CSS for Styling ---
st.markdown("""
<style>
    .st-emotion-cache-1y4p8pa { padding-top: 2rem; }
    .st-emotion-cache-1v0mbdj { border-radius: 12px; padding: 1.5rem; }
    [data-testid="stMetric"] { background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 1rem; }
    [data-testid="stMetricLabel"] { font-size: 1.1rem; font-weight: 600; color: #a0a0a0; }
    [data-testid="stMetricValue"] { font-size: 2.2rem; font-weight: 700; }
    .st-emotion-cache-1v0mbdj h3 { font-size: 1.5rem; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)


# --- Data Loading & Initialization ---
uid = st.session_state.get('uid')
with st.spinner("Loading your Playground..."):
    playground_portfolio = get_playground_portfolio(uid)

if playground_portfolio is None:
    st.error("Could not load your playground. Please try again later.")
    st.stop()

holdings_df = pd.DataFrame(playground_portfolio['holdings'])
if not holdings_df.empty:
    live_prices = get_live_prices(holdings_df['ticker'].unique().tolist())
    holdings_df['current_price'] = holdings_df['ticker'].map(live_prices).fillna(holdings_df['purchase_price'])
    holdings_df['market_value'] = holdings_df['shares'] * holdings_df['current_price']
    holdings_df['gain_loss'] = holdings_df['market_value'] - (holdings_df['shares'] * holdings_df['purchase_price'])
    total_stock_value = holdings_df['market_value'].sum()
else:
    total_stock_value = 0

total_portfolio_value = playground_portfolio['cash'] + total_stock_value
total_gain_loss = holdings_df['gain_loss'].sum() if not holdings_df.empty else 0

# --- Page Title & Header ---
st.markdown(" # 🎮 The Playground")
st.caption("Learn to invest with a $100,000 virtual portfolio. No real money involved!")
st.divider()

# --- Dashboard Metrics ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Portfolio Value", f"${total_portfolio_value:,.2f}")
col2.metric("Cash Balance", f"${playground_portfolio['cash']:,.2f}")
delta_color = "normal" if total_gain_loss >= 0 else "inverse"
col3.metric("Total P/L", f"${total_gain_loss:,.2f}", delta_color=delta_color)
st.markdown("<br>", unsafe_allow_html=True)

# --- Main Content (Trading Panel & Portfolio Info) ---
main_col1, main_col2 = st.columns([1, 1.2], gap="large")

# --- Trading Panel ---
with main_col1:
    with st.container(border=True):
        st.subheader("📈 Trade Stocks")
        ticker_input = st.text_input("Enter Stock Symbol (e.g., AAPL)", key="trade_ticker").upper()
        trade_assistant = st.empty()

        if ticker_input:
            try:
                stock_info = yf.Ticker(ticker_input).info
                company_name = stock_info.get('longName', 'N/A')
                current_price = stock_info.get('regularMarketPrice', 0)
                with trade_assistant.container(border=True):
                    logo_col, name_col = st.columns([1, 4])
                    if 'logo_url' in stock_info: logo_col.image(stock_info['logo_url'], width=50)
                    name_col.markdown(f"**{company_name}**")
                    name_col.markdown(f"**Current Price:** `${current_price:,.2f}`")
            except Exception:
                trade_assistant.warning("Could not fetch info for this symbol.")
                current_price = 0
        else:
            current_price = 0
        
        with st.form(key="trade_form"):
            action = st.radio("Action", ["Buy", "Sell"], horizontal=True)
            quantity = st.number_input("Quantity", min_value=1, step=1)
            
            if ticker_input and current_price > 0 and quantity > 0:
                estimated_cost = quantity * current_price
                st.info(f"Estimated Cost: **${estimated_cost:,.2f}**")
            
            submit_trade = st.form_submit_button(f"Submit {action} Order", use_container_width=True, type="primary")

            if submit_trade:
                if not ticker_input: st.error("Please enter a stock symbol.")
                elif quantity <= 0: st.error("Please enter a valid quantity.")
                else:
                    with st.spinner("Placing trade..."):
                        success, message = execute_trade(uid, ticker_input, quantity, current_price, action.lower())
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

# --- Portfolio Info & Health Report ---
with main_col2:
    tab1, tab2 = st.tabs(["Portfolio Composition", "AI Health Report"])

    with tab1:
        with st.container(border=True, height=450):
            st.subheader("📊 Composition")
            labels = ['Cash', 'Stocks']
            values = [playground_portfolio['cash'], total_stock_value]
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker_colors=['#4B8BBE', '#2ECC71'])])
            fig.update_layout(showlegend=True, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        with st.container(border=True, height=450):
            st.subheader("🤖 AI Health Report")
            if st.button("🔬 Analyze My Playground Health", use_container_width=True):
                st.session_state['report_generated'] = True
            
            if st.session_state.get('report_generated', False):
                with st.spinner("Generating your AI Health Report... This may take a moment."):
                    report, message = generate_health_report(uid, playground_portfolio, total_portfolio_value, total_stock_value)
                
                if report:
                    st.markdown(report['ai_analysis'])
                    st.divider()
                    st.write("**Sector Allocation**")
                    st.bar_chart(report['sector_allocation'])
                else:
                    st.warning(message)

# --- Holdings Display ---
st.markdown("<br>", unsafe_allow_html=True)
with st.container(border=True):
    st.subheader("💼 Your Virtual Holdings")
    if holdings_df.empty:
        st.info("You have no stock holdings yet. Buy a stock to get started!")
    else:
        display_df = holdings_df[['ticker', 'shares', 'purchase_price', 'current_price', 'market_value', 'gain_loss']].copy()
        display_df.rename(columns={'ticker': 'Ticker', 'shares': 'Shares', 'purchase_price': 'Avg. Cost', 'current_price': 'Current Price', 'market_value': 'Market Value', 'gain_loss': 'P/L'}, inplace=True)
        st.dataframe(display_df, use_container_width=True, column_config={"Avg. Cost": st.column_config.NumberColumn(format="$%.2f"),"Current Price": st.column_config.NumberColumn(format="$%.2f"), "Market Value": st.column_config.NumberColumn(format="$%.2f"), "P/L": st.column_config.NumberColumn(format="$%.2f")}, hide_index=True)