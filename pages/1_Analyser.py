import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta
import sys
import os

# --- Authentication Guard & Path Setup ---
if not st.session_state.get("logged_in", False):
    st.error("You need to log in to access this page.")
    st.stop()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.data_handler import get_stock_data, get_financial_news, get_watchlist, add_to_watchlist, remove_from_watchlist
from backend.ai_analyzer import analyze_sentiment, get_ai_summary, get_ai_comparison
from backend.predictor import get_price_prediction
from backend.technical_analyzer import add_technical_indicators
from backend.portfolio_manager import add_to_portfolio

# --- Page Configuration ---
st.set_page_config(page_title="QuantView AI Analyser", page_icon="📈", layout="wide")

# --- Callback & Helper Functions (These all remain the same) ---
def handle_add(uid, ticker):
    add_to_watchlist(uid, ticker)
    if 'watchlist' in st.session_state and ticker not in st.session_state.watchlist:
        st.session_state.watchlist.append(ticker)
    st.toast(f"Added {ticker} to your watchlist!", icon="⭐")

def handle_remove(uid, ticker):
    remove_from_watchlist(uid, ticker)
    if 'watchlist' in st.session_state and ticker in st.session_state.watchlist:
        st.session_state.watchlist.remove(ticker)
    st.toast(f"Removed {ticker} from your watchlist.", icon="🗑️")

def normalize_prices(df):
    """Normalizes the 'Close' price of a dataframe to start at 100."""
    return (df['Close'] / df['Close'].iloc[0]) * 100
    
def display_stock_details(container, ticker_data):
    st.info("Displaying Stock Details (DEBUG)") # NEW DEBUG MESSAGE
    uid = st.session_state.get('uid')
    ticker = ticker_data['ticker']
    is_in_watchlist = ticker in st.session_state.get('watchlist', [])

    col1_header, col2_header = container.columns([3, 1])
    col1_header.header(f"{ticker_data['info'].info.get('longName', ticker)}")

    if is_in_watchlist:
        col2_header.button("⭐ In Watchlist", key=f"remove_{ticker}", on_click=handle_remove, args=(uid, ticker), use_container_width=True)
    else:
        col2_header.button("➕ Add to Watchlist", key=f"add_{ticker}", on_click=handle_add, args=(uid, ticker), use_container_width=True, type="primary")

    sub_tabs = container.tabs(["📊 Key Metrics", "💬 News Sentiment", "💰 Financials", "📰 Recent News"])
    with sub_tabs[0]:
        if ticker_data['hist'].empty: 
            st.warning("No historical price data.")
        else:
            c1, c2 = st.columns(2)
            c1.metric("Last Close", f"${ticker_data['hist']['Close'].iloc[-1]:,.2f}")
            c2.metric("Market Cap", f"${ticker_data['info'].info.get('marketCap', 0) / 1e9:,.2f}B")
        st.divider()

        # --- NEW: "Add to Portfolio" Form ---
        st.subheader("Add to Portfolio")
        with st.form(key=f"add_portfolio_{ticker_data['ticker']}"):
            shares = st.number_input("Number of Shares", min_value=0.0, format="%.4f")
            purchase_price = st.number_input("Purchase Price per Share", min_value=0.0, format="%.2f")
            
            submitted = st.form_submit_button("Add Holding")
            if submitted:
                if shares > 0 and purchase_price > 0:
                    uid = st.session_state.get('uid')
                    if add_to_portfolio(uid, ticker_data['ticker'], shares, purchase_price):
                        st.success(f"Successfully added {shares} shares of {ticker_data['ticker']} to your portfolio!")
                        st.rerun() # Rerun to refresh portfolio immediately
                    else:
                        st.error("Failed to add holding to portfolio.")
                else:
                    st.warning("Please enter a valid number of shares and purchase price.")
    with sub_tabs[1]:
        st.metric("Sentiment Score", f"{ticker_data['sentiment']:.2f}")
    with sub_tabs[2]:
        st.write("**Income Statement**"); st.dataframe(ticker_data['info'].income_stmt.head())
        st.write("**Balance Sheet**"); st.dataframe(ticker_data['info'].balance_sheet.head())
    with sub_tabs[3]:
        if not ticker_data['news']: st.write("No recent news found.")
        else:
            for article in ticker_data['news'][:5]:
                if article and article.get('title'):
                    st.write(f"**{article['title']}**"); st.write(f"_{article.get('source', {}).get('name', 'Unknown Source')} - {pd.to_datetime(article.get('publishedAt')).strftime('%Y-%m-%d')}_")
                    st.markdown(f"[Read]({article.get('url')})", unsafe_allow_html=True); st.divider()

