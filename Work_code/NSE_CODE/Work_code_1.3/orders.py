import logging
from kiteconnect import KiteConnect
import pandas as pd
import json
from datetime import datetime
import os

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

# Define the symbol for which we want to check and place an order (example: NIFTY)
csv_file_path = 'options_tradingsymbols_ce.csv'  # Update this with the actual path to your file
options_csv_df = pd.read_csv(csv_file_path)
symbol = options_csv_df.tradingsymbol.iloc[0]

# Quantity to buy or sell
quantity = 15
signal_file='signal.json'
order_file='order.json'  
price_file = "avg_price.json"  # File to store order data

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


# Function to place a buy order
def place_buy_order(symbol, quantity):
    order_id = kite.place_order(tradingsymbol=symbol,
                             variety=kite.VARIETY_REGULAR,
                             exchange=kite.EXCHANGE_NFO,
                             transaction_type=kite.TRANSACTION_TYPE_BUY,
                             quantity=quantity,
                             order_type=kite.ORDER_TYPE_MARKET,
                             product=kite.PRODUCT_NRML)
    return order_id


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

##################################################################################################################

# 1. Check if there is an existing order in order.json
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
    
    return supertrend_signal, close_price

#################################################################################################################

# Main function to handle the logic
def trading_loop():
    # while True:
        supertrend_signal, close_price = check_signal(signal_file)
        existing_order = check_existing_order(symbol, order_file)

        # Step 3: Check if Buy signal is generated
        if supertrend_signal == "Buy":
            print("Buy signal generated.")
            
            # Step 4: Place a buy order and store average price
            if not existing_order or existing_order['order_type'] == "Sell":
                place_new_order(symbol, order_type="Buy", quantity=quantity, order_file=order_file)
                order_id = place_buy_order(symbol, quantity)
                avg_price = get_average_price(order_id)

                if avg_price:
                    store_average_price(order_id, avg_price)
                    print(f"Buy order placed. Order ID: {order_id}, Average Price: {avg_price}")
            else:
                 print('Buy Order already exist')        

        # Step 5: Check if Sell condition is met (Close price > Average Price + 20)
        avg_price = read_average_price()
        if avg_price:
            print("Entering Sell block")
            if supertrend_signal == "Sell" or close_price >= (avg_price + 20):
                print("Sell condition met, exiting the position")
                place_new_order(symbol, order_type="Sell", quantity=quantity, order_file=order_file)
                clear_avg_price_file()
                # Step 6: Place sell order
                sell_order = kite.place_order(tradingsymbol=symbol,
                                              variety=kite.VARIETY_REGULAR,
                                              exchange=kite.EXCHANGE_NFO,
                                              transaction_type=kite.TRANSACTION_TYPE_SELL,
                                              quantity=quantity,
                                              order_type=kite.ORDER_TYPE_MARKET,
                                              product=kite.PRODUCT_NRML)
                print(f"Sell order placed: {sell_order}")
        
        # Step 7: Sleep before the next iteration (based on your interval)
        # time.sleep(60)  # 5-minute interval

##################################################################################################################

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

    logging.info(f"New {order_type} order placed: {new_order}")
    return new_order.get('order_id')  # Return the order ID to append to avg_price.json

def clear_avg_price_file(price_file='avg_price.json'):
    # Write an empty dictionary or list to clear the file
    with open(price_file, 'w') as f:
        json.dump({}, f, indent=4)  # Empty dictionary to clear the file
    logging.info(f"{price_file} has been cleared.")

        
# Corrected main function to run the trading loop
if __name__ == "__main__":
    trading_loop()
