import logging
from kiteconnect import KiteConnect
import pandas as pd
import json
import os
from datetime import datetime

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

# Load KiteConnect API key, secret, and access token
with open('kite_key.json', 'r') as f:
    keys = json.load(f)

api_key = keys.get('api_key')
api_secret = keys.get('api_secret')

with open('kite_session.json', 'r') as f:
    session_data = json.load(f)

access_token = session_data.get("access_token")

# Initialize KiteConnect API
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

# Define trading symbol and other variables
csv_file_path = 'options_tradingsymbols_ce.csv'  
options_csv_df = pd.read_csv(csv_file_path)
symbol = options_csv_df.tradingsymbol.iloc[0]  # Example: NIFTY
quantity = 15

#Files
signal_file='signal.json'
order_file='order.json'  
price_file = "avg_price.json"

# 1. Check if there is an existing order in order_pe.json
def check_existing_order(symbol, order_file='order.json'):
    if os.path.exists(order_file):
        with open(order_file, 'r') as file:
            try:
                orders = json.load(file)
            except json.JSONDecodeError:
                orders = []  # If JSON is malformed or empty, treat it as no orders
    else:
        orders = []  # No file means no orders

    for order in orders:
        if order.get('symbol') == symbol:
            return order  # Return the existing order

    return None  # No existing order for the symbol

# 2. Check the signal in signal.json file
def check_signal(signal_file='signal.json'):
    if os.path.exists(signal_file):
        with open(signal_file, 'r') as file:
            try:
                signals = json.load(file)
            except json.JSONDecodeError:
                logging.error(f"Error reading {signal_file}. Invalid JSON format.")
                return None, None
    else:
        logging.error(f"{signal_file} not found!")
        return None, None

    # Retrieve the 'Supertrend_Signal' and 'close' values
    supertrend_signal = signals.get("Supertrend_Signal", "")
    close_price = signals.get("close", "")
    consolidation = signals.get("is_consolidating","")
    
    return supertrend_signal,close_price,consolidation 


# Function to place a buy order
def place_buy_order(symbol, quantity):
    order_id = kite.place_order(tradingsymbol=symbol,
                                variety=kite.VARIETY_REGULAR,
                                exchange=kite.EXCHANGE_NFO,
                                transaction_type=kite.TRANSACTION_TYPE_BUY,
                                quantity=quantity,
                                order_type=kite.ORDER_TYPE_MARKET,
                                product=kite.PRODUCT_NRML)
    print(f"Buy order placed: {order_id}")
    return order_id


# Function to place a sell order
def place_sell_order(symbol, quantity):
    order_id = kite.place_order(tradingsymbol=symbol,
                                variety=kite.VARIETY_REGULAR,
                                exchange=kite.EXCHANGE_NFO,
                                transaction_type=kite.TRANSACTION_TYPE_SELL,
                                quantity=quantity,
                                order_type=kite.ORDER_TYPE_MARKET,
                                product=kite.PRODUCT_NRML)
    print(f"Sell order placed: {order_id}")
    return order_id


# Function to place a new order and write it to order.json (clears old orders)
def place_new_order(symbol, order_type, quantity=quantity, order_file='order.json'):
    new_order = {
        "symbol": symbol,
        "order_type": order_type,
        "quantity": quantity,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    # Clear the old orders by overwriting the file with the new order only
    with open(order_file, 'w') as file:
        json.dump([new_order], file, indent=4)  # Write only the new order, overwriting the old one
    print(f"New {order_type} order placed: {new_order}")


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
    with open(price_file, 'w') as f:
        json.dump(data, f)


# Function to read average price from JSON
def read_average_price():
    try:
        with open(price_file, 'r') as f:
            data = json.load(f)
            return data['average_price']
    except (FileNotFoundError, KeyError):
        return None


# Function to monitor live market data and act accordingly
def monitor_market():       
        # Step 1: Check if the market is consolidating
        supertrend_signal, close_price, consolidation = check_signal(signal_file)
        existing_order = check_existing_order(symbol, order_file)

        if consolidation == "True":
            print("Market is consolidating. No trades will be placed.")
        elif consolidation == "False":
            
            print(f"Supertrend Signal: {supertrend_signal}")
            
            if supertrend_signal == "Buy":
                if not existing_order or existing_order['order_type'] == "Sell":
                    print("Buy Order placed")
                    place_new_order(symbol, order_type="Buy", quantity=quantity, order_file=order_file)
                    order_id = place_buy_order(symbol, quantity)
                    avg_price = get_average_price(order_id)
                    if avg_price:
                        store_average_price(order_id, avg_price)
                        print(f"Buy order placed. Order ID: {order_id}, Average Price: {avg_price}")

                elif existing_order:
                    print("Buy order exist,check current price and average price to close Buy order.")
                    avg_price = read_average_price()
                    if avg_price:
                        if close_price >= (avg_price + 40):
                            place_sell_order(symbol, quantity)
            

            elif supertrend_signal == "Sell":
                if not existing_order or existing_order['order_type'] == "Buy":
                    print("Sell Order placed")
                    place_new_order(symbol, order_type="Sell", quantity=quantity, order_file=order_file)
                    place_sell_order(symbol, quantity)
                else:
                    print("Sell order already placed, waiting for new buy order.")
                
# Main function to start the market monitoring
if __name__ == "__main__":
    print("Starting market monitoring for consolidation and Supertrend signal.")
    monitor_market()