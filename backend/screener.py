import streamlit as st
import os
import yfinance as yf
import pandas as pd
import requests
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# --- Helper function to get the stock list ---
@st.cache_data(ttl=3600) # Cache the list for 1 hour to avoid refetching
def get_sp500_tickers():
    """Fetches the list of S&P 500 tickers."""
    try:
        # Using Wikipedia's S&P 500 list
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        df = tables[0]
        return df['Symbol'].tolist()
    except Exception as e:
        print(f"Error fetching S&P 500 tickers: {e}")
        # Fallback list in case the API fails
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "JPM", "JNJ"]

# --- Helper function to get key stats for a list of tickers ---
@st.cache_data(ttl=600) # Cache data for 10 minutes
def get_key_stats(tickers):
    """Fetches key financial statistics for a list of stock tickers."""
    all_stats = []
    for ticker_symbol in tickers:
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            # Select only the most relevant stats for screening
            stats = {
                'Symbol': ticker_symbol,
                'Name': info.get('longName', 'N/A'),
                'Sector': info.get('sector', 'N/A'),
                'Industry': info.get('industry', 'N/A'),
                'Market Cap': info.get('marketCap', 0),
                'P/E Ratio': info.get('trailingPE', 0),
                'Debt/Equity': info.get('debtToEquity', 0),
                'Profit Margin': info.get('profitMargins', 0),
                'Revenue Growth': info.get('revenueGrowth', 0)
            }
            all_stats.append(stats)
        except Exception as e:
            print(f"Could not fetch stats for {ticker_symbol}: {e}")
            continue
    return pd.DataFrame(all_stats)

# --- Main AI Screener Function ---
def run_ai_screener(prompt):
    """
    Takes a natural language prompt, fetches stock data, and uses an LLM to screen for matching stocks.
    """
    if not prompt:
        return "Please enter a screening criterion.", pd.DataFrame()

    # Step 1: Get the universe of stocks to screen (S&P 500)
    tickers = get_sp500_tickers()
    
    # For demonstration purposes, let's limit to the first 200 stocks to keep it fast
    tickers_to_scan = tickers[:200] 
    
    # Step 2: Get the key financial data for these stocks
    df_stats = get_key_stats(tickers_to_scan)
    if df_stats.empty:
        return "Could not retrieve financial data for screening.", pd.DataFrame()
        
    # Convert the DataFrame to a string format for the AI prompt
    stats_string = df_stats.to_string()

    # Step 3: Use an LLM to perform the screening
    if 'GROQ_API_KEY' in st.secrets:
        api_key = st.secrets['GROQ_API_KEY']
    else:
        api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return "Error: GROQ_API_KEY not found.", pd.DataFrame()

    llm = ChatGroq(temperature=0, model_name="llama3-70b-8192", api_key=api_key)

    screener_template = """
    You are an expert financial analyst with the task of screening stocks.
    Based on the user's request, you must analyze the following list of stocks and their financial data.
    Your task is to return ONLY a Python list of the stock symbols that strictly match the user's criteria.
    Do not provide any explanation or other text, just the Python list of symbols.

    User's Request: "{prompt}"

    Stock Data:
    {stock_data}

    Based on the user's request, the Python list of matching stock symbols is:
    """
    
    prompt_template = PromptTemplate(
        template=screener_template, 
        input_variables=["prompt", "stock_data"]
    )
    
    screener_chain = LLMChain(prompt=prompt_template, llm=llm)

    try:
        response = screener_chain.invoke({
            "prompt": prompt,
            "stock_data": stats_string
        })
        
        ai_response_text = response.get('text', '[]')
        
        # Safely evaluate the string to get a Python list
        import ast
        try:
            screened_tickers = ast.literal_eval(ai_response_text)
            if not isinstance(screened_tickers, list):
                screened_tickers = []
        except:
            screened_tickers = [] # If AI returns malformed text, return an empty list

        # Filter the original DataFrame to show only the results
        results_df = df_stats[df_stats['Symbol'].isin(screened_tickers)]
        
        analysis_summary = f"Screening complete. Found {len(results_df)} stocks matching your criteria."
        
        return analysis_summary, results_df

    except Exception as e:
        return f"An error occurred during AI screening: {e}", pd.DataFrame()

