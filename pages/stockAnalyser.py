import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import sys
import os

# This tells Python to look in the parent directory for modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from backend.data_handler import get_stock_data, get_financial_news
from backend.ai_analyzer import analyze_sentiment, get_ai_summary, get_ai_comparison
from backend.predictor import get_price_prediction # <-- NEW IMPORT

# --- Page Configuration ---
st.set_page_config(
    page_title="QuantView AI",
    page_icon="📈",
    layout="wide"
)

# --- Helper Functions ---
def normalize_prices(df):
    """Normalizes the 'Close' price of a dataframe to start at 100."""
    return (df['Close'] / df['Close'].iloc[0]) * 100

def display_sentiment_bar(container, score):
    """Displays a custom sentiment bar inside a given container."""
    sentiment_color = "green" if score > 0.05 else "red" if score < -0.05 else "orange"
    bar_width = (score + 1) * 50
    container.markdown(f"""
        <div style="width: 100%; background-color: #ddd; border-radius: 5px; height: 24px;">
            <div style="width: {bar_width}%; background-color: {sentiment_color}; height: 24px; border-radius: 5px; text-align: center; color: white; line-height: 24px;">
            </div>
        </div>
    """, unsafe_allow_html=True)

def display_stock_details(container, ticker_data):
    """Displays the detailed data for a single stock in a given container."""
    container.header(f"{ticker_data['info'].info.get('longName', ticker_data['ticker'])}")
    sub_tabs = container.tabs(["📊 Key Metrics", "💬 News Sentiment", "💰 Financials", "📰 Recent News"])
    with sub_tabs[0]:
        if ticker_data['hist'].empty:
            st.warning("No historical price data for the selected range.")
        else:
            col1, col2 = st.columns(2)
            current_price = ticker_data['hist']['Close'].iloc[-1]
            col1.metric("Last Close", f"${current_price:,.2f}")
            market_cap = ticker_data['info'].info.get('marketCap', 0)
            col2.metric("Market Cap", f"${market_cap / 1e9:,.2f}B")
    with sub_tabs[1]:
        st.metric("Sentiment Score", f"{ticker_data['sentiment']:.2f}", help="Score > 0.05 is Positive, < -0.05 is Negative")
        display_sentiment_bar(st, ticker_data['sentiment'])
    with sub_tabs[2]:
        st.write("**Income Statement**")
        st.dataframe(ticker_data['info'].income_stmt.head())
        st.write("**Balance Sheet**")
        st.dataframe(ticker_data['info'].balance_sheet.head())
    with sub_tabs[3]:
        if not ticker_data['news']:
            st.write("No recent news found.")
        for article in ticker_data['news'][:5]:
            if article and article.get('title'):
                st.write(f"**{article['title']}**")
                st.write(f"_{article.get('source', {}).get('name', 'Unknown Source')} - {pd.to_datetime(article.get('publishedAt')).strftime('%Y-%m-%d')}_")
                st.markdown(f"[Read]({article.get('url')})", unsafe_allow_html=True)
                st.divider()

# --- Main App ---
st.markdown("""
    # QuantView AI
    **Made by Dev Mehta** | *Powered by yFinance, NewsAPI, VADER, Groq, and Prophet*
""")
st.caption("Enter one or two stocks (comma-separated) for a side-by-side comparison.")
st.divider()

# --- Sidebar ---
with st.sidebar:
    st.header("Stock Selection")
    tickers_input = st.text_input("Enter stocks (e.g., AAPL, MSFT)", "TSLA").upper()
    
    st.header("Date Range")
    today = date.today()
    start_date = st.date_input("Start Date", today - timedelta(days=730))
    end_date = st.date_input("End Date", today)
    
    st.header("AI Analysis Level")
    investor_level = st.selectbox("Choose your investor profile:", ("Beginner", "Advanced"))
    
    analyze_button = st.button("Analyse Stocks", type="primary")

# --- Main Content ---
if analyze_button:
    if start_date >= end_date:
        st.warning("The start date must be before the end date.")
    else:
        tickers = [ticker.strip() for ticker in tickers_input.split(',') if ticker.strip()]
        
        if not tickers:
            st.warning("Please enter at least one valid stock ticker.")
        else:
            all_data = []
            with st.spinner("Fetching and analysing data..."):
                for ticker in tickers:
                    stock_info, stock_hist = get_stock_data(ticker, start_date, end_date)
                    if stock_info:
                        news = get_financial_news(ticker)
                        sentiment = analyze_sentiment(news)
                        all_data.append({
                            "ticker": ticker, "info": stock_info, "hist": stock_hist if stock_hist is not None else pd.DataFrame(),
                            "news": news, "sentiment": sentiment
                        })
                    else:
                        st.error(f"Could not retrieve data for {ticker}. It may be an invalid ticker symbol.")
            
            if not all_data:
                st.stop()

            # --- Create Main Tabs ---
            tab_list = ["📊 Performance", "🤖 AI Insights", "📈 Detailed Analysis"]
            if len(all_data) == 1:
                tab_list.append("🔮 Price Prediction")
            main_tabs = st.tabs(tab_list)

            with main_tabs[0]: # Performance Tab
                plot_data = [data for data in all_data if not data['hist'].empty]
                if plot_data:
                    fig = go.Figure()
                    for data in plot_data:
                        normalized_hist = normalize_prices(data['hist'])
                        fig.add_trace(go.Scatter(x=normalized_hist.index, y=normalized_hist, mode='lines', name=data['ticker']))
                    fig.update_layout(title="Normalized Price Performance (starting at 100)", yaxis_title="Normalized Price")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No historical data to plot for the selected range.")

            with main_tabs[1]: # AI Insights Tab
                if len(all_data) == 2:
                    ai_comp = get_ai_comparison(all_data[0], all_data[1], investor_level)
                    st.markdown(ai_comp)
                else:
                    ai_sum = get_ai_summary(all_data[0]['news'], all_data[0]['ticker'], investor_level)
                    st.markdown(ai_sum)

            with main_tabs[2]: # Detailed Analysis Tab
                if len(all_data) == 1:
                    display_stock_details(st, all_data[0])
                elif len(all_data) == 2:
                    col1, col2 = st.columns(2)
                    display_stock_details(col1, all_data[0])
                    display_stock_details(col2, all_data[1])

            # Price Prediction Tab (only if one stock is selected)
            if len(all_data) == 1 and len(main_tabs) == 4:
                with main_tabs[3]:
                    st.header(f"30-Day Price Forecast for {all_data[0]['ticker']}")
                    with st.spinner("Generating price forecast..."):
                        forecast = get_price_prediction(all_data[0]['hist'])
                    
                    if forecast is not None:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Forecast', line=dict(color='royalblue', dash='dash')))
                        fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_upper'], fill=None, mode='lines', line=dict(color='lightgray'), showlegend=False))
                        fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_lower'], fill='tonexty', mode='lines', line=dict(color='lightgray'), name='Uncertainty'))
                        fig.add_trace(go.Scatter(x=all_data[0]['hist'].index, y=all_data[0]['hist']['Close'], mode='lines', name='Actual Price', line=dict(color='black')))
                        
                        fig.update_layout(title='Price Forecast with Uncertainty Interval', yaxis_title='Price (USD)')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Could not generate a forecast. The stock may not have enough historical data (at least 30 data points are recommended).")
else:
    st.info("Enter a stock and click 'Analyse Stocks' to begin.")