# --- Main App UI ---
st.markdown(f" # QuantView AI \n *Welcome, {st.session_state.get('email', 'Investor')}!*")
st.divider()

# --- Sidebar ---
with st.sidebar:
    st.header("Stock Selection")
    tickers_input = st.text_input("Enter stock(s) (e.g., AAPL,MSFT)", "TSLA").upper()
    
    st.header("AI Analysis Level")
    investor_level = st.selectbox("Choose your investor profile:", ("Beginner", "Advanced"))

    # --- ADVANCED MODE LOGIC: Only show these options if the user is 'Advanced' ---
    selected_indicators = []
    if investor_level == "Advanced":
        st.header("Chart Options")
        st.info("Technical analysis is best viewed for a single stock.")
        indicator_options = ["SMA 20", "SMA 50", "EMA 20", "Bollinger Bands", "RSI", "MACD", "OBV"]
        selected_indicators = st.multiselect("Select technical indicators:", indicator_options, default=["SMA 20", "SMA 50"])

    st.header("Date Range")
    today = date.today()
    start_date = st.date_input("Start Date", today - timedelta(days=730))
    end_date = st.date_input("End Date", today)
    
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = get_watchlist(st.session_state.get('uid'))
    
    analyze_button = st.button("Analyse Stock(s)", type="primary")

# --- Main Content Logic ---
if analyze_button:
    if start_date >= end_date:
        st.warning("The start date must be before the end date.")
        st.session_state['analysis_data'] = [] # Clear data if dates are invalid
    else:
        st.session_state.watchlist = get_watchlist(st.session_state.get('uid'))
        tickers = [ticker.strip() for ticker in tickers_input.split(',') if ticker.strip()]
        
        if not tickers:
            st.warning("Please enter at least one valid stock ticker.")
            st.session_state['analysis_data'] = [] # Clear data if no tickers
        else:
            all_data = []
            with st.spinner(f"Fetching and analysing {', '.join(tickers)}..."):
                for ticker in tickers:
                    stock_info, stock_hist = get_stock_data(ticker, start_date, end_date)
                    if stock_info:
                        # --- ADVANCED MODE LOGIC: Removed calculation here, now done before plotting ---
                        # if investor_level == "Advanced":
                        #     stock_hist = add_technical_indicators(stock_hist.copy())
                        
                        news = get_financial_news(ticker)
                        all_data.append({
                            "ticker": ticker, "info": stock_info, 
                            "hist": stock_hist,
                            "news": news, 
                            "sentiment": analyze_sentiment(news)
                        })
                    else:
                        st.error(f"Could not retrieve data for {ticker}.")
            
            st.session_state['analysis_data'] = all_data # Store fetched data

