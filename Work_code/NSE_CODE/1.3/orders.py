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
df = pd.DataFrame(instruments)

csv_file_path = 'options_tradingsymbols_ce.csv'  # Update this with the actual path to your file
options_csv_df = pd.read_csv(csv_file_path)

# Step 5: Filter contracts that match the trading symbols in the CSV file
matching_contracts_df = df[df['tradingsymbol'].isin(options_csv_df['tradingsymbol'])]

# Step 6: Extract the first matching instrument token and store it in a variable
if not matching_contracts_df.empty:
    instrument_token = matching_contracts_df.iloc[0]['instrument_token']
    tradingsymbol = matching_contracts_df.iloc[0]['tradingsymbol']
else:
    logging.error("No matching instruments found.")

################################################################################################

# Step 4 - Download historical data using kite's API session created in step 1
# Define the instrument token and the time period
from_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
to_date = datetime.now().strftime('%Y-%m-%d')
interval = "minute"  # Can be "minute", "5minute", "15minute", "day", etc.

try:
    # Fetch historical data
    historical_data = kite.historical_data(instrument_token, from_date, to_date, interval)
    niftydf = pd.DataFrame(historical_data)
except Exception as e:
    logging.error(f"Error fetching historical data: {e}")

######################################################################################################

# Step 5 - Add RSI, EMA, Supertrend, and DMI signals to historical data
# Example: Exponential Moving Average (EMA) signal using TA-Lib
def ema_signal(df, window=30):
    df['EMA'] = talib.EMA(df['close'], timeperiod=window)  # Using TA-Lib EMA
    df['EMA_Signal'] = np.where(df['close'] > df['EMA'], 'Buy', 'Sell')
    return df

# Example: RSI (Relative Strength Index) signal using TA-Lib
def rsi_signal(df, window=14):
    df['RSI'] = talib.RSI(df['close'], timeperiod=window)  # Using TA-Lib RSI
    df['RSI_Signal'] = np.where(df['RSI'] > 80, 'Sell', np.where(df['RSI'] < 15, 'Buy', 'Hold'))
    return df

# Example: Supertrend signal using TA-Lib ATR
def supertrend(df, period=7, multiplier=3):
    high = df['high']
    low = df['low']
    close = df['close']

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

# Example: DMI (Directional Movement Index) signal using TA-Lib
def dmi_signal(df, period=14):
    df['+DI'] = talib.PLUS_DI(df['high'], df['low'], df['close'], timeperiod=period)
    df['-DI'] = talib.MINUS_DI(df['high'], df['low'], df['close'], timeperiod=period)

    # Buy signal when +DI crosses above -DI
    # Sell signal when -DI crosses above +DI
    df['DMI_Signal'] = np.where(df['+DI'] > df['-DI'], 'Buy', 'Sell')
    return df

# Apply all signals to niftydf
try:
    niftydf = ema_signal(niftydf)  # Apply EMA
    niftydf = supertrend(niftydf)  # Apply Supertrend
    niftydf = rsi_signal(niftydf)  # Apply RSI
    niftydf = dmi_signal(niftydf)  # Apply DMI
except KeyError as e:
    logging.error(f"KeyError: {e}")
except Exception as e:  
    logging.error(f"An error occurred: {e}")

# Extract the signal columns
signals_df = niftydf[['EMA_Signal', 'RSI_Signal', 'Supertrend_Signal', 'DMI_Signal']]

# Convert the signals DataFrame to a dictionary (to be JSON serializable)
signals_dict = signals_df.tail(1).to_dict(orient='records')[0]  # Only store the last row of signals

# Add the tradingsymbol to the signals dictionary
signals_dict['tradingsymbol'] = tradingsymbol

# Save the signals to a JSON file
with open('signal.json', 'w') as json_file:
    json.dump(signals_dict, json_file, indent=4)

logging.info("Signals saved to kite_signal.json")