from firebase_admin import firestore
import streamlit as st
import yfinance as yf
import pandas as pd
from .data_handler import get_financial_news
from .ai_analyzer import analyze_sentiment, get_ai_portfolio_analysis

# Initialize Firestore client
db = firestore.client()

def get_playground_portfolio(uid):
    """
    Retrieves or initializes a user's playground portfolio from Firestore.
    
    Args:
        uid (str): User's unique identifier
        
    Returns:
        dict: Portfolio data containing cash balance and holdings, or None if error
    """
    if not uid: return None
    try:
        portfolio_doc_ref = db.collection('users').document(uid).collection('playground').document('portfolio_data')
        portfolio_doc = portfolio_doc_ref.get()

        if portfolio_doc.exists:
            return portfolio_doc.to_dict()
        else:
            initial_portfolio = {
                'cash': 100000.00,
                'holdings': []
            }
            portfolio_doc_ref.set(initial_portfolio)
            return initial_portfolio
            
    except Exception as e:
        print(f"Error getting playground portfolio for {uid}: {e}")
        return None

def execute_trade(uid, ticker, quantity, price, action):
    """
    Executes a buy or sell trade and updates the user's portfolio in Firestore.
    
    Args:
        uid (str): User's unique identifier
        ticker (str): Stock symbol
        quantity (float): Number of shares to trade
        price (float): Price per share
        action (str): 'buy' or 'sell'
        
    Returns:
        tuple: (success (bool), message (str))
    """
    if not all([uid, ticker, quantity > 0, price > 0, action in ['buy', 'sell']]):
        return False, "Invalid trade parameters."

    try:
        portfolio_doc_ref = db.collection('users').document(uid).collection('playground').document('portfolio_data')
        
        @firestore.transactional
        def update_in_transaction(transaction, doc_ref):
            snapshot = doc_ref.get(transaction=transaction)
            if not snapshot.exists:
                return False, "Portfolio not found."
            
            portfolio_data = snapshot.to_dict()
            cash = portfolio_data.get('cash', 0)
            holdings = portfolio_data.get('holdings', [])
            
            if action == 'buy':
                cost = quantity * price
                if cash < cost:
                    return False, "Insufficient cash to complete this purchase."
                new_cash = cash - cost
                existing_holding = next((h for h in holdings if h['ticker'] == ticker), None)
                if existing_holding:
                    total_shares = existing_holding['shares'] + quantity
                    total_cost = (existing_holding['shares'] * existing_holding['purchase_price']) + cost
                    existing_holding['purchase_price'] = total_cost / total_shares
                    existing_holding['shares'] = total_shares
                else:
                    holdings.append({'ticker': ticker, 'shares': quantity, 'purchase_price': price})
                transaction.update(doc_ref, {'cash': new_cash, 'holdings': holdings})
                return True, f"Successfully purchased {quantity} shares of {ticker}."

            elif action == 'sell':
                existing_holding = next((h for h in holdings if h['ticker'] == ticker), None)
                if not existing_holding or existing_holding['shares'] < quantity:
                    return False, f"You do not own enough shares of {ticker} to sell."
                proceeds = quantity * price
                new_cash = cash + proceeds
                existing_holding['shares'] -= quantity
                updated_holdings = [h for h in holdings if h['shares'] > 0]
                transaction.update(doc_ref, {'cash': new_cash, 'holdings': updated_holdings})
                return True, f"Successfully sold {quantity} shares of {ticker}."

        transaction = db.transaction()
        success, message = update_in_transaction(transaction, portfolio_doc_ref)
        return success, message

    except Exception as e:
        print(f"Error executing trade for {uid}: {e}")
        return False, f"An unexpected error occurred: {e}"

@st.cache_data(ttl=600) # Cache report for 10 minutes
def generate_health_report(_uid, portfolio, total_portfolio_value, total_stock_value):
    """
    Analyzes the user's portfolio and generates data for the AI report.
    
    Args:
        _uid (str): User's unique identifier (unused, for cache invalidation)
        portfolio (dict): User's portfolio data
        total_portfolio_value (float): Total value of portfolio including cash
        total_stock_value (float): Total value of stock holdings
        
    Returns:
        tuple: (report_data (dict), message (str))
    """
    holdings = portfolio.get('holdings', [])
    if not holdings:
        return None, "Your portfolio is empty. Add some stocks to get a health report."

    df = pd.DataFrame(holdings)
    tickers = df['ticker'].unique().tolist()
    
    all_news = []
    sector_data = {}
    
    # Get sector allocation and news data
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            sector = info.get('sector', 'Other')
            if sector not in sector_data:
                sector_data[sector] = 0
            
            # Calculate market value for this ticker
            market_value = (df[df['ticker'] == ticker]['shares'].iloc[0] * info.get('regularMarketPrice', 0))
            sector_data[sector] += market_value
            
            all_news.extend(get_financial_news(ticker))
        except Exception:
            continue
            
    # Calculate portfolio metrics
    # Diversification Score (Herfindahl-Hirschman Index inverse)
    sector_weights = {sector: value / total_stock_value for sector, value in sector_data.items()}
    hhi = sum(weight**2 for weight in sector_weights.values())
    diversification_score = (1 - hhi) * 100
    
    # Risk Concentration
    df['market_value'] = df.apply(lambda row: row['shares'] * yf.Ticker(row['ticker']).info.get('regularMarketPrice', 0), axis=1)
    df['portfolio_weight'] = df['market_value'] / total_portfolio_value
    highest_risk = df.sort_values('portfolio_weight', ascending=False).iloc[0]
    
    # Portfolio Sentiment
    portfolio_sentiment = analyze_sentiment(all_news)

    # Format data for AI analysis
    report_data = {
        "Total Portfolio Value": f"${total_portfolio_value:,.2f}",
        "Cash vs Stocks Ratio": f"{portfolio['cash']/total_portfolio_value:.1%} Cash vs. {total_stock_value/total_portfolio_value:.1%} Stocks",
        "Diversification Score (0-100)": f"{diversification_score:.1f}",
        "Sector Allocation": {sector: f"{weight:.1%}" for sector, weight in sector_weights.items()},
        "Highest Stock Concentration": f"{highest_risk['ticker']} makes up {highest_risk['portfolio_weight']:.1%} of your portfolio.",
        "Overall News Sentiment": f"{portfolio_sentiment:.2f} (where >0 is positive, <0 is negative)"
    }
    
    report_data_string = "\n".join([f"- {key}: {value}" for key, value in report_data.items()])
    
    # Generate AI analysis
    ai_analysis = get_ai_portfolio_analysis(report_data_string)
    
    # Prepare final report
    final_report = {
        "diversification_score": diversification_score,
        "portfolio_sentiment": portfolio_sentiment,
        "sector_allocation": {sector: value for sector, value in sorted(sector_data.items(), key=lambda item: item[1], reverse=True)},
        "ai_analysis": ai_analysis
    }
    
    return final_report, "Report generated successfully."