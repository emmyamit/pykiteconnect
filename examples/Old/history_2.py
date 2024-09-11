#Step 1 - import libararies and intial connection to kite platform

import logging
from kiteconnect import KiteConnect
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import talib

logging.basicConfig(level=logging.DEBUG)
kite = KiteConnect(api_key="luu5ax574l5l4wy5")

# https://kite.zerodha.com/connect/login?api_key=luu5ax574l5l4wy5&v=3
data = kite.generate_session("g1g2Z2Bx79Tgo5X0SEJ2CAh710trTv4t", api_secret="42f1n196xlkpmei6v5duzyhwn5vurgaa")
print(data["access_token"])
kite.set_access_token(data["access_token"])

#######################################################################################################

#Step 2 - Download hostorical data using kite's api session created in step 1

# Define the instrument token and the time period
instrument_token = 256265  # Example: Token for NIFTY (NIFTY)
from_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
to_date = datetime.now().strftime('%Y-%m-%d')
interval = "5minute"  # Can be "minute", "5minute", "15minute", "day", etc.

try:
    # Fetch historical data
    historical_data = kite.historical_data(instrument_token, from_date, to_date, interval)

    # Convert the data to a DataFrame for easier handling
    niftydf = pd.DataFrame(historical_data)
except Exception as e:
    logging.error(f"Error fetching historical data: {e}")

######################################################################################################

#Step 3 - add RSI, EMA and Supertrend indicator to Historical data
 
# Example: Exponential Moving Average (EMA) signal using TA-Lib
def ema_signal(df, window=25):
    df['EMA'] = talib.EMA(df['close'], timeperiod=window)  # Using TA-Lib EMA
    df['EMA_Signal'] = np.where(df['close'] > df['EMA'], 'Buy', 'Sell')
    return df

# Example: RSI (Relative Strength Index) signal using TA-Lib
def rsi_signal(df, window=14):
    df['RSI'] = talib.RSI(df['close'], timeperiod=window)  # Using TA-Lib RSI
    # RSI signal: Buy if RSI < 30, Sell if RSI > 70, Hold otherwise
    df['RSI_Signal'] = np.where(df['RSI'] > 80, 'Sell', np.where(df['RSI'] < 15, 'Buy', 'Hold'))
    return df

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

# Apply signals to niftydf
niftydf = ema_signal(niftydf)  # Use EMA with TA-Lib
niftydf = supertrend(niftydf)
niftydf = rsi_signal(niftydf)  # Use RSI with TA-Lib

