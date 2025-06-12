import yfinance as yf
from firebase_admin import firestore
import pandas as pd

db = firestore.client()

def add_to_portfolio(uid, ticker, shares, purchase_price):
    """Adds a holding to the user's portfolio in Firestore."""
    if not all([uid, ticker, shares, purchase_price]):
        return False
    try:
        # We can store multiple lots of the same stock, so we use add() to get a unique ID.
        portfolio_ref = db.collection('users').document(uid).collection('portfolio')
        portfolio_ref.add({
            'ticker': ticker,
            'shares': float(shares),
            'purchase_price': float(purchase_price),
            'added_at': firestore.SERVER_TIMESTAMP
        })
        print(f"Firestore: Added {shares} of {ticker} to portfolio for user {uid}")
        return True
    except Exception as e:
        print(f"Error adding to portfolio: {e}")
        return False

def get_portfolio(uid):
    """Retrieves all holdings for a given user ID."""
    if not uid:
        return []
    try:
        holdings_ref = db.collection('users').document(uid).collection('portfolio')
        docs = holdings_ref.stream()
        portfolio = []
        for doc in docs:
            holding = doc.to_dict()
            holding['id'] = doc.id # Keep the document ID for deletion
            portfolio.append(holding)
        return portfolio
    except Exception as e:
        print(f"Error getting portfolio: {e}")
        return []

def remove_from_portfolio(uid, holding_id):
    """Removes a specific holding from the user's portfolio."""
    if not uid or not holding_id:
        return False
    try:
        holding_ref = db.collection('users').document(uid).collection('portfolio').document(holding_id)
        holding_ref.delete()
        print(f"Firestore: Removed holding {holding_id} for user {uid}")
        return True
    except Exception as e:
        print(f"Error removing from portfolio: {e}")
        return False

@st.cache_data(ttl=300) # Cache live prices for 5 minutes
def get_live_prices(tickers):
    """Gets the current market price for a list of tickers."""
    if not tickers:
        return {}
    
    # yfinance can take a space-separated string of tickers
    data = yf.download(tickers=' '.join(tickers), period='1d', progress=False)
    if data.empty:
        return {}
    
    # Get the most recent closing price for each ticker
    prices = data['Close'].iloc[-1].to_dict()
    return prices
