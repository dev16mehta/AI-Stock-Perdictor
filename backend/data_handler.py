import yfinance as yf
from newsapi import NewsApiClient
import os
from dotenv import load_dotenv
from firebase_admin import firestore
import time

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
        print("No UID provided for get_watchlist")
        return []
    try:
        print(f"Fetching watchlist for UID: {uid}")
        # First, ensure the user's watchlist document exists
        user_watchlist_ref = db.collection('users').document(uid)
        user_watchlist = user_watchlist_ref.get()
        
        if not user_watchlist.exists:
            print(f"Creating new watchlist document for user {uid}")
            user_watchlist_ref.set({'created_at': firestore.SERVER_TIMESTAMP})
        
        # Now get the stocks collection
        stocks_ref = user_watchlist_ref.collection('stocks')
        docs = list(stocks_ref.stream())  # Convert to list to ensure we get all documents
        watchlist = [doc.id for doc in docs]
        print(f"Retrieved watchlist: {watchlist}")
        return watchlist
    except Exception as e:
        print(f"Error getting watchlist: {str(e)}")
        import traceback
        print(f"Full error traceback: {traceback.format_exc()}")
        return []

def add_to_watchlist(uid, ticker):
    """Adds a ticker to the user's watchlist."""
    if not uid or not ticker:
        print(f"Invalid parameters for add_to_watchlist - UID: {uid}, Ticker: {ticker}")
        return False
    try:
        print(f"Adding {ticker} to watchlist for UID: {uid}")
        # First, ensure the user's watchlist document exists
        user_watchlist_ref = db.collection('users').document(uid)
        user_watchlist = user_watchlist_ref.get()
        
        if not user_watchlist.exists:
            print(f"Creating new watchlist document for user {uid}")
            user_watchlist_ref.set({'created_at': firestore.SERVER_TIMESTAMP})
        
        # Add the stock to the user's watchlist
        stock_ref = user_watchlist_ref.collection('stocks').document(ticker)
        
        # Create a batch write to ensure atomicity
        batch = db.batch()
        batch.set(stock_ref, {
            'added_at': firestore.SERVER_TIMESTAMP,
            'last_updated': firestore.SERVER_TIMESTAMP
        })
        
        # Commit the batch
        batch.commit()
        
        # Verify the write
        stock_doc = stock_ref.get()
        if stock_doc.exists:
            print(f"Successfully added {ticker} to watchlist")
            return True
        else:
            print(f"Failed to verify addition of {ticker} to watchlist")
            return False
            
    except Exception as e:
        print(f"Error adding to watchlist: {str(e)}")
        import traceback
        print(f"Full error traceback: {traceback.format_exc()}")
        return False

def remove_from_watchlist(uid, ticker):
    """Removes a ticker from the user's watchlist."""
    if not uid or not ticker:
        print(f"Invalid parameters for remove_from_watchlist - UID: {uid}, Ticker: {ticker}")
        return False
    try:
        print(f"Removing {ticker} from watchlist for UID: {uid}")
        # Get the user's watchlist document
        user_watchlist_ref = db.collection('users').document(uid)
        
        # Remove the stock from the user's watchlist
        stock_ref = user_watchlist_ref.collection('stocks').document(ticker)
        
        # Create a batch write to ensure atomicity
        batch = db.batch()
        batch.delete(stock_ref)
        
        # Commit the batch
        batch.commit()
        
        # Verify the deletion
        stock_doc = stock_ref.get()
        if not stock_doc.exists:
            print(f"Successfully removed {ticker} from watchlist")
            return True
        else:
            print(f"Failed to verify removal of {ticker} from watchlist")
            return False
            
    except Exception as e:
        print(f"Error removing from watchlist: {str(e)}")
        import traceback
        print(f"Full error traceback: {traceback.format_exc()}")
        return False
