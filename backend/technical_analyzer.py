import pandas as pd
import pandas_ta as ta

def add_technical_indicators(df):
    """
    Calculates and adds technical indicators to the historical data DataFrame.
    
    Args:
        df (pd.DataFrame): The stock's historical price data.
        
    Returns:
        pd.DataFrame: The DataFrame with added indicator columns.
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
        df = df.join(bollinger) # Joins BBL_20_2.0, BBM_20_2.0, BBU_20_2.0, etc.

    # Relative Strength Index (RSI)
    df['RSI_14'] = ta.rsi(df['Close'], length=14)
    
    return df
