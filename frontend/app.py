import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import sys
import os

# This tells Python to look in the parent directory for modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.data_handler import get_stock_data, get_financial_news
from backend.ai_analyzer import analyze_sentiment, get_ai_summary, get_ai_comparison

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Stock Analyser",
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
    bar_width = (score + 1) * 50  # Scale -1 to 1 -> 0 to 100
    container.markdown(f"""
        <div style="width: 100%; background-color: #ddd; border-radius: 5px; height: 24px;">
            <div style="width: {bar_width}%; background-color: {sentiment_color}; height: 24px; border-radius: 5px; text-align: center; color: white; line-height: 24px;">
            </div>
        </div>
    """, unsafe_allow_html=True)

def display_stock_data(container, ticker_data):
    """
    Displays the data for a single stock in a given container (either st or a column).
    All st calls are replaced with container calls to direct output correctly.
    """
    container.header(f"{ticker_data['info'].info.get('longName', ticker_data['ticker'])}")
    
    # Check if historical data exists before trying to display it
    if ticker_data['hist'].empty:
        container.error("No historical price data found for the selected date range. Please select a valid range (e.g., in the past).")
    else:
        # Key Metrics
        col1, col2 = container.columns(2)
        current_price = ticker_data['hist']['Close'].iloc[-1]
        col1.metric("Last Close", f"${current_price:,.2f}")
        market_cap = ticker_data['info'].info.get('marketCap', 0)
        col2.metric("Market Cap", f"${market_cap / 1e9:,.2f}B")

    # Sentiment
    container.subheader("News Sentiment")
    container.metric("Sentiment Score", f"{ticker_data['sentiment']:.2f}", help="Score > 0.05 is Positive, < -0.05 is Negative")
    display_sentiment_bar(container, ticker_data['sentiment'])
    
    # Financials
    with container.expander("View Financials"):
        st.write("**Income Statement**") # st.write is fine here as it's inside an expander
        st.dataframe(ticker_data['info'].income_stmt.head())
        st.write("**Balance Sheet**")
        st.dataframe(ticker_data['info'].balance_sheet.head())
    
    # News
    with container.expander("View Recent News"):
        if not ticker_data['news']:
            st.write("No recent news found.")
        for article in ticker_data['news'][:5]: # Show top 5
            if article and article.get('title'):
                st.write(f"**{article['title']}**")
                st.write(f"_{article.get('source', {}).get('name', 'Unknown Source')} - {pd.to_datetime(article.get('publishedAt')).strftime('%Y-%m-%d')}_")
                st.markdown(f"[Read]({article.get('url')})", unsafe_allow_html=True)
                st.markdown("---")


# --- Main App ---
st.title("AI Stock Analyser")
st.caption("Enter one or two stocks (comma-separated) for a side-by-side comparison.")

# --- Sidebar ---
with st.sidebar:
    st.header("Stock Selection")
    tickers_input = st.text_input("Enter stocks (e.g., AAPL, MSFT)", "TSLA, GOOGL").upper()
    
    st.header("Date Range")
    today = date.today()
    one_year_ago = today - timedelta(days=365)
    start_date = st.date_input("Start Date", one_year_ago)
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
        
        if not tickers or len(tickers) > 2:
            st.warning("Please enter one or two valid stocks.")
        else:
            all_data = []
            with st.spinner("Fetching and analysing data..."):
                for ticker in tickers:
                    stock_info, stock_hist = get_stock_data(ticker, start_date, end_date)
                    if stock_info:
                        news = get_financial_news(ticker)
                        sentiment = analyze_sentiment(news)
                        all_data.append({
                            "ticker": ticker,
                            "info": stock_info,
                            "hist": stock_hist if stock_hist is not None else pd.DataFrame(),
                            "news": news,
                            "sentiment": sentiment
                        })
                    else:
                        st.error(f"Could not retrieve data for {ticker}. It may be an invalid ticker symbol.")
            
            plot_data = [data for data in all_data if not data['hist'].empty]

            if plot_data:
                st.header("Performance Comparison")
                fig = go.Figure()
                for data in plot_data:
                    normalized_hist = normalize_prices(data['hist'])
                    fig.add_trace(go.Scatter(x=normalized_hist.index, y=normalized_hist, mode='lines', name=data['ticker']))
                fig.update_layout(title="Normalized Price Performance (starting at 100)", yaxis_title="Normalized Price")
                st.plotly_chart(fig, use_container_width=True)
            elif all_data:
                 st.info("No historical data to plot for the selected range.")

            if all_data:
                st.header("AI Insights")
                if len(all_data) == 2:
                    with st.spinner("Generating AI comparison..."):
                        ai_comp = get_ai_comparison(all_data[0], all_data[1], investor_level)
                    st.markdown(ai_comp)
                else:
                    with st.spinner("Generating AI summary..."):
                        ai_sum = get_ai_summary(all_data[0]['news'], all_data[0]['ticker'], investor_level)
                    st.markdown(ai_sum)
                st.markdown("---")

            if len(all_data) == 1:
                # Call the function on the main 'st' object
                display_stock_data(st, all_data[0])
            elif len(all_data) == 2:
                # Call the function on each column object
                col1, col2 = st.columns(2)
                display_stock_data(col1, all_data[0])
                display_stock_data(col2, all_data[1])
else:
    st.info("Enter stock and click 'Analyse Stocks' to begin.")
