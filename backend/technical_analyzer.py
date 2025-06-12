import pandas as pd
import pandas_ta_openbb as ta

def add_technical_indicators(df):
    """
    Calculates and adds a comprehensive set of technical indicators 
    to the historical data DataFrame using the pandas-ta library.
    
    Args:
        df (pd.DataFrame): The stock's historical price data. 
                           It must have 'Open', 'High', 'Low', 'Close', 'Volume' columns.
        
    Returns:
        pd.DataFrame: The original DataFrame with new columns for each indicator.
    """
    if df.empty:
        return df
        
    # Simple Moving Averages (SMA)
    df['SMA_20'] = ta.sma(df['Close'], length=20)
    df['SMA_50'] = ta.sma(df['Close'], length=50)
    
    # Exponential Moving Average (EMA)
    df['EMA_20'] = ta.ema(df['Close'], length=20)
    
    # Bollinger Bands
    bollinger = ta.bbands(df['Close'], length=20)
    if bollinger is not None and not bollinger.empty:
        df = df.join(bollinger)

    # Relative Strength Index (RSI)
    df['RSI_14'] = ta.rsi(df['Close'], length=14)
    
    # Moving Average Convergence Divergence (MACD)
    macd = ta.macd(df['Close'])
    if macd is not None and not macd.empty:
        # Join the MACD line, signal line, and histogram
        df = df.join(macd)

    # On-Balance Volume (OBV)
    df['OBV'] = ta.obv(df['Close'], df['Volume'])
    
    return df
