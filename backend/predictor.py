import pandas as pd
from prophet import Prophet

def get_price_prediction(hist_df):
    """
    Generates a 30-day price forecast using Facebook's Prophet model.
    
    Args:
        hist_df (pd.DataFrame): DataFrame containing historical stock data from yFinance.
        
    Returns:
        pd.DataFrame: A DataFrame containing the forecast with columns 'ds', 'yhat', 'yhat_lower', 'yhat_upper'.
    """
    if hist_df.empty or len(hist_df) < 30: # Need enough data to forecast
        return None

    # Prophet requires columns to be named 'ds' (datestamp) and 'y' (value)
    df_train = hist_df.reset_index()[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})

    # Initialize and train the model
    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=True,
        yearly_seasonality=True,
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10.0
    )
    model.fit(df_train)

    # Create a future dataframe for the next 30 days
    future = model.make_future_dataframe(periods=30)
    
    # Generate the forecast
    forecast = model.predict(future)
    
    return forecast