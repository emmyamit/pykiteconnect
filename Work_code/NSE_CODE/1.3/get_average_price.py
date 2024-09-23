import logging
from kiteconnect import KiteConnect
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import talib
import json
import time


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

###############################################################################################################

# Define instrument and parameters
symbol = 'BANKNIFTY2492551800CE'
interval = '5minute'
lookback_period = 14  # Example lookback period for SuperTrend
json_file = "average.json"  # File to store order data


# Function to compute SuperTrend
def supertrend(df, period=7, multiplier=3):
    hl2 = (df['high'] + df['low']) / 2
    df['ATR'] = df['close'].rolling(window=period).std()  # Simplified ATR calculation
    df['UpperBand'] = hl2 + (multiplier * df['ATR'])
    df['LowerBand'] = hl2 - (multiplier * df['ATR'])
    
    df['SuperTrend'] = df['LowerBand']  # Default to LowerBand for simplicity
    df['Buy_Signal'] = df['close'] > df['SuperTrend']  # Buy if price is above SuperTrend
    df['Sell_Signal'] = df['close'] < df['SuperTrend']  # Sell if price is below SuperTrend
    return df


# Function to download historical data
def download_historical_data(symbol, interval, from_date, to_date):
    data = kite.historical_data(instrument_token=738561,  # Example instrument token for RELIANCE
                                from_date=from_date,
                                to_date=to_date,
                                interval=interval)
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['date'])
    return df


# Function to place a buy order
def place_buy_order(symbol, quantity):
    order = kite.place_order(tradingsymbol=symbol,
                             variety=kite.VARIETY_REGULAR,
                             exchange=kite.EXCHANGE_NFO,
                             transaction_type=kite.TRANSACTION_TYPE_BUY,
                             quantity=quantity,
                             order_type=kite.ORDER_TYPE_MARKET,
                             product=kite.PRODUCT_MIS)
    return order['order_id']


# Function to retrieve average price of completed order
def get_average_price(order_id):
    order_details = kite.order_history(order_id=order_id)
    for detail in order_details:
        if detail['status'] == 'COMPLETE':
            return detail['average_price']
    return None


# Function to store average price in JSON
def store_average_price(order_id, avg_price):
    data = {'order_id': order_id, 'average_price': avg_price}
    with open(json_file, 'w') as f:
        json.dump(data, f)


# Function to read average price from JSON
def read_average_price():
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
            return data['average_price']
    except (FileNotFoundError, KeyError):
        return None


# Main function to handle the logic
def trading_loop():
    # Set date range for historical data
    from_date = '2023-09-01'
    to_date = '2023-09-05'

    while True:
        # Step 1: Download historical data
        df = download_historical_data(symbol, interval, from_date, to_date)

        # Step 2: Calculate SuperTrend and check buy/sell signals
        df = supertrend(df)

        # Step 3: Check if Buy signal is generated
        if df.iloc[-1]['Buy_Signal']:
            print("Buy signal generated.")
            
            # Step 4: Place a buy order and store average price
            order_id = place_buy_order(symbol, quantity=1)
            avg_price = get_average_price(order_id)
            
            if avg_price:
                store_average_price(order_id, avg_price)
                print(f"Buy order placed. Order ID: {order_id}, Average Price: {avg_price}")

        # Step 5: Check if Sell condition is met (Close price > Average Price + 20)
        avg_price = read_average_price()
        if avg_price:
            if df.iloc[-1]['close'] > (avg_price + 20):
                print(f"Sell condition met: Close Price {df.iloc[-1]['close']} > {avg_price + 20}")
                
                # Step 6: Place sell order
                sell_order = kite.place_order(tradingsymbol=symbol,
                                              variety=kite.VARIETY_REGULAR,
                                              exchange=kite.EXCHANGE_NFO,
                                              transaction_type=kite.TRANSACTION_TYPE_SELL,
                                              quantity=1,
                                              order_type=kite.ORDER_TYPE_MARKET,
                                              product=kite.PRODUCT_MIS)
                print(f"Sell order placed: {sell_order}")
        
        # Step 7: Sleep before the next iteration (based on your interval)
        time.sleep(300)  # 5-minute interval


# Corrected main function to run the trading loop
if __name__ == "__main__":
    trading_loop()