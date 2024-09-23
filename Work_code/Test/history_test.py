import logging
from kiteconnect import KiteConnect
import pandas as pd
import talib
import json
from datetime import datetime, timedelta

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

# Step 1: Load API key and secret from key.json
with open('kite_key.json', 'r') as f:
    keys = json.load(f)

api_key = keys.get('api_key')
api_secret = keys.get('api_secret')

# Step 2: Load the stored session (access token) from the JSON file
with open('kite_session.json', 'r') as f:
    session_data = json.load(f)

access_token = session_data.get("access_token")

# Step 3: Initialize KiteConnect with the saved access token
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

# Fetch historical data for a specific instrument (e.g., NIFTY)
from_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
to_date = datetime.now().strftime('%Y-%m-%d')
interval = "minute"  # You can adjust the time frame based on your strategy

# Step 4: Function to fetch historical data from Kite API
def fetch_historical_data(instrument_token):
    try:
        historical_data = kite.historical_data(instrument_token, from_date, to_date, interval)
        df = pd.DataFrame(historical_data)
        return df
    except Exception as e:
        logging.error(f"Error fetching historical data: {e}")
        return pd.DataFrame()

# Step 5: Check consolidation condition (within a narrow range)
def is_consolidating(df, percentage_range=20, period=10):
    # Calculate the highest high and lowest low in the period
    df['max_high'] = df['high'].rolling(window=period).max()
    df['min_low'] = df['low'].rolling(window=period).min()

    # Calculate the percentage range of the price
    df['range'] = (df['max_high'] - df['min_low']) / df['min_low'] * 100

    # If the range is within the given percentage, it is consolidating
    df['is_consolidating'] = df['range'] <= percentage_range

    return df

# Step 6: Check ATR (Average True Range) to measure volatility
def check_atr(df, period=14):
    df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=period)
    return df

# Step 7: Consolidation criteria
def check_market_consolidation(df):
    df = check_atr(df)  # Add ATR for volatility measurement
    df = is_consolidating(df)  # Check if it's within the consolidation range

    # Consolidation signal when true for last period
    latest_consolidation = df['is_consolidating'].iloc[-1]

    if latest_consolidation:
        logging.info("The market is in consolidation.")
    else:
        logging.info("The market is trending.")

    return latest_consolidation

# Example: Fetch and check consolidation for NIFTY
instrument_token = 	10357762  # NIFTY 50 token, replace with your instrument token
df = fetch_historical_data(instrument_token)

if not df.empty:
    consolidation_status = check_market_consolidation(df)

