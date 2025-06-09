import pandas as pd
from prophet import Prophet

def get_price_prediction(hist_df):
    """
    Generates a 30-day price forecast using Facebook's Prophet model.
    """
    if hist_df.empty or len(hist_df) < 30: # Prophet needs sufficient data
        return None

    # Prophet requires columns 'ds' (datestamp) and 'y' (value)
    df_train = hist_df.reset_index()[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})

    # --- FIX: Remove timezone information from the 'ds' column ---
    df_train['ds'] = df_train['ds'].dt.tz_localize(None)

    # Initialize and train the model
    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=True,
        yearly_seasonality=True
    )
    model.fit(df_train)

    # Create a future dataframe for the next 30 days
    future = model.make_future_dataframe(periods=30)
    
    # Generate the forecast
    forecast = model.predict(future)
    
    return forecast
