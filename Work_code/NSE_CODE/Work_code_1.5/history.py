# use_session.py
import logging
from kiteconnect import KiteConnect
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import talib
import json

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

################################################################################################

# Fetch all instruments for NSE
instruments = kite.instruments("NFO")

# Convert to DataFrame for easier filtering
nse = pd.DataFrame(instruments)

csv_file_path = 'options_tradingsymbols_ce.csv'  # Update this with the actual path to your file
options_csv_df = pd.read_csv(csv_file_path)

# Step 5: Filter contracts that match the trading symbols in the CSV file
matching_contracts_df = nse[nse['tradingsymbol'].isin(options_csv_df['tradingsymbol'])]

# Step 6: Extract the first matching instrument token and store it in a variable
if not matching_contracts_df.empty:
    instrument_token = matching_contracts_df.iloc[0]['instrument_token']
    tradingsymbol = matching_contracts_df.iloc[0]['tradingsymbol']
    #logging.info(f"Instrument token for {tradingsymbol} is {instrument_token}")
else:
    logging.error("No matching instruments found.")

################################################################################################

#Step 4 - Download hostorical data using kite's api session created in step 1
# Define the instrument token and the time period
from_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
to_date = datetime.now().strftime('%Y-%m-%d')
interval = "minute"  # Can be "minute", "5minute", "15minute", "day", etc.

try:
    # Fetch historical data
    historical_data = kite.historical_data(instrument_token, from_date, to_date, interval)

    # Convert the data to a DataFrame for easier handling
    nifty = pd.DataFrame(historical_data)
except Exception as e:
    logging.error(f"Error fetching historical data: {e}")


######################################################################################################

# Step 5: Check consolidation condition (within a narrow range)
def is_consolidating(nifty, percentage_range=20, period=10):
    # Calculate the highest high and lowest low in the period
    nifty['max_high'] = nifty['high'].rolling(window=period).max()
    nifty['min_low'] = nifty['low'].rolling(window=period).min()

    # Calculate the percentage range of the price
    nifty['range'] = (nifty['max_high'] - nifty['min_low']) / nifty['min_low'] * 100
    # If the range is within the given percentage, it is consolidating
    nifty['is_consolidating'] = nifty['range'] <= percentage_range
    return nifty

# Step 6: Check ATR (Average True Range) to measure volatility
def check_atr(nifty, period=14):
    nifty['ATR'] = talib.ATR(nifty['high'], nifty['low'], nifty['close'], timeperiod=period)
    return nifty


# Step 7: Consolidation criteria
def check_market_consolidation(nifty):
    nifty = check_atr(nifty)  # Add ATR for volatility measurement
    nifty = is_consolidating(nifty)  # Check if it's within the consolidation range

    # Consolidation signal when true for last period
    latest_consolidation = nifty['is_consolidating'].iloc[-1]
    return latest_consolidation

if not nifty.empty:
    consolidation_status = check_market_consolidation(nifty)

########################################################################################################################

#Step 5 - add RSI, EMA and Supertrend indicator to Historical data
# Example: Exponential Moving Average (EMA) signal using TA-Lib
# def ema_signal(df, window=30):
#     df['EMA'] = talib.EMA(df['close'], timeperiod=window)  # Using TA-Lib EMA
#     df['EMA_Signal'] = np.where(df['close'] > df['EMA'], 'Buy', 'Sell')
#     return df

# # Example: RSI (Relative Strength Index) signal using TA-Lib
# def rsi_signal(df, window=14):
#     df['RSI'] = talib.RSI(df['close'], timeperiod=window)  # Using TA-Lib RSI
#     # RSI signal: Buy if RSI < 30, Sell if RSI > 70, Hold otherwise
#     df['RSI_Signal'] = np.where(df['RSI'] > 75, 'Sell', np.where((df['RSI'] >= 55) & (df['RSI'] <= 60), 'Buy', 'Hold'))
#     return df

# Example: Supertrend signal using TA-Lib ATR
def supertrend(df, period=7, multiplier=3):
    high = df['high']
    low = df['low']
    close = df['close']

    # Use TA-Lib's ATR (Average True Range) function
    atr = talib.ATR(high, low, close, timeperiod=period)

    upper_band = ((high + low) / 2) + (multiplier * atr)
    lower_band = ((high + low) / 2) - (multiplier * atr)

    supertrend = [True] * len(df)

    for i in range(1, len(df.index)):
        if close[i] > upper_band[i-1]:
            supertrend[i] = True
        elif close[i] < lower_band[i-1]:
            supertrend[i] = False
        else:
            supertrend[i] = supertrend[i-1]

        if supertrend[i]:
            lower_band[i] = max(lower_band[i], lower_band[i-1])
        else:
            upper_band[i] = min(upper_band[i], upper_band[i-1])

    df['Supertrend'] = supertrend
    df['Supertrend_Signal'] = np.where(df['Supertrend'], 'Buy', 'Sell')
    return df

# Apply signals to nifty
try:
    # nifty = ema_signal(nifty)  # Use EMA with TA-Lib
    nifty = supertrend(nifty)
    # nifty = rsi_signal(nifty)  # Use RSI with TA-Lib
except KeyError as e:
    logging.error(f"KeyError: {e}")
except Exception as e:  
    logging.error(f"An error occurred: {e}")

# Extract the signal columns
nifty['is_consolidating'] = nifty['is_consolidating'].astype(str)
# signals_df = nifty[['EMA_Signal', 'RSI_Signal', 'Supertrend_Signal','close','is_consolidating']]
signals_df = nifty[['Supertrend_Signal','close','is_consolidating']]

# Convert the signals DataFrame to a dictionary (to be JSON serializable)
signals_dict = signals_df.tail(1).to_dict(orient='records')[0]  # Only store the last row of signals

# Add the tradingsymbol to the signals dictionary
signals_dict['tradingsymbol'] = tradingsymbol

# Save the signals to a JSON file
with open('signal.json', 'w') as json_file:
    json.dump(signals_dict, json_file, indent=4)