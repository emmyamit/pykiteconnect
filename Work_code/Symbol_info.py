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
df = pd.DataFrame(instruments)

# Filter contracts for NIFTY 50 (includes futures and options)
nifty_contracts_df = df[df['tradingsymbol'].str.contains("NIFTY") & 
                    (df['segment'] == 'NFO-OPT') & 
                    (df['instrument_type'] == 'CE') & 
                    (df['name'] == 'NIFTY')]

# Display the first few rows of the DataFrame
print(nifty_contracts_df.head())