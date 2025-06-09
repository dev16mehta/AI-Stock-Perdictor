import yfinance as yf
from newsapi import NewsApiClient
import os
from dotenv import load_dotenv
from firebase_admin import firestore

load_dotenv() # Load environment variables from .env file

db = firestore.client() # Initialize Firestore client

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

# --- WATCHLIST FUNCTIONS ---

def get_watchlist(uid):
    """Retrieves the watchlist for a given user ID."""
    if not uid:
        return []
    try:
        watchlist_ref = db.collection('watchlists').document(uid).collection('stocks')
        docs = watchlist_ref.stream()
        return [doc.id for doc in docs]
    except Exception as e:
        print(f"Error getting watchlist: {e}")
        return []

def add_to_watchlist(uid, ticker):
    """Adds a ticker to the user's watchlist."""
    if not uid or not ticker:
        return
    try:
        watchlist_ref = db.collection('watchlists').document(uid).collection('stocks').document(ticker)
        watchlist_ref.set({'added_on': firestore.SERVER_TIMESTAMP})
    except Exception as e:
        print(f"Error adding to watchlist: {e}")

def remove_from_watchlist(uid, ticker):
    """Removes a ticker from the user's watchlist."""
    if not uid or not ticker:
        return
    try:
        watchlist_ref = db.collection('watchlists').document(uid).collection('stocks').document(ticker)
        watchlist_ref.delete()
    except Exception as e:
        print(f"Error removing from watchlist: {e}")