# Now, always display tabs if analysis_data exists
if st.session_state.get('analysis_data') and len(st.session_state['analysis_data']) > 0:
    all_data = st.session_state['analysis_data'] # Retrieve data
    
    # --- Tab Creation ---
    tab_list = ["Chart", "AI Insights", "Detailed Analysis", "Price Prediction"]
    main_tabs = st.tabs(tab_list)

    with main_tabs[0]: # Chart Tab
        # --- ADVANCED MODE LOGIC: Show different charts based on user level ---
        if investor_level == "Advanced":
            st.header(f"Advanced Chart for {all_data[0]['ticker']}")
            stock_df = all_data[0]['hist'].copy() # Use a copy to avoid modifying original session state data
            if not stock_df.empty:
                # Calculate technical indicators here, right before plotting
                stock_df = add_technical_indicators(stock_df)
                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])
                fig.add_trace(go.Candlestick(x=stock_df.index, open=stock_df['Open'], high=stock_df['High'],low=stock_df['Low'], close=stock_df['Close'], name='Price'), row=1, col=1)

                # Plot selected indicators on the main chart
                if "SMA 20" in selected_indicators: fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['SMA_20'], mode='lines', name='SMA 20', line=dict(width=1)), row=1, col=1)
                if "SMA 50" in selected_indicators: fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['SMA_50'], mode='lines', name='SMA 50', line=dict(width=1)), row=1, col=1)
                if "EMA 20" in selected_indicators: fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['EMA_20'], mode='lines', name='EMA 20', line=dict(width=1, dash='dash')), row=1, col=1)
                if "Bollinger Bands" in selected_indicators and 'BBU_20_2.0' in stock_df.columns:
                    fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['BBU_20_2.0'], line=dict(color='gray', width=0.5), name='Upper Band'), row=1, col=1)
                    fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['BBL_20_2.0'], line=dict(color='gray', width=0.5), fill='tonexty', fillcolor='rgba(128,128,128,0.1)', name='Lower Band'), row=1, col=1)
                
                if "MACD" in selected_indicators and 'MACD_12_26_9' in stock_df.columns:
                    fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['MACD_12_26_9'], name='MACD', line=dict(color='blue', width=1)), row=2, col=1)
                    fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['MACDs_12_26_9'], name='Signal', line=dict(color='orange', width=1)), row=2, col=1)
                    fig.add_trace(go.Bar(x=stock_df.index, y=stock_df['MACDh_12_26_9'], name='Histogram', marker_color=['green' if val >= 0 else 'red' for val in stock_df['MACDh_12_26_9']]), row=2, col=1)
                    fig.update_yaxes(title_text="MACD", row=2, col=1)
                
                if "RSI" in selected_indicators:
                    fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['RSI_14'], mode='lines', name='RSI'), row=3, col=1)
                    fig.add_hline(y=70, row=3, col=1, line_dash="dash", line_color="red", line_width=1); fig.add_hline(y=30, row=3, col=1, line_dash="dash", line_color="green", line_width=1)
                    fig.update_yaxes(title_text="RSI", row=3, col=1)
                elif "OBV" in selected_indicators:
                    fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['OBV'], mode='lines', name='OBV'), row=3, col=1)
                    fig.update_yaxes(title_text="OBV", row=3, col=1)
                
                fig.update_layout(title_text=f"{all_data[0]['ticker']} Advanced Chart", xaxis_rangeslider_visible=False, height=700)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data to plot.")
        else: # Beginner Mode
            st.header("Performance Comparison")
            plot_data = [data for data in all_data if not data['hist'].empty]
            if plot_data:
                fig = go.Figure()
                for data in plot_data:
                    normalized_hist = normalize_prices(data['hist'])
                    fig.add_trace(go.Scatter(x=normalized_hist.index, y=normalized_hist, mode='lines', name=data['ticker']))
                fig.update_layout(title="Normalized Price Performance (starting at 100)", yaxis_title="Normalized Price")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data to plot.")

    with main_tabs[1]:
        # This logic remains the same, but now works with multiple stocks for beginners
        if len(all_data) > 1:
            st.info("AI Insights below compare the first two selected stocks.")
            ai_comp = get_ai_comparison(all_data[0], all_data[1], investor_level)
            st.markdown(ai_comp)
        else:
            ai_sum = get_ai_summary(all_data[0]['news'], all_data[0]['ticker'], investor_level)
            st.markdown(ai_sum)

    with main_tabs[2]:
        if len(all_data) == 1:
            display_stock_details(st, all_data[0])
        else:
            col1, col2 = st.columns(2)
            if len(all_data) > 0: display_stock_details(col1, all_data[0])
            if len(all_data) > 1: display_stock_details(col2, all_data[1])
            
    with main_tabs[3]:
        st.header(f"30-Day Price Forecast for {all_data[0]['ticker']}")
        if len(all_data) > 1:
            st.warning("Price prediction is only available when analyzing a single stock.")
        else:
            with st.spinner("Generating price forecast..."): forecast = get_price_prediction(all_data[0]['hist'])
            if forecast is not None:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Forecast', line=dict(color='royalblue', dash='dash')))
                fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_upper'], fill=None, mode='lines', line=dict(color='lightgray'), showlegend=False))
                fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_lower'], fill='tonexty', mode='lines', line=dict(color='lightgray'), name='Uncertainty'))
                fig.add_trace(go.Scatter(x=all_data[0]['hist'].index, y=all_data[0]['hist']['Close'], mode='lines', name='Actual Price', line=dict(color='black')))
                fig.update_layout(title='Price Forecast with Uncertainty Interval', yaxis_title='Price (USD)'); st.plotly_chart(fig, use_container_width=True)
            else: st.warning("Could not generate a forecast. Not enough historical data.")
else:
    st.info("Enter stock(s) and click 'Analyse' to begin.")
