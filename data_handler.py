import yfinance as yf
from newsapi import NewsApiClient
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

def get_stock_data(ticker, start_date, end_date):
    """Fetches historical stock data from yFinance."""
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start_date, end=end_date)
    return stock, hist

def get_financial_news(ticker_symbol):
    """Fetches financial news for a given ticker from NewsAPI."""
    newsapi = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))
    try:
        headlines = newsapi.get_everything(q=ticker_symbol, language='en', sort_by='relevancy', page_size=20)
        return headlines['articles']
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []