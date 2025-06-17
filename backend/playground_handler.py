from firebase_admin import firestore
import streamlit as st
import yfinance as yf

# Initialize Firestore client
db = firestore.client()

def get_playground_portfolio(uid):
    """
    Retrieves or initializes a user's playground portfolio from Firestore.
    
    Args:
        uid (str): The user's unique identifier.
        
    Returns:
        dict: A dictionary containing the user's cash and holdings.
              Returns None if there is an error.
    """
    if not uid: return None
    try:
        # Document reference for the entire playground
        portfolio_doc_ref = db.collection('users').document(uid).collection('playground').document('portfolio_data')
        portfolio_doc = portfolio_doc_ref.get()

        if portfolio_doc.exists:
            # Portfolio exists, return its data
            return portfolio_doc.to_dict()
        else:
            # Portfolio does not exist, so initialize it
            initial_portfolio = {
                'cash': 100000.00,
                'holdings': [] # List of dictionaries: {'ticker': str, 'shares': float, 'purchase_price': float}
            }
            portfolio_doc_ref.set(initial_portfolio)
            print(f"Initialized playground for user {uid}")
            return initial_portfolio
            
    except Exception as e:
        print(f"Error getting playground portfolio for {uid}: {e}")
        return None

def execute_trade(uid, ticker, quantity, price, action):
    """
    Executes a buy or sell trade and updates the user's portfolio in Firestore.
    
    Args:
        uid (str): The user's unique identifier.
        ticker (str): The stock symbol to trade.
        quantity (int): The number of shares to trade.
        price (float): The price per share.
        action (str): 'buy' or 'sell'.
        
    Returns:
        tuple: (bool, str) indicating success and a message.
    """
    if not all([uid, ticker, quantity > 0, price > 0, action in ['buy', 'sell']]):
        return False, "Invalid trade parameters."

    try:
        portfolio_doc_ref = db.collection('users').document(uid).collection('playground').document('portfolio_data')
        
        # Use a transaction to ensure atomic read/write
        @firestore.transactional
        def update_in_transaction(transaction, doc_ref):
            snapshot = doc_ref.get(transaction=transaction)
            if not snapshot.exists:
                return False, "Portfolio not found."
            
            portfolio_data = snapshot.to_dict()
            cash = portfolio_data.get('cash', 0)
            holdings = portfolio_data.get('holdings', [])
            
            # --- BUY LOGIC ---
            if action == 'buy':
                cost = quantity * price
                if cash < cost:
                    return False, "Insufficient cash to complete this purchase."
                
                # Update cash
                new_cash = cash - cost
                
                # Check if stock is already in holdings
                existing_holding = next((h for h in holdings if h['ticker'] == ticker), None)
                
                if existing_holding:
                    # Update existing holding
                    total_shares = existing_holding['shares'] + quantity
                    total_cost = (existing_holding['shares'] * existing_holding['purchase_price']) + cost
                    existing_holding['purchase_price'] = total_cost / total_shares
                    existing_holding['shares'] = total_shares
                else:
                    # Add new holding
                    holdings.append({
                        'ticker': ticker,
                        'shares': quantity,
                        'purchase_price': price
                    })
                
                transaction.update(doc_ref, {'cash': new_cash, 'holdings': holdings})
                return True, f"Successfully purchased {quantity} shares of {ticker}."

            # --- SELL LOGIC ---
            elif action == 'sell':
                existing_holding = next((h for h in holdings if h['ticker'] == ticker), None)
                
                if not existing_holding or existing_holding['shares'] < quantity:
                    return False, f"You do not own enough shares of {ticker} to sell."
                    
                # Update cash
                proceeds = quantity * price
                new_cash = cash + proceeds
                
                # Update holdings
                existing_holding['shares'] -= quantity
                
                # If shares are zero, remove the holding
                updated_holdings = [h for h in holdings if h['shares'] > 0]
                
                transaction.update(doc_ref, {'cash': new_cash, 'holdings': updated_holdings})
                return True, f"Successfully sold {quantity} shares of {ticker}."

        transaction = db.transaction()
        success, message = update_in_transaction(transaction, portfolio_doc_ref)
        return success, message

    except Exception as e:
        print(f"Error executing trade for {uid}: {e}")
        return False, f"An unexpected error occurred: {e}"

def update_portfolio_values(portfolio):
    # This function is now mostly handled on the frontend for live display,
    # but can be used for backend calculations if needed.
    holdings = portfolio.get('holdings', [])
    if not holdings:
        return 0, 0
    
    df = pd.DataFrame(holdings)
    tickers = df['ticker'].unique().tolist()
    live_prices = get_live_prices(tickers)
    
    df['current_price'] = df['ticker'].map(live_prices).fillna(df['purchase_price'])
    df['market_value'] = df['shares'] * df['current_price']
    df['gain_loss'] = df['market_value'] - (df['shares'] * df['purchase_price'])
    
    total_stock_value = df['market_value'].sum()
    total_gain_loss = df['gain_loss'].sum()
    
    return total_stock_value, total_gain_loss