import pandas as pd
import pandas_ta as ta

def add_technical_indicators(df):
    """
    Calculate and add technical indicators to stock price data.
    
    This function adds several popular technical indicators to the DataFrame:
    - Simple Moving Averages (20 and 50 periods)
    - Exponential Moving Average (20 periods)
    - Bollinger Bands (20 periods, 2 standard deviations)
    - Relative Strength Index (14 periods)
    - MACD (12, 26, 9)
    - On-Balance Volume
    
    Args:
        df (pd.DataFrame): Historical price data with columns:
            - Open: Opening prices
            - High: Highest prices
            - Low: Lowest prices
            - Close: Closing prices
            - Volume: Trading volume
        
    Returns:
        pd.DataFrame: Original DataFrame with additional indicator columns
    """
    if df.empty:
        return df
        
    # Calculate trend-following indicators
    df['SMA_20'] = ta.sma(df['Close'], length=20)
    df['SMA_50'] = ta.sma(df['Close'], length=50)
    df['EMA_20'] = ta.ema(df['Close'], length=20)
    
    # Calculate volatility indicators
    bollinger = ta.bbands(df['Close'], length=20)
    if bollinger is not None and not bollinger.empty:
        df = df.join(bollinger)

    # Calculate momentum indicators
    df['RSI_14'] = ta.rsi(df['Close'], length=14)
    
    # Calculate trend and momentum crossover indicator
    macd = ta.macd(df['Close'])
    if macd is not None and not macd.empty:
        df = df.join(macd)

    # Calculate volume-based indicator
    df['OBV'] = ta.obv(df['Close'], df['Volume'])
    
    return df
