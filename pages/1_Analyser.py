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
from backend.technical_analyzer import add_technical_indicators # <-- NEW IMPORT

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

def display_stock_details(container, ticker_data):
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
        if ticker_data['hist'].empty: st.warning("No historical price data.")
        else:
            c1, c2 = st.columns(2)
            c1.metric("Last Close", f"${ticker_data['hist']['Close'].iloc[-1]:,.2f}")
            c2.metric("Market Cap", f"${ticker_data['info'].info.get('marketCap', 0) / 1e9:,.2f}B")
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
    tickers_input = st.text_input("Enter a stock ticker (e.g., AAPL)", "TSLA").upper()
    
    st.header("Chart Options")
    indicator_options = ["SMA 20", "SMA 50", "EMA 20", "Bollinger Bands", "RSI", "MACD", "OBV"]
    selected_indicators = st.multiselect("Select technical indicators:", indicator_options, default=[])

    st.header("Date Range")
    today = date.today()
    start_date = st.date_input("Start Date", today - timedelta(days=730))
    end_date = st.date_input("End Date", today)
    
    st.header("AI Analysis Level")
    investor_level = st.selectbox("Choose your investor profile:", ("Beginner", "Advanced"))
    
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = get_watchlist(st.session_state.get('uid'))
    
    analyze_button = st.button("Analyse Stock", type="primary")

# --- Main Content Logic ---
if analyze_button:
    if start_date >= end_date:
        st.warning("The start date must be before the end date.")
    else:
        st.session_state.watchlist = get_watchlist(st.session_state.get('uid'))
        # Technical analysis is best for a single stock
        ticker = tickers_input.split(',')[0].strip()
        
        if not ticker:
            st.warning("Please enter at least one valid stock ticker.")
        else:
            all_data = []
            with st.spinner(f"Fetching and analysing {ticker}..."):
                stock_info, stock_hist = get_stock_data(ticker, start_date, end_date)
                if stock_info:
                    stock_hist_with_ta = add_technical_indicators(stock_hist.copy())
                    news = get_financial_news(ticker)
                    all_data.append({
                        "ticker": ticker, "info": stock_info, 
                        "hist": stock_hist_with_ta,
                        "news": news, 
                        "sentiment": analyze_sentiment(news)
                    })
                else:
                    st.error(f"Could not retrieve data for {ticker}.")
            
            if not all_data: st.stop()

            # --- Tab Creation ---
            tab_list = ["Advanced Chart", "AI Insights", "Detailed Analysis", "Price Prediction"]
            main_tabs = st.tabs(tab_list)

            with main_tabs[0]: # Advanced Chart Tab
                stock_df = all_data[0]['hist']
                if not stock_df.empty:
                    # Create subplots: 1 for price, 1 for MACD, 1 for RSI/OBV
                    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                                        vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])

                    # Plot Main Price Candlestick
                    fig.add_trace(go.Candlestick(x=stock_df.index, open=stock_df['Open'], high=stock_df['High'],
                                                 low=stock_df['Low'], close=stock_df['Close'], name='Price'), row=1, col=1)

                    # Plot selected indicators on the main chart
                    if "SMA 20" in selected_indicators:
                        fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['SMA_20'], mode='lines', name='SMA 20', line=dict(width=1)), row=1, col=1)
                    if "SMA 50" in selected_indicators:
                        fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['SMA_50'], mode='lines', name='SMA 50', line=dict(width=1)), row=1, col=1)
                    if "EMA 20" in selected_indicators:
                        fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['EMA_20'], mode='lines', name='EMA 20', line=dict(width=1, dash='dash')), row=1, col=1)
                    if "Bollinger Bands" in selected_indicators and 'BBU_20_2.0' in stock_df.columns:
                        fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['BBU_20_2.0'], line=dict(color='gray', width=0.5), name='Upper Band'), row=1, col=1)
                        fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['BBL_20_2.0'], line=dict(color='gray', width=0.5), fill='tonexty', fillcolor='rgba(128,128,128,0.1)', name='Lower Band'), row=1, col=1)
                    
                    # Plot MACD on the second subplot
                    if "MACD" in selected_indicators and 'MACD_12_26_9' in stock_df.columns:
                        fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['MACD_12_26_9'], name='MACD', line=dict(color='blue', width=1)), row=2, col=1)
                        fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['MACDs_12_26_9'], name='Signal', line=dict(color='orange', width=1)), row=2, col=1)
                        colors = ['green' if val >= 0 else 'red' for val in stock_df['MACDh_12_26_9']]
                        fig.add_trace(go.Bar(x=stock_df.index, y=stock_df['MACDh_12_26_9'], name='Histogram', marker_color=colors), row=2, col=1)
                        fig.update_yaxes(title_text="MACD", row=2, col=1)
                    
                    # Plot RSI or OBV on the third subplot
                    if "RSI" in selected_indicators:
                        fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['RSI_14'], mode='lines', name='RSI'), row=3, col=1)
                        fig.add_hline(y=70, row=3, col=1, line_dash="dash", line_color="red", line_width=1)
                        fig.add_hline(y=30, row=3, col=1, line_dash="dash", line_color="green", line_width=1)
                        fig.update_yaxes(title_text="RSI", row=3, col=1)
                    elif "OBV" in selected_indicators:
                        fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['OBV'], mode='lines', name='OBV'), row=3, col=1)
                        fig.update_yaxes(title_text="OBV", row=3, col=1)
                    
                    fig.update_layout(title_text=f"{ticker} Advanced Chart", xaxis_rangeslider_visible=False, height=700, showlegend=True)
                    fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data to plot.")
            
            with main_tabs[1]:
                ai_sum = get_ai_summary(all_data[0]['news'], all_data[0]['ticker'], investor_level)
                st.markdown(ai_sum)

            with main_tabs[2]:
                display_stock_details(st, all_data[0])
                    
            with main_tabs[3]:
                st.header(f"30-Day Price Forecast for {ticker}")
                with st.spinner("Generating price forecast..."): forecast = get_price_prediction(all_data[0]['hist'])
                if forecast is not None:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Forecast', line=dict(color='royalblue', dash='dash')))
                    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_upper'], fill=None, mode='lines', line=dict(color='lightgray'), showlegend=False))
                    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_lower'], fill='tonexty', mode='lines', line=dict(color='lightgray'), name='Uncertainty'))
                    fig.add_trace(go.Scatter(x=all_data[0]['hist'].index, y=all_data[0]['hist']['Close'], mode='lines', name='Actual Price', line=dict(color='black')))
                    fig.update_layout(title='Price Forecast with Uncertainty Interval', yaxis_title='Price (USD)'); st.plotly_chart(fig, use_container_width=True)
                else: st.warning("Could not generate a forecast. The stock may not have enough historical data.")
else:
    st.info("Enter a stock and click 'Analyse Stocks' to begin.")
