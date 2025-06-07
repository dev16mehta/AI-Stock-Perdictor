import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from data_handler import get_stock_data, get_financial_news
from ai_analyzer import analyze_sentiment, get_ai_summary

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Stock Analysis",
    page_icon="📈",
    layout="wide"
)

# --- Main Title ---
st.title("AI Stock Analyser")
st.caption("""Made by Dev Mehta,
           Powered by yFinance, NewsAPI, VADER, and Groq""")

# --- Sidebar for User Inputs ---
with st.sidebar:
    st.header("Select your stock: ")
    ticker = st.text_input("Enter a Stock (e.g. AAPL)", "TSLA").upper()
    
    st.header("Date Range")
    start_date = st.date_input("Start Date", date.today() - timedelta(days=365))
    end_date = st.date_input("End Date", date.today())
    
    st.header("AI Analysis")
    investor_level = st.selectbox("Choose your investor profile:", ("Beginner", "Advanced"))
    
    analyze_button = st.button("Analyse Stock", type="primary")

# --- Main Content Area ---
if analyze_button:
    if not ticker:
        st.warning("Please enter a stock.")
    else:
        # --- Data Fetching and Analysis ---
        with st.spinner(f"I am analysing {ticker} for you... This may take a moment!"):
            stock_info, stock_hist = get_stock_data(ticker, start_date, end_date)
            news_articles = get_financial_news(ticker)
            sentiment_score = analyze_sentiment(news_articles)
            ai_summary = get_ai_summary(news_articles, ticker, investor_level)

        # --- Displaying Data ---
        st.header(f"{stock_info.info.get('longName', ticker)} ({ticker})")
        
        # --- Key Metrics and Sentiment ---
        col1, col2, col3 = st.columns(3)
        with col1:
            current_price = stock_hist['Close'].iloc[-1]
            st.metric("Last Close Price", f"${current_price:,.2f}")
        with col2:
            market_cap = stock_info.info.get('marketCap', 0)
            st.metric("Market Cap", f"${market_cap / 1e9:,.2f}B")
        with col3:
            # Display sentiment with color
            sentiment_color = "green" if sentiment_score > 0.05 else "red" if sentiment_score < -0.05 else "orange"
            st.metric("News Sentiment", f"{sentiment_score:.2f}", help="Score > 0.05 is Positive, < -0.05 is Negative")
            st.markdown(f'<div style="width: 100%; background-color: #ddd; border-radius: 5px;"><div style="width: {(sentiment_score + 1) * 50}%; background-color: {sentiment_color}; height: 24px; border-radius: 5px; text-align: center; color: white; line-height: 24px;"></div></div>', unsafe_allow_html=True)
            
        # --- Create Tabs ---
        tab1, tab2, tab3, tab4 = st.tabs(["Price Chart", "AI Insights", "Latest News", "Financials"])

        with tab1:
            fig = go.Figure(data=[go.Candlestick(x=stock_hist.index,
                            open=stock_hist['Open'],
                            high=stock_hist['High'],
                            low=stock_hist['Low'],
                            close=stock_hist['Close'])])
            fig.update_layout(title=f'{ticker} Price Action', xaxis_title='Date', yaxis_title='Price (USD)', xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("AI Summary")
            st.markdown(ai_summary)

        with tab3:
            st.subheader("Recent News")
            for article in news_articles:
                with st.expander(f"{article['title']}"):
                    st.write(article['description'])
                    st.write(f"Source: {article['source']['name']} | Published: {pd.to_datetime(article['publishedAt']).strftime('%Y-%m-%d')}")
                    st.markdown(f"[Read full article]({article['url']})", unsafe_allow_html=True)

        with tab4:
            st.subheader("Company Financials")
            st.write("Income Statement")
            st.dataframe(stock_info.income_stmt)
            st.write("Balance Sheet")
            st.dataframe(stock_info.balance_sheet)

else:
    st.info("Enter a stock and click 'Analyse Stock' to begin.")