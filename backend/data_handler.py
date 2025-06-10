import yfinance as yf
from newsapi import NewsApiClient
import os
from dotenv import load_dotenv
from firebase_admin import firestore

load_dotenv() 

db = firestore.client()

def get_stock_data(ticker, start_date, end_date):
    """Fetches historical stock data from yFinance."""
    try:
        stock = yf.Ticker(ticker)
        if not stock.info or stock.info.get('regularMarketPrice') is None:
            return None, None
        return stock, stock.history(start=start_date, end=end_date)
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None, None

def get_financial_news(ticker_symbol):
    """Fetches financial news from NewsAPI."""
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return []
    try:
        newsapi = NewsApiClient(api_key=api_key)
        return newsapi.get_everything(q=ticker_symbol, language='en', sort_by='relevancy', page_size=20).get('articles', [])
    except Exception as e:
        print(f"Error fetching news for {ticker_symbol}: {e}")
        return []

# --- NEW, SIMPLIFIED WATCHLIST FUNCTIONS ---

def get_watchlist(uid):
    """Retrieves the watchlist for a given user ID."""
    if not uid: return []
    try:
        docs = db.collection('users').document(uid).collection('stocks').stream()
        return [doc.id for doc in docs]
    except Exception as e:
        print(f"Error getting watchlist: {e}")
        return []

def add_to_watchlist(uid, ticker):
    """Adds a ticker to the user's watchlist."""
    if not uid or not ticker: return
    try:
        db.collection('users').document(uid).collection('stocks').document(ticker).set({
            'added_at': firestore.SERVER_TIMESTAMP
        })
        print(f"Successfully added {ticker} to Firestore for user {uid}")
    except Exception as e:
        print(f"Error adding {ticker} to watchlist: {e}")

def remove_from_watchlist(uid, ticker):
    """Removes a ticker from the user's watchlist."""
    if not uid or not ticker: return
    try:
        db.collection('users').document(uid).collection('stocks').document(ticker).delete()
        print(f"Successfully removed {ticker} from Firestore for user {uid}")
    except Exception as e:
        print(f"Error removing {ticker} from watchlist: {e}")
