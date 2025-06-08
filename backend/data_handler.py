import yfinance as yf
from newsapi import NewsApiClient
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

def get_stock_data(ticker, start_date, end_date):
    """
    Fetches historical stock data from yFinance for a single ticker.
    Includes error handling for invalid tickers and empty data.
    """
    try:
        stock = yf.Ticker(ticker)
        # Check for valid ticker by accessing info. If it's invalid, .info will be empty or cause an error.
        if not stock.info or stock.info.get('regularMarketPrice') is None:
            print(f"Invalid or delisted ticker: {ticker}")
            return None, None
            
        hist = stock.history(start=start_date, end=end_date)
        
        return stock, hist
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None, None


def get_financial_news(ticker_symbol):
    """Fetches financial news for a given ticker from NewsAPI."""
    # Check if API key exists
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        print("Error: NEWS_API_KEY not found. Please check your .env file.")
        return []
        
    newsapi = NewsApiClient(api_key=api_key)
    try:
        headlines = newsapi.get_everything(q=ticker_symbol, language='en', sort_by='relevancy', page_size=20)
        return headlines.get('articles', []) # Use .get() for safety
    except Exception as e:
        print(f"Error fetching news for {ticker_symbol}: {e}")
        return []
