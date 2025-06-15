import yfinance as yf
from firebase_admin import firestore
import pandas as pd
import streamlit as st

db = firestore.client()

def add_to_portfolio(uid, ticker, shares, purchase_price):
    """
    Add a stock holding to the user's portfolio in Firestore.
    
    Args:
        uid (str): User's unique identifier
        ticker (str): Stock symbol
        shares (float): Number of shares purchased
        purchase_price (float): Price per share at purchase
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not all([uid, ticker, shares, purchase_price]):
        return False
    try:
        # Create a new document with auto-generated ID for each lot
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
    """
    Retrieve all stock holdings for a user from Firestore.
    
    Args:
        uid (str): User's unique identifier
        
    Returns:
        list: List of dictionaries containing holding information
    """
    if not uid:
        return []
    try:
        holdings_ref = db.collection('users').document(uid).collection('portfolio')
        docs = holdings_ref.stream()
        portfolio = []
        for doc in docs:
            holding = doc.to_dict()
            holding['id'] = doc.id  # Store document ID for future operations
            portfolio.append(holding)
        return portfolio
    except Exception as e:
        print(f"Error getting portfolio: {e}")
        return []

def remove_from_portfolio(uid, holding_id):
    """
    Remove a specific stock holding from the user's portfolio.
    
    Args:
        uid (str): User's unique identifier
        holding_id (str): Document ID of the holding to remove
        
    Returns:
        bool: True if successful, False otherwise
    """
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

@st.cache_data(ttl=300)  # Cache market prices for 5 minutes to reduce API calls
def get_live_prices(tickers):
    """
    Fetch current market prices for a list of stock symbols.
    
    Args:
        tickers (list): List of stock symbols to fetch prices for
        
    Returns:
        dict: Dictionary mapping ticker symbols to their current prices
    """
    if not tickers:
        return {}
    
    # Download latest price data for all tickers
    data = yf.download(tickers=' '.join(tickers), period='1d', progress=False)
    if data.empty:
        return {}
    
    # Extract most recent closing prices
    prices = data['Close'].iloc[-1].to_dict()
    return prices
