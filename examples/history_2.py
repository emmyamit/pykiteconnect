import logging
from kiteconnect import KiteConnect
from datetime import datetime, timedelta
import pandas as pd
import logging

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key="luu5ax574l5l4wy5")

# https://kite.zerodha.com/connect/login?api_key=luu5ax574l5l4wy5&v=3

data = kite.generate_session("qftzLcArzs83vopCxtUM4z7bdeDh6re0", api_secret="42f1n196xlkpmei6v5duzyhwn5vurgaa")
print(data["access_token"])
kite.set_access_token(data["access_token"])

# Initialise
#kws = KiteTicker("your_api_key", "your_access_token")

#######################################################################################################

# Define the instrument token and the time period
instrument_token = 256265  # Example: Token for NIFTY (NIFTY)
from_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
to_date = datetime.now().strftime('%Y-%m-%d')
interval = "5minute"  # Can be "minute", "5minute", "15minute", "day", etc.

# Fetch historical data
historical_data = kite.historical_data(instrument_token, from_date, to_date, interval)

# Convert data to DataFrame for easier handling (optional)
nifty50df = pd.DataFrame(historical_data)

print(nifty50df.head())  # Display the first few rows of the data

######################################################################################################


#####################################################################################################

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

#################################################################################################

#9908994
#256265

# Define the instrument token and the time period
instrument_token = 256265  # Example: Token for INFY (Infosys)
from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
to_date = datetime.now().strftime('%Y-%m-%d')
interval = "5minute"  # Can be "minute", "5minute", "15minute", "day", etc.

# Fetch historical data
historical_data = kite.historical_data(instrument_token, from_date, to_date, interval)

# Convert data to DataFrame for easier handling (optional)
filterdf = pd.DataFrame(historical_data)

print(filterdf.head())  # Display the first few rows of the data
